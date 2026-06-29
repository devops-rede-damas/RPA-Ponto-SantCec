"""
Carregamento e validação das configurações via .env
"""

import os
import sys
import logging

from dotenv import load_dotenv

from utils.exceptions import ConfigError

logger = logging.getLogger(__name__)

# Carrega .env do diretório raiz do projeto
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_BASE_DIR, ".env"))


def _require_env(name: str) -> str:
    """Retorna valor da variável ou levanta ConfigError."""
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"Variável de ambiente obrigatória ausente: {name}")
    return value


# --- SFTP Santa Cecília (origem) ---
SANTA_CECILIA_HOST = _require_env("SANTA_CECILIA_HOST")
SANTA_CECILIA_PORT = int(_require_env("SANTA_CECILIA_PORT"))
SANTA_CECILIA_USER = _require_env("SANTA_CECILIA_USER")
SANTA_CECILIA_PASS = _require_env("SANTA_CECILIA_PASS")

# --- SFTP Totvs RM TCloud (destino) ---
TOTVS_HOST = _require_env("TOTVS_HOST")
TOTVS_PORT = int(_require_env("TOTVS_PORT"))
TOTVS_USER = _require_env("TOTVS_USER")
TOTVS_PASS = _require_env("TOTVS_PASS")
TOTVS_REMOTE_DIR = os.getenv("TOTVS_REMOTE_DIR", "/Ponto")

# --- Paths locais ---
LOCAL_DIR = os.getenv("LOCAL_DIR", r"D:\PONTO\Coleta Batidas\Todos os REPs")
LOCAL_FILENAME = "AFD_STACECILIA.txt"
REMOTE_FILENAME = "AFD.txt"

# --- Timeouts ---
SCRIPT_TIMEOUT = int(os.getenv("SCRIPT_TIMEOUT", "300"))
SFTP_TIMEOUT = int(os.getenv("SFTP_TIMEOUT", "30"))
