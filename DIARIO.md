# Diário do FluxoLoad

### Bug visual da interface identificado

- Botao de configuracoes agora funciona como alternancia: ao abrir, guarda a tela atual; ao clicar novamente, retorna para a ultima tela (Home ou navegador).
- A barra de progresso inferior e o texto de status agora ficam ocultos enquanto o painel de Downloads estÃ¡ aberto; o progresso continua visÃ­vel no card do download.
- Nova preferÃªncia nas ConfiguraÃ§Ãµes: "Abrir o painel de Downloads ao iniciar um download". Ela vem ativada por padrÃ£o e pode ser desativada para manter o painel fechado ao iniciar downloads.
- Painel de Downloads agora nÃ£o pode ser desencaixado/flutuado; o botÃ£o de desencaixe foi removido. O erro HTTP 403 do YouTube foi separado dos avisos JavaScript do navegador e permanece pendente de reproduÃ§Ã£o com a URL especÃ­fica.
- Erros de download agora mostram as aÃ§Ãµes "Tentar novamente" e "Sair"; a tentativa repete a Ãºltima URL e as opÃ§Ãµes selecionadas.
- Erro reproduzido: o YouTube exibiu "Sign in to confirm you\u2019re not a bot" porque o fluxo de download nÃ£o chamava a exportaÃ§Ã£o de cookies, embora a funÃ§Ã£o existisse. CorreÃ§Ã£o local aplicada para sincronizar os cookies antes do download e tambÃ©m antes de uma nova tentativa.
- IntegraÃ§Ã£o interna reforÃ§ada: o download agora recebe os cookies em cache e o mesmo User-Agent do navegador QtWebEngine, sem depender de Brave/Chrome externo.
- Backup completo criado em `C:\\Users\\gilma\\Projects\\baixarcoisas_backup_2026-11-23_1930` antes da nova correÃ§Ã£o.
- ExportaÃ§Ã£o Netscape corrigida para manter cookies de sessÃ£o sem vencimento e marcar cookies `HttpOnly` corretamente.
- Painel de Downloads recebeu rolagem vertical prÃ³pria; a barra de progresso inferior agora some ao concluir e reaparece quando um novo download comeÃ§a.
- Busca de assets reforÃ§ada para `run.py` e pacotes; divisor do painel lateral agora fica arrastÃ¡vel entre 260 e 600 px, com alÃ§a visual no separador.
- Goal PO Token iniciado apÃ³s backup completo. Plugin `bgutil-ytdlp-pot-provider` instalado, provedor Node compilado em `%USERPROFILE%\\bgutil-ytdlp-pot-provider` e inicializaÃ§Ã£o local integrada ao downloader com cliente YouTube `mweb`.
- DiagnÃ³stico de download adicionado: a barra de status informa somente a quantidade de cookies sincronizados da sessÃ£o QtWebEngine e se o provedor local de PO Token estÃ¡ ativo; nenhum valor de cookie Ã© exibido. O Ãºltimo teste ainda reproduziu o bloqueio, antes da validaÃ§Ã£o com o novo diagnÃ³stico.
- ParÃ¢metro `base_url` corrigido para o formato esperado pelo plugin; consulta de metadados pÃºblica confirmou `Generating a gvs PO Token for mweb client via bgutil HTTP server`. Falta validar um download com a sessÃ£o autenticada do QtWebEngine.
- Clientes YouTube `tv` e `web_safari` adicionados como fallback; nova consulta pÃºblica confirmou geraÃ§Ã£o de PO Token para `mweb` e `web_safari` pelo servidor HTTP local.
- ValidaÃ§Ã£o pelo `run.py` concluÃ­da com sucesso: o usuÃ¡rio confirmou um download autorizado funcionando com a integraÃ§Ã£o interna de PO Token e a sessÃ£o persistente do QtWebEngine.
- Crash reproduzido no Windows durante download: o WER registrou `APPCRASH` de `python.exe`/`python314.dll` com `0xc0000005`, sem exceÃ§Ã£o Python visÃ­vel. O worker foi migrado de `threading.Thread` para `QThread` do Qt, exceÃ§Ãµes inesperadas passaram a ser exibidas e `run.py` agora grava `runtime-crash.log`.
- Novo crash diagnosticado pelo `runtime-crash.log`: dois `QThread` estavam executando `yt-dlp` simultaneamente em `ssl.py`, enquanto a referÃªncia do worker era sobrescrita. O FluxoLoad agora bloqueia um segundo download enquanto o primeiro estiver ativo, evitando essa concorrÃªncia nÃ£o suportada.
- Novo log mostrou que mesmo com um Ãºnico download `_update_progress` era chamado dentro do `QThread` e atualizava widgets fora da thread principal. `BrowserFluxoLoadApp` agora Ã© `QObject` e os slots de progresso/conclusÃ£o/falha estÃ£o registrados para entrega segura na thread da UI.
- A limitaÃ§Ã£o de um Ãºnico download foi substituÃ­da por fila sequencial: o usuÃ¡rio pode adicionar vÃ¡rios downloads, mas somente um `yt-dlp` roda por vez; o prÃ³ximo inicia automaticamente apÃ³s sucesso ou apÃ³s fechar o erro.
- Cards dos downloads enfileirados agora sÃ£o criados imediatamente com o estado `Na fila...`; cada item permanece visÃ­vel e Ã© promovido ao estado ativo quando chega sua vez.
- Cards temporÃ¡rios vermelhos sÃ£o removidos ao concluir; o arquivo final reaparece como card normal clicÃ¡vel. O painel tambÃ©m atualiza ao ser aberto e depois de cada conclusÃ£o.
- Teste final realizado pelo usuÃ¡rio: download individual, fila com vÃ¡rios itens, cards visÃ­veis, execuÃ§Ã£o sequencial, atualizaÃ§Ã£o ao abrir o painel e abertura dos arquivos funcionaram sem crash.
- Instalador final gerado em `installer\\output\\FluxoLoad-1.1.0-Setup.exe` com Inno Setup; inclui termos de uso, desinstalador, Ã­cone, novos assets, Node interno e servidor local de PO Token. O instalador nÃ£o remove perfil do navegador nem downloads ao desinstalar.
- Pacote beta 1.1 gerado em `dist/beta1.1youtube_estable_FluxoLoad/beta1.1youtube_estable_FluxoLoad.exe` com o cÃ³digo atual e os assets do projeto.

