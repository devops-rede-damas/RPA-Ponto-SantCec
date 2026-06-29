"""
Task: Baixar AFD.txt do SFTP de Santa Cecília.

Conecta ao servidor SFTP, baixa o arquivo AFD.txt e salva
localmente como AFD_STACECILIA.txt.
"""

import logging
import os
import socket

import paramiko

from config.settings import (
    SANTA_CECILIA_HOST,
    SANTA_CECILIA_PORT,
    SANTA_CECILIA_USER,
    SANTA_CECILIA_PASS,
    LOCAL_DIR,
    LOCAL_FILENAME,
    REMOTE_FILENAME,
    SFTP_TIMEOUT,
)
from utils.decorators import retry
from utils.exceptions import SFTPConnectionError, SFTPTransferError

logger = logging.getLogger(__name__)


@retry(
    max_attempts=3,
    delay=2.0,
    backoff=2.0,
    exceptions=(SFTPConnectionError, SFTPTransferError, OSError, socket.timeout),
)
def executar() -> str:
    """
    Baixa AFD.txt do SFTP Santa Cecília e salva como AFD_STACECILIA.txt.

    Returns:
        Caminho completo do arquivo local salvo.

    Raises:
        SFTPConnectionError: Se não conseguir conectar/autenticar.
        SFTPTransferError: Se o download falhar ou arquivo não existir.
    """
    local_path = os.path.join(LOCAL_DIR, LOCAL_FILENAME)

    # Garante que diretório local existe
    os.makedirs(LOCAL_DIR, exist_ok=True)

    logger.info(
        "Conectando ao SFTP Santa Cecília %s:%d (timeout=%ds)",
        SANTA_CECILIA_HOST, SANTA_CECILIA_PORT, SFTP_TIMEOUT,
    )

    transport = None
    sftp = None

    try:
        # Cria socket com timeout explícito (anti-trava)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SFTP_TIMEOUT)

        try:
            sock.connect((SANTA_CECILIA_HOST, SANTA_CECILIA_PORT))
        except socket.timeout:
            raise SFTPConnectionError(
                f"Timeout de {SFTP_TIMEOUT}s ao conectar em {SANTA_CECILIA_HOST}:{SANTA_CECILIA_PORT}"
            )
        except socket.gaierror:
            raise SFTPConnectionError(
                f"Não foi possível resolver hostname: {SANTA_CECILIA_HOST}"
            )
        except ConnectionRefusedError:
            raise SFTPConnectionError(
                f"Conexão recusada em {SANTA_CECILIA_HOST}:{SANTA_CECILIA_PORT} — verificar firewall/porta"
            )
        except OSError as exc:
            raise SFTPConnectionError(
                f"Erro de rede ao conectar em {SANTA_CECILIA_HOST}:{SANTA_CECILIA_PORT}: {exc}"
            )

        # Cria transport SSH com timeouts
        transport = paramiko.Transport(sock)
        transport.banner_timeout = SFTP_TIMEOUT
        transport.auth_timeout = SFTP_TIMEOUT

        try:
            transport.connect(username=SANTA_CECILIA_USER, password=SANTA_CECILIA_PASS)
        except paramiko.AuthenticationException:
            raise SFTPConnectionError(
                f"Autenticação falhou para {SANTA_CECILIA_USER}@{SANTA_CECILIA_HOST} — verificar credenciais"
            )
        except paramiko.SSHException as exc:
            raise SFTPConnectionError(
                f"Erro SSH ao conectar em {SANTA_CECILIA_HOST}: {exc}"
            )

        logger.info("Autenticado com sucesso. Iniciando download de '%s'", REMOTE_FILENAME)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get_channel().settimeout(SFTP_TIMEOUT)

        # Verifica se arquivo existe no remoto
        try:
            remote_stat = sftp.stat(REMOTE_FILENAME)
            logger.info("Arquivo remoto encontrado: %s (%d bytes)", REMOTE_FILENAME, remote_stat.st_size)
        except FileNotFoundError:
            raise SFTPTransferError(
                f"Arquivo '{REMOTE_FILENAME}' não encontrado no servidor {SANTA_CECILIA_HOST}"
            )
        except IOError as exc:
            raise SFTPTransferError(
                f"Erro ao verificar arquivo remoto '{REMOTE_FILENAME}': {exc}"
            )

        # Download
        try:
            sftp.get(REMOTE_FILENAME, local_path)
        except IOError as exc:
            raise SFTPTransferError(
                f"Erro durante download de '{REMOTE_FILENAME}': {exc}"
            )
        except socket.timeout:
            raise SFTPTransferError(
                f"Timeout durante download de '{REMOTE_FILENAME}' — conexão pode estar instável"
            )

        # Verifica tamanho local
        local_size = os.path.getsize(local_path)
        logger.info("Download concluído: %s (%d bytes)", local_path, local_size)

        return local_path

    finally:
        if sftp:
            try:
                sftp.close()
            except Exception:
                pass
        if transport:
            try:
                transport.close()
            except Exception:
                pass
