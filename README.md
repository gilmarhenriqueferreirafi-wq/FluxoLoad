# FluxoLoad

> **Status: projeto incompleto / beta 1.1**
>
> O aplicativo já possui uma versão funcional para testes, mas ainda não é uma versão final. O principal ponto pendente é a distribuição do executável: ele não possui assinatura digital pública e pode ser bloqueado pelo Smart App Control do Windows. Além disso, YouTube, Instagram e TikTok podem alterar seus mecanismos de acesso e exigir novas adaptações.

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

Para downloads do YouTube, o FluxoLoad usa o provedor local de PO Token quando ele está instalado. O provedor fica preso em `127.0.0.1` e é iniciado automaticamente pelo aplicativo.

Antes de baixar, o aplicativo sincroniza a sessão do navegador QtWebEngine. A barra de status informa apenas a quantidade de cookies sincronizados e se o provedor local está ativo; os valores dos cookies não são exibidos. PO Token não garante a remoção de bloqueios por conta, IP ou desafio antirobô. Se aparecer "Nenhum cookie da sessão interna", faça login no navegador interno, aguarde a página terminar de carregar e tente novamente.

Falhas inesperadas do processo ficam registradas em `%LOCALAPPDATA%\FluxoLoad\runtime-crash.log` para diagnóstico.

```powershell
git clone --depth 1 --branch 2.0.2 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git "$env:USERPROFILE\bgutil-ytdlp-pot-provider"
cd "$env:USERPROFILE\bgutil-ytdlp-pot-provider\server"
npm install --include=dev
node node_modules/typescript/bin/tsc
```

## Executar em desenvolvimento

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

Também é possível executar `executar_fluxoload_fonte.cmd`. Esse lançador procura o Python instalado e, se necessário, tenta instalar o Python pelo WinGet, cria o ambiente `.venv`, instala as dependências com pip e inicia o `run.py`.

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
executar_fluxoload_fonte.cmd  Preparacao automatica do ambiente de codigo-fonte
```

O código-fonte é mantido no repositório. O executável e o instalador ficam separados como arquivos da release para não misturar artefatos binários com o código.

## Licença

Este projeto está disponível sob a licença [MIT](LICENSE).

## Aviso do Windows SmartScreen

A beta ainda não possui assinatura digital pública. Consulte [AVISO-SMARTSCREEN.txt](AVISO-SMARTSCREEN.txt) antes de executar o programa e baixe-o somente pela release oficial.
