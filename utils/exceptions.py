"""
Exceções customizadas do RPA-Ponto-SantCec.

Hierarquia:
    RPAError
    ├── ConfigError
    ├── SFTPConnectionError
    └── SFTPTransferError
"""


class RPAError(Exception):
    """Exceção base para todos os erros do RPA."""
    pass


class ConfigError(RPAError):
    """Variável de ambiente ausente ou inválida."""
    pass


class SFTPConnectionError(RPAError):
    """Falha ao conectar ou autenticar no servidor SFTP."""
    pass


class SFTPTransferError(RPAError):
    """Falha durante download ou upload de arquivo via SFTP."""
    pass
