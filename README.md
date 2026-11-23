# FluxoLoad

Gerenciador local de downloads de mídia para Windows, com navegador integrado, painel de progresso e preferências persistentes.

## Recursos

- Navegação integrada para YouTube, Instagram e TikTok.
- Download autorizado de vídeos e áudios usando `yt-dlp`.
- Opções de qualidade, idioma, legendas e formato.
- Painel lateral de downloads com progresso e arquivos concluídos.
- Tema claro/escuro, cor de destaque e diretório configurável.
- Perfil local do navegador para manter a sessão no computador.

Use o aplicativo somente para conteúdo que você tem autorização para baixar e de acordo com os termos da plataforma.

## Requisitos

- Windows 10/11 64-bit.
- Python 3.12 ou superior para executar a partir do código-fonte.
- FFmpeg é recomendado para combinar vídeo e áudio e gerar MP3.

## Executar em desenvolvimento

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

Os arquivos baixados ficam em `Downloads\FluxoLoad` por padrão.

## Gerar o executável

```powershell
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --clean FluxoLoad.spec
```

O executável será criado em `dist\FluxoLoad`. As pastas `build` e `dist` são artefatos locais e não entram no Git.

## Estrutura

```text
assets/                  Ícones das plataformas
fluxoload/               Código do aplicativo
DIARIO.md                Histórico de decisões e validações
FluxoLoad.spec           Configuração do PyInstaller
requirements.txt         Dependências de execução
requirements-build.txt   Dependências de empacotamento
run.py                   Ponto de entrada
```

## Licença

Este projeto está disponível sob a licença [MIT](LICENSE).
