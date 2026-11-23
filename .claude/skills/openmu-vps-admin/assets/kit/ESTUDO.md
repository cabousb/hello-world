# Estudar o código do OpenMU no seu PC (Windows)

Roteiro para rodar o OpenMU a partir do código-fonte, ler os projetos na ordem certa e fazer
o primeiro plugin. Tudo roda **no seu PC**, sem mexer na VPS.

> Os caminhos abaixo foram conferidos no repositório. Os comandos do passo 1 a 4 seguem a
> documentação oficial (`docs-website/docs/getting-started/from-source.md`). O código do
> exercício (passo 6) **não foi compilado**: pode precisar de pequenos ajustes.

## 1. Ferramentas

| Ferramenta | Como |
|---|---|
| .NET SDK 10 | já instalado; confira com `dotnet --version` |
| Git | `winget install Git.Git` |
| Node.js LTS | `winget install OpenJS.NodeJS.LTS` (a documentação lista como requisito) |
| VS Code + extensão **C# Dev Kit** | `winget install Microsoft.VisualStudioCode` e instale a extensão pelo painel de extensões |

Não precisa de PostgreSQL: o modo `-demo` guarda tudo na memória.

## 2. Baixar o código

```powershell
mkdir C:\Dev
cd C:\Dev
git clone https://github.com/MUnique/OpenMU.git
cd OpenMU
git switch -c estudo
```

Faça as suas alterações na branch `estudo`. Assim a `master` continua igual à do projeto
e dá para atualizá-la depois com `git pull`.

## 3. Compilar

```powershell
dotnet restore
dotnet build src/MUnique.OpenMU.sln
```

A primeira vez demora, porque baixa os pacotes.

## 4. Rodar em modo demonstração

**Feche antes o túnel SSH do painel da VPS**, porque ele usa a porta 80 do PC e o painel local
também usa a 80.

```powershell
dotnet run --project src/Startup/MUnique.OpenMU.Startup.csproj -- -demo -autostart
```

- O painel abre em **http://localhost** (sem login em modo demo).
- Em modo demo **nada é salvo**: o banco é refeito a cada início.
- Para jogar nele: no launcher use host `127.127.127.127` (**não** `127.0.0.1`, o cliente
  bloqueia) e porta `44405`. Se cair depois de escolher o servidor, vá em
  *Configuration → System* e ponha o **IP Resolver** em `Loopback`.

Para parar: **Ctrl+C**.

## 5. Ordem de leitura

Abra a pasta `C:\Dev\OpenMU` no VS Code e leia nesta ordem. Cada projeto de `src/` tem um
`Readme.md`.

| # | Pasta | O que olhar |
|---|---|---|
| 1 | `src/Startup` | Como tudo é ligado e iniciado num só processo |
| 2 | `src/Network` | Conexão TCP e pacotes do protocolo do MU |
| 3 | `src/ConnectServer` | O servidor mais simples: lista de servidores |
| 4 | `src/GameServer/MessageHandler` | Pacote do cliente → ação (um handler por tipo de pacote) |
| 5 | `src/GameLogic/PlayerActions` | As regras do jogo, sem saber nada de rede (login, itens, trade, party...) |
| 6 | `src/GameLogic/PlugIns/ChatCommands` | Comandos de chat: o melhor lugar para o primeiro exercício |
| 7 | `src/PlugIns` | O sistema de plugins (o `Readme.md` explica bem) |
| 8 | `src/DataModel` e `src/Persistence` | Entidades e acesso ao banco |
| 9 | `src/Web/AdminPanel` | O painel, em Blazor |

Documentação: `docs-website/docs/development/architecture.md` e `solution-structure.md`.

**Como ler:** escolha uma ação (por exemplo, `/online`, em `OnlineChatCommandPlugIn.cs`) e
siga o caminho dela: chat no cliente → handler em `GameServer/MessageHandler` → plugin em
`GameLogic/PlugIns/ChatCommands` → resposta ao jogador. Use **F12** (ir para a definição) e
**Shift+F12** (ver referências) no VS Code.

Comandos bons para ler primeiro, do mais simples ao mais cheio:
`OnlineChatCommandPlugIn.cs` → `GetMoneyChatCommandPlugIn.cs` → `NoticeChatCommandPlugIn.cs`.

## 6. Primeiro exercício: o comando /hora

Crie `src/GameLogic/PlugIns/ChatCommands/HoraChatCommandPlugIn.cs`:

```csharp
// <copyright file="HoraChatCommandPlugIn.cs" company="MUnique">
// Licensed under the MIT License. See LICENSE file in the project root for full license information.
// </copyright>

namespace MUnique.OpenMU.GameLogic.PlugIns.ChatCommands;

using System.ComponentModel.DataAnnotations;
using System.Runtime.InteropServices;
using MUnique.OpenMU.GameLogic.PlugIns.ChatCommands.Arguments;
using MUnique.OpenMU.PlugIns;

/// <summary>
/// A chat command plugin which shows the current server time.
/// </summary>
[Guid("0A1B2C92-9435-4CB2-A6B8-EE38FDCEEE88")]
[PlugIn]
[Display(Name = "Comando /hora", Description = "Mostra a hora do servidor.")]
[ChatCommandHelp(Command, typeof(EmptyChatCommandArgs), CharacterStatus.Normal)]
public class HoraChatCommandPlugIn : ChatCommandPlugInBase<EmptyChatCommandArgs>, IChatCommandPlugIn
{
    private const string Command = "/hora";

    /// <inheritdoc />
    public override string Key => Command;

    /// <inheritdoc />
    public override CharacterStatus MinCharacterStatusRequirement => CharacterStatus.Normal;

    /// <inheritdoc />
    protected override async ValueTask DoHandleCommandAsync(Player player, EmptyChatCommandArgs arguments)
    {
        await player.ShowBlueMessageAsync($"Hora do servidor: {DateTime.Now:HH:mm:ss}").ConfigureAwait(false);
    }
}
```

Depois:

1. Pare o servidor (Ctrl+C), rode `dotnet build` e inicie de novo.
2. Em *Configuration → Plugins* no painel, procure "Comando /hora" e confira se está **ativo**.
3. No jogo, entre com uma conta de teste e digite `/hora` no chat.

O `[Guid]` precisa ser **único** por plugin. O desta página foi gerado só para você.

Ideias para evoluir: aceitar um argumento (veja `GetMoneyChatCommandPlugIn.cs`, que usa
`ArgumentsBase`), restringir a GM (`CharacterStatus.GameMaster`) ou mostrar quantos jogadores
estão online (veja `OnlineChatCommandPlugIn.cs`).

## 7. Levar o seu plugin para a VPS

A VPS usa a **imagem oficial** do OpenMU, então ela não tem o seu código. Para rodar a sua
versão lá, é preciso construir uma imagem própria a partir da sua branch. É um assunto para
depois, quando o plugin estiver funcionando no seu PC.
