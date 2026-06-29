"""
Task: Enviar AFD_STACECILIA.txt para o SFTP da Totvs RM TCloud.

Conecta ao servidor SFTP da Totvs e faz upload do arquivo
para a pasta /Ponto/.
"""

import logging
import os
import socket

import paramiko

from config.settings import (
    TOTVS_HOST,
    TOTVS_PORT,
    TOTVS_USER,
    TOTVS_PASS,
    TOTVS_REMOTE_DIR,
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
def executar(local_path: str, remote_filename: str) -> None:
    """
    Envia arquivo para o SFTP da Totvs RM TCloud.

    Args:
        local_path: Caminho completo do arquivo local.
        remote_filename: Nome do arquivo no destino (ex: AFD_STACECILIA.txt).

    Raises:
        SFTPConnectionError: Se não conseguir conectar/autenticar.
        SFTPTransferError: Se o upload falhar.
    """
    remote_path = f"{TOTVS_REMOTE_DIR}/{remote_filename}"

    logger.info(
        "Conectando ao SFTP Totvs %s:%d (timeout=%ds)",
        TOTVS_HOST, TOTVS_PORT, SFTP_TIMEOUT,
    )

    transport = None
    sftp = None

    try:
        # Cria socket com timeout explícito (anti-trava)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SFTP_TIMEOUT)

        try:
            sock.connect((TOTVS_HOST, TOTVS_PORT))
        except socket.timeout:
            raise SFTPConnectionError(
                f"Timeout de {SFTP_TIMEOUT}s ao conectar em {TOTVS_HOST}:{TOTVS_PORT}"
            )
        except socket.gaierror:
            raise SFTPConnectionError(
                f"Não foi possível resolver hostname: {TOTVS_HOST}"
            )
        except ConnectionRefusedError:
            raise SFTPConnectionError(
                f"Conexão recusada em {TOTVS_HOST}:{TOTVS_PORT} — verificar firewall/porta"
            )
        except OSError as exc:
            raise SFTPConnectionError(
                f"Erro de rede ao conectar em {TOTVS_HOST}:{TOTVS_PORT}: {exc}"
            )

        # Cria transport SSH com timeouts
        transport = paramiko.Transport(sock)
        transport.banner_timeout = SFTP_TIMEOUT
        transport.auth_timeout = SFTP_TIMEOUT

        try:
            transport.connect(username=TOTVS_USER, password=TOTVS_PASS)
        except paramiko.AuthenticationException:
            raise SFTPConnectionError(
                f"Autenticação falhou para {TOTVS_USER}@{TOTVS_HOST} — verificar credenciais"
            )
        except paramiko.SSHException as exc:
            raise SFTPConnectionError(
                f"Erro SSH ao conectar em {TOTVS_HOST}: {exc}"
            )

        logger.info("Autenticado com sucesso. Iniciando upload para '%s'", remote_path)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get_channel().settimeout(SFTP_TIMEOUT)

        # Upload
        local_size = os.path.getsize(local_path)

        try:
            sftp.put(local_path, remote_path)
        except FileNotFoundError:
            raise SFTPTransferError(
                f"Diretório remoto '{TOTVS_REMOTE_DIR}' não encontrado no servidor Totvs"
            )
        except IOError as exc:
            raise SFTPTransferError(
                f"Erro durante upload para '{remote_path}': {exc}"
            )
        except socket.timeout:
            raise SFTPTransferError(
                f"Timeout durante upload para '{remote_path}' — conexão pode estar instável"
            )

        # Verifica tamanho remoto
        try:
            remote_stat = sftp.stat(remote_path)
            if remote_stat.st_size != local_size:
                raise SFTPTransferError(
                    f"Tamanho divergente após upload: local={local_size} bytes, "
                    f"remoto={remote_stat.st_size} bytes"
                )
        except IOError:
            logger.warning("Não foi possível verificar tamanho do arquivo remoto após upload")

        logger.info(
            "Upload concluído: %s -> %s (%d bytes)",
            local_path, remote_path, local_size,
        )

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
