# Problemas já vistos e o conserto

| Sintoma | Causa e conserto |
|---|---|
| `git clone` pede usuário e senha do GitHub | Repositório privado. O GitHub não aceita a senha da conta. Torne público (se só tem scripts) ou crie um *fine-grained token* só de leitura. |
| SSH: `Permission denied, please try again` (pede senha) | Senha digitada errada (a tela não mostra nada, e teclados de celular alteram letras). Redefina a senha do root pelo painel do provedor. |
| Console VNC do provedor não cola | Limitação dele. Use SSH. |
| SSH: `Permission denied (publickey)` sem pedir frase-senha | A VPS não reconhece a chave. Na VPS: `ssh-keygen -lf ~/.ssh/authorized_keys` (o fingerprint da chave tem que aparecer), `sed 's/AAAA[^ ]*/<chave>/' ~/.ssh/authorized_keys \| cat -A` (caracteres escondidos, `^M`), e `journalctl -u ssh --since "5 min ago"`. |
| SSH pede a frase-senha e recusa | **Caps Lock ligado** (já aconteceu). A frase não aparece enquanto se digita. Teste local: `ssh-keygen -y -f $env:USERPROFILE\.ssh\id_ed25519`. |
| SSH dá timeout depois de várias falhas | fail2ban bloqueou o IP (5 falhas em 10 min). `fail2ban-client status sshd` e `fail2ban-client unban IP`. |
| `curl -I http://localhost:80` na VPS devolve **405** | O painel está **vivo**: o `HEAD` não é aceito. Não é erro. |
| Navegador: `ERR_CONNECTION_REFUSED` no painel | Túnel aberto no lugar errado (dentro da VPS em vez do PowerShell do PC) ou com porta local diferente de 80 (o redirecionamento de login perde a porta). Use `-L 80:127.0.0.1:80`, como administrador. Feche o `dotnet run` local, que ocupa a porta 80. |
| Painel pelo celular | Port forwarding do Termius é instável (o Android pausa o app). Alternativa temporária: `cloudflared` em container com `tunnel --url http://127.0.0.1:80` gera um link HTTPS público. Desligue-o (`docker rm -f`) ao terminar e não compartilhe o link. |
| Cai ao escolher o servidor | IP resolver: `Public`, ou `Custom` com o IP. No mesmo PC, `127.127.127.127`. |
| "wzAudio.dll não foi encontrado" | O `main.exe` está fora da pasta do cliente. Mova-o para onde está a pasta `Data` e o `wzAudio.dll`, e aponte o launcher para ele. |
| `main.exe` não aparece depois de extrair | O zip do launcher não traz `main.exe`. Se o zip era do cliente, veja o Histórico de proteção do Windows (antivírus) e subpastas. |
| VS Code não acha `OnlineChatCommandPlugIn.cs` | Pasta errada aberta. O topo do Explorer deve ser `OPENMU`. |
| Plugin de reset: "não está habilitado" | O plugin vem desativado. Ative em *Plugins*, configure o ⚙ e recarregue os servidores. |
| Reset volta ao nível 10 com 1500 pontos, mesmo depois de configurar | A configuração não foi gravada: faltou o **Yes** na janela "Change" que abre depois do *Submit*. Reabra o ⚙, confira os valores e recarregue os servidores. |
| Plugin de reset não aparece em *Plugins* | A lista tem várias páginas. Busque `Reset Feature` (nome) ou `ResetFeaturePlugIn` (tipo). Não confunda com *Stat Reset Feature*. Botão verde *Activate* = desligado; amarelo *Deactivate* = ligado. |
| Mudança no painel não surtiu efeito | Falta **Reload configuration and restart all game servers** na página *Servers*. |
| `docker compose` ignorou `ports: !override` | Precisa do Docker Compose 2.24.4+. |
| Ícone vermelho nos `.gz` no `ls` | É só a cor do Linux para arquivos compactados. |
