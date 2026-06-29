# RPA-Ponto-SantCec

RPA para coleta e envio automático do arquivo de ponto (AFD) do Colégio Santa Cecília.

## Fluxo

1. Conecta via SFTP no servidor do Santa Cecília e baixa o arquivo `AFD.txt`
2. Salva localmente como `AFD_STACECILIA.txt`
3. Envia `AFD_STACECILIA.txt` para o SFTP da Totvs RM TCloud na pasta `/Ponto/`

## Requisitos

- Python 3.10+
- Acesso de rede aos servidores SFTP (Santa Cecília e Totvs)

## Instalação

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Configuração

Copie `.env.example` para `.env` e preencha as credenciais:

```bash
copy .env.example .env
```

### Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `SANTA_CECILIA_HOST` | IP do servidor SFTP Santa Cecília |
| `SANTA_CECILIA_PORT` | Porta SFTP Santa Cecília |
| `SANTA_CECILIA_USER` | Usuário SFTP Santa Cecília |
| `SANTA_CECILIA_PASS` | Senha SFTP Santa Cecília |
| `TOTVS_HOST` | Host do SFTP Totvs RM TCloud |
| `TOTVS_PORT` | Porta SFTP Totvs |
| `TOTVS_USER` | Usuário SFTP Totvs |
| `TOTVS_PASS` | Senha SFTP Totvs |
| `TOTVS_REMOTE_DIR` | Diretório remoto no Totvs (padrão: `/Ponto`) |
| `LOCAL_DIR` | Diretório local para salvar o AFD temporariamente |
| `SCRIPT_TIMEOUT` | Timeout global em segundos (padrão: 300) |
| `SFTP_TIMEOUT` | Timeout de conexão SFTP em segundos (padrão: 30) |

## Execução

```bash
python main.py
```

Ou via batch (para Windows Task Scheduler):

```bash
executar.bat
```

## Agendamento (Windows Task Scheduler)

1. Abrir **Agendador de Tarefas**
2. Criar tarefa → Ação: `Iniciar um programa`
3. Programa: caminho completo para `executar.bat`
4. Iniciar em: diretório do projeto
5. Configurar frequência desejada (ex: a cada 1 hora)

## Exit Codes

| Código | Significado |
|--------|-------------|
| 0 | Sucesso |
| 1 | Erro de configuração (.env) |
| 2 | Erro de conexão SFTP Santa Cecília |
| 3 | Erro de download / arquivo não encontrado |
| 4 | Arquivo vazio (upload abortado) |
| 5 | Erro de conexão SFTP Totvs |
| 6 | Erro de upload |
| 99 | Timeout global excedido (5 min) |

## Logs

Logs são gravados em `logs/execucao.log` (rotação automática a cada 5MB, mantém 3 backups) e exibidos no stdout.

## Estrutura

```
RPA-Ponto-SantCec/
├── config/
│   └── settings.py          # Configurações via .env
├── tasks/
│   ├── baixar_afd.py        # Download SFTP Santa Cecília
│   └── enviar_sftp.py       # Upload SFTP Totvs TCloud
├── utils/
│   ├── logging_config.py    # Logging (stdout + arquivo)
│   ├── decorators.py        # @retry com backoff exponencial
│   └── exceptions.py        # Exceções customizadas
├── main.py                   # Orquestrador principal
├── executar.bat              # Launcher para Task Scheduler
├── requirements.txt
├── .env.example
└── .gitignore
```
