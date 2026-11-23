# Estudar o código do OpenMU no Windows

O guia completo está em `assets/kit/ESTUDO.md`. Este arquivo resume o roteiro e as armadilhas.

## Ambiente

1. Git, Node.js LTS e VS Code (`winget install Git.Git OpenJS.NodeJS.LTS Microsoft.VisualStudioCode`),
   mais a extensão **C# Dev Kit**. O .NET SDK 10 também é necessário. Não precisa de PostgreSQL com `-demo`.
2. `git clone https://github.com/MUnique/OpenMU.git` em `C:\Dev`, `git switch -c estudo`,
   `dotnet restore`, `dotnet build src/MUnique.OpenMU.sln`.
3. Rodar: `dotnet run --project src/Startup/MUnique.OpenMU.Startup.csproj -- -demo -autostart`. O painel
   abre em `http://localhost` sem login. No modo demo nada é salvo. A janela fica ocupada: use outra
   para os demais comandos. **Feche o túnel SSH do painel antes**, porque os dois usam a porta 80.
4. Jogar nele: launcher com `127.127.127.127`, porta 44405. Se cair, IP resolver `Loopback`.

## Armadilhas já vistas no VS Code

- **Abrir a pasta errada** (a pasta do usuário em vez de `C:\Dev\OpenMU`): o Explorer deve mostrar
  `OPENMU` no topo. Use *File → Open Folder*.
- A tela **Workspace Trust / Restricted Mode**: confiar é seguro para o repositório oficial. Em pastas
  desconhecidas, deixe em modo restrito.
- A aba "Get Started with C# Dev Kit" pode ser fechada. Ctrl+Shift+E "não faz nada" se o Explorer já
  está aberto. **Ctrl+P** abre arquivos pelo nome.
- Depois de abrir a pasta, a extensão leva alguns minutos para carregar os projetos.

## Ordem de leitura (`src/`)

`Startup` → `Network` → `ConnectServer` → `GameServer/MessageHandler` → `GameLogic/PlayerActions` →
`GameLogic/PlugIns/ChatCommands` → `PlugIns` (leia o Readme) → `DataModel` e `Persistence` →
`Web/AdminPanel`. Documentação: `docs-website/docs/development/architecture.md` e
`solution-structure.md`. Comece seguindo um comando de chat (`OnlineChatCommandPlugIn.cs`,
`GetMoneyChatCommandPlugIn.cs`) com F12 (definição) e Shift+F12 (referências).

## Primeiro exercício: comando /hora

Um plugin de chat é uma classe com `[Guid]` único, `[PlugIn]`, `[Display]`, `[ChatCommandHelp]`,
herdando `ChatCommandPlugInBase<EmptyChatCommandArgs>`, com `Key`, `MinCharacterStatusRequirement` e
`DoHandleCommandAsync`. O arquivo vai em `src/GameLogic/PlugIns/ChatCommands/` (o exemplo completo
está em `assets/kit/ESTUDO.md`; gere um GUID novo para cada plugin). A mensagem ao jogador sai por
`player.ShowBlueMessageAsync(...)`. Depois: `dotnet run` (recompila), conferir o plugin em
*Configuration → Plugins* e digitar `/hora` no jogo.

**Esse código nunca foi compilado.** Avise e peça a mensagem de erro, se houver (o projeto usa
StyleCop, então cabeçalho e comentários XML importam).

## Levar um plugin para a VPS

A VPS usa a imagem oficial `munique/openmu`, que não tem o código do usuário. É preciso construir uma
imagem a partir da branch dele (o Dockerfile está em `src/Startup/Dockerfile`) e apontar o compose
para ela. Configurações do painel (itens, monstros, resets) ficam no banco, não em arquivos, e não se
copiam por SSH: edite pelo painel da VPS, com backup antes.
