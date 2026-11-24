# FluxoLoad 1.2

- Instalação automática do portable em `C:\Program Files\FluxoLoad`.
- Registro em Aplicativos instalados, atalhos e desinstalador.
- Preservação do portable original, downloads, cookies e configurações pessoais.
- Verificação de espaço livre e log de instalação em `%TEMP%\FluxoLoad-install.log`.
- Correção da inicialização do Qt: `QApplication` é criado antes dos ícones.
- Home usa os PNGs claros e escuros das plataformas conforme o tema selecionado.
- Portable incluído sem wheelhouse nesta build; a instalação precisa de internet para baixar dependências.