- Nas capturas enviadas, o painel lateral de Downloads ocupa/excede a largura disponível da janela. Os cards, barras de progresso e botões ficam cortados horizontalmente, e o conteúdo do navegador fica comprimido. Investigar o dimensionamento e o layout do painel antes de alterar o comportamento dos downloads.
- Causa identificada: a URL longa do card ativo impunha uma largura mínima ao painel quando o carregamento começava.
- Correção aplicada em `fluxoload/browser_app.py`: o título do card agora pode encolher/quebrar linha, e o painel lateral foi limitado a 460 px; o fluxo de download não foi alterado.
- Validação: com URL longa, a janela permaneceu em 1180 px e o painel em no máximo 460 px; `python -m compileall -q fluxoload` passou.

## Estado atual — 23/11/2026

### Objetivo

Criar um aplicativo para Windows 10/11 64-bit que permita pesquisar conteúdo em redes sociais e baixar arquivos localmente, com suporte inicial a YouTube e expansão posterior para Instagram, TikTok e outras redes.

### Decisões tomadas

- Nome do projeto: **FluxoLoad**.
- Primeira plataforma: Windows 10/11 64-bit.
- Dados, downloads, histórico e configurações devem permanecer no dispositivo do usuário.
- O projeto antigo em `Projects/03-python-e-bots/baixarcoisas` será usado como referência para a lógica existente.
- A primeira prioridade é fazer o fluxo funcionar; otimização de consumo e troca do motor de navegação virão depois.
- A pesquisa deve funcionar dentro do aplicativo, em um navegador interno.
- O navegador interno será tratado como um módulo substituível. O protótipo funcional usa QtWebEngine; a alternativa mais leve será investigada depois.
- Não haverá servidor próprio nem telemetria planejada.

### O que já existe

