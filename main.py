"""
RPA-Ponto-SantCec — Entry Point

Fluxo:
    1. Download AFD.txt do SFTP Santa Cecília
    2. Validação do arquivo (não vazio)
    3. Upload AFD_STACECILIA.txt para SFTP Totvs TCloud /Ponto/

Exit Codes:
    0  = Sucesso
    1  = Erro de configuração (.env inválido)
    2  = Erro de conexão SFTP Santa Cecília
    3  = Erro de download / arquivo não encontrado
    4  = Arquivo vazio / inválido
    5  = Erro de conexão SFTP Totvs
    6  = Erro de upload
    99 = Timeout global excedido
"""

import logging
import os
import socket
import sys
import threading
import time

logger = logging.getLogger(__name__)


def _force_exit():
    """Encerra o script forçadamente após timeout global."""
    logger.critical(
        "ERRO: Timeout global excedido — encerrando forçadamente. "
        "O script ultrapassou o tempo máximo de execução."
    )
    os._exit(99)


def main():
    start_time = time.time()

    # --- Timeout global (anti-trava) ---
    # Importa settings aqui para capturar ConfigError antes de tudo
    try:
        from config.settings import SCRIPT_TIMEOUT, SFTP_TIMEOUT, LOCAL_FILENAME
    except Exception as exc:
        # Logging pode não estar configurado ainda, print direto
        print(f"ERRO FATAL: Falha ao carregar configuração: {exc}")
        sys.exit(1)

    # Configura logging
    from utils.logging_config import setup_logging
    setup_logging()

    # Socket timeout padrão global (fallback para qualquer operação de rede)
    socket.setdefaulttimeout(SFTP_TIMEOUT)

    # Timer de segurança: encerra processo se ultrapassar SCRIPT_TIMEOUT
    watchdog = threading.Timer(SCRIPT_TIMEOUT, _force_exit)
    watchdog.daemon = True
    watchdog.start()

    logger.info("=" * 60)
    logger.info("RPA-Ponto-SantCec — Início da execução")
    logger.info("=" * 60)

    try:
        # ============================================================
        # FASE 1: Download do AFD.txt do SFTP Santa Cecília
        # ============================================================
        logger.info("[FASE 1] Download do AFD.txt do SFTP Santa Cecília")

        from tasks import baixar_afd
        from utils.exceptions import (
            ConfigError,
            SFTPConnectionError,
            SFTPTransferError,
        )

        try:
            local_path = baixar_afd.executar()
        except ConfigError as exc:
            logger.critical("ERRO DE CONFIGURAÇÃO: %s", exc)
            sys.exit(1)
        except SFTPConnectionError as exc:
            logger.critical("ERRO DE CONEXÃO (Santa Cecília): %s", exc)
            sys.exit(2)
        except SFTPTransferError as exc:
            logger.critical("ERRO DE DOWNLOAD: %s", exc)
            sys.exit(3)

        # ============================================================
        # FASE 2: Validação do arquivo baixado
        # ============================================================
        logger.info("[FASE 2] Validando arquivo baixado")

        if not os.path.exists(local_path):
            logger.critical("ERRO: Arquivo não encontrado após download: %s", local_path)
            sys.exit(3)

        file_size = os.path.getsize(local_path)
        if file_size == 0:
            logger.critical(
                "ERRO: Arquivo baixado está vazio (0 bytes): %s — "
                "REP pode não ter batidas registradas. Upload abortado.",
                local_path,
            )
            sys.exit(4)

        logger.info("Arquivo válido: %s (%d bytes)", local_path, file_size)

        # ============================================================
        # FASE 3: Upload para SFTP Totvs TCloud
        # ============================================================
        logger.info("[FASE 3] Upload do %s para SFTP Totvs TCloud", LOCAL_FILENAME)

        from tasks import enviar_sftp

        try:
            enviar_sftp.executar(local_path, LOCAL_FILENAME)
        except SFTPConnectionError as exc:
            logger.critical("ERRO DE CONEXÃO (Totvs): %s", exc)
            sys.exit(5)
        except SFTPTransferError as exc:
            logger.critical("ERRO DE UPLOAD: %s", exc)
            sys.exit(6)

        # ============================================================
        # CONCLUSÃO
        # ============================================================
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info("RPA-Ponto-SantCec — Execução concluída com SUCESSO em %.1fs", elapsed)
        logger.info("=" * 60)
        sys.exit(0)

    except Exception as exc:
        logger.critical("ERRO NÃO ESPERADO: %s", exc, exc_info=True)
        sys.exit(3)

    finally:
        watchdog.cancel()


if __name__ == "__main__":
    main()