- Interface inicial em Tkinter.
- Campo para URL e pesquisa no navegador padrão.
- Gerenciador de download separado da interface.
- Barra de progresso.
- Escolha da pasta de destino.
- Integração inicial preparada para `yt-dlp`.
- `requirements.txt` e instruções para empacotar com PyInstaller.
- Compilação sintática e imports validados.
- Protótipo de navegador interno criado em `browser_app.py`.
- Dependências instaladas também no interpretador usado por `py` após detectar duas instalações distintas do Python.
- `py run.py` está pronto para iniciar o aplicativo; imports de PySide6, QtWebEngine e yt-dlp foram validados.
- Barra de plataformas adicionada com atalhos para YouTube, Instagram e TikTok.
- O botão de download agora recusa sites fora das plataformas suportadas.
- Corrigido erro de download sem FFmpeg: o núcleo agora detecta FFmpeg e usa formato único como fallback.
- Removidos a barra de pesquisa/URL e o botão de pesquisa; a navegação inicial ocorre pelos botões das plataformas.
- FFmpeg configurado com o caminho exato do executável e mesclagem condicionada à detecção real do programa.
- Nomes de saída passaram a incluir o ID do vídeo e downloads não continuam arquivos parciais, reduzindo colisões de arquivos bloqueados.
- Arquivos intermediários agora ficam em `.fluxoload_work` e só o arquivo final é movido para a pasta de downloads após o processamento.
- Formato padrão ajustado para H.264 + AAC, evitando arquivos AV1/Opus que o Windows Media Player local não reproduz.
- Novos arquivos compatíveis recebem o sufixo `[compat]` para não serem confundidos com downloads antigos.
- YouTube Shorts bloqueados; somente vídeos normais do YouTube entram no fluxo de download.
- Shorts ocultados visualmente na navegação interna do YouTube por script do FluxoLoad.
- Painel lateral de downloads adicionado com botão no topo, URL, progresso e status do download atual.
- Painel passou a listar arquivos existentes na pasta de downloads e ganhou os botões Atualizar e Abrir diretório.
- Diálogo de opções adicionado para tipo vídeo/áudio, qualidade, idioma do áudio e legendas.
- Painel filtra somente `.mp4` e `.mp3`, com filtros por vídeo/áudio e botão para abrir cada arquivo no player externo padrão.
- Aba de Configurações adicionada com preferências persistentes em `%LOCALAPPDATA%\\FluxoLoad\\settings.json`.
- Preferências padrão agora alimentam o diálogo de cada download.
- Qualidade agora muda dinamicamente: vídeo mostra resoluções e áudio mostra kbps; a qualidade de áudio escolhida é aplicada ao MP3.
- Opção de áudio padrão descrita como “Padrão (recomendado) — MP3 192 kbps”, com explicação visível na escolha.
- Primeira etapa de refinamento visual adicionada: tema claro/escuro e cor de destaque configuráveis na aba Configurações.
- Refinamento visual aplicado com stylesheet global reutilizando os controles Qt existentes; home, abas, toolbar, cards de download e painel lateral agora acompanham o tema e a cor de destaque.
- Configurações ganharam restauração segura dos padrões, sem tocar nos arquivos baixados.
- Navegador e Configurações foram unificados em uma única área; abas visíveis removidas e acesso às configurações movido para engrenagem no canto superior direito.
- Cabeçalho visual refinado com marca FluxoLoad, ação de download destacada, espaçamento flexível e controles laterais mais limpos.
- Perfil persistente do navegador adicionado para manter cookies e login localmente; desafios anti-bot continuam sendo tratados manualmente pelo usuário.
- Cookies da sessão interna agora são exportados temporariamente em formato Netscape para o yt-dlp durante o download e apagados ao terminar.
- Sincronização de cookies reforçada com carregamento persistente e espera de 2,5 segundos antes de iniciar o yt-dlp.
- Removida a chamada incompatível `flushStore()`; a sincronização usa somente APIs disponíveis no PySide6 instalado.
- Teste real reproduziu o bloqueio e identificou EJS como causa; `yt-dlp[default]` e runtime Node foram habilitados para resolver os desafios JavaScript do YouTube.
- Download real validado com cookies em memória, Node/EJS e H.264/AAC; arquivo final de 6.672.796 bytes criado e nenhum cookie temporário deixado no `%TEMP%`.
- Primeiro pacote Windows gerado em `dist/FluxoLoad/FluxoLoad.exe` com os ícones copiados para `_internal/assets`.
- Extensões reais de navegador podem ser avaliadas futuramente, com créditos e licenças registrados.
- Tela inicial alterada para abrir diretamente com miniaturas circulares de YouTube, Instagram e TikTok; o Google não é mais carregado na inicialização.
- Avisos do console JavaScript do navegador interno foram silenciados na interface.
- Ícones enviados pelo usuário adicionados em `assets/` para YouTube, Instagram e TikTok.
- Botão `⌂ Home` adicionado à barra superior para retornar à tela das plataformas.

### Próxima etapa

1. Instalar `requirements.txt` e abrir o aplicativo com `run.py`.
2. Testar uma pesquisa e um download autorizado de YouTube.
3. Corrigir integração com playlists, formatos e FFmpeg.
4. Só depois avaliar consumo de memória, inicialização e alternativas ao motor provisório.

### Riscos conhecidos

- Navegadores internos aumentam o tamanho do executável e o consumo de memória.
- YouTube, Instagram e TikTok podem mudar seus mecanismos e exigir adaptações.
- Login e credenciais não devem ser capturados pelo aplicativo; o armazenamento seguro será planejado separadamente.
- O aplicativo deve ser usado somente para conteúdo que o usuário tenha autorização para baixar e conforme os termos de cada plataforma.

### Comandos atuais

```powershell
cd C:\Users\gilma\Projects\baixarcoisas
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

### Observacao pendente

- O painel de downloads apresenta um bug visual ao iniciar o carregamento; registrar para identificacao antes de alterar o comportamento.

### Empacotamento beta 1.1

- Instalador final gerado em `installer\output\FluxoLoad-1.1.0-Setup-v2.exe` com Inno Setup.
- O instalador inclui termos de uso, desinstalador, ícone do FluxoLoad, assets adicionais, Node interno e servidor local de PO Token.
- O instalador não inicia mais o aplicativo automaticamente; isso evita o erro 4551 quando o Windows bloqueia o executável por falta de assinatura/reputação.
- O arquivo `executar_fluxoload.cmd` foi incluído para teste local de desbloqueio do executável, mas o Smart App Control ainda pode exigir uma permissão manual do Windows.

### Pacote alternativo pelo código-fonte

- Criada a pasta `distribuicao\FluxoLoad-Fonte`, separada do executável e do instalador.
- O pacote inclui `run.py`, `fluxoload`, `assets`, `requirements.txt`, licença, termos de uso e `executar_fluxoload_fonte.cmd`.
- O lançador procura o Python instalado; se não encontrar, tenta instalar o Python oficial pelo WinGet, cria `.venv`, instala as dependências via pip e executa `run.py`.
- O instalador ficou separado em `distribuicao\FluxoLoad-Executavel`.
