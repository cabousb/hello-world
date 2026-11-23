---
name: openmu-vps-admin
description: Instalar, proteger, configurar e administrar um servidor de MU Online com o OpenMU (emulador open source em C#/.NET) numa VPS Linux com Docker, e ajudar a estudar ou modificar o código dele. Use sempre que o usuário falar de servidor de MU, MU Online, muonline, OpenMU, resets e níveis, Castle Siege, eventos, sets, painel admin do OpenMU, túnel SSH para o painel, backup do banco do OpenMU, ClientLauncher, main.exe ou cliente Season 6, ou quiser montar, configurar ou colocar online um servidor de MU, mesmo sem citar OpenMU pelo nome.
---

# Servidor de MU Online com OpenMU numa VPS

Este guia vem de uma instalação real, feita passo a passo com um estudante de programação
iniciante em Linux. Os erros que apareceram no caminho estão em `references/troubleshooting.md`.

## Como conduzir a conversa

- **Diga onde cada comando é digitado.** Iniciantes confundem "PowerShell do PC", "terminal da
  VPS" e "terminal do VS Code". O prompt `PS C:\...>` é o PC e `root@...:~#` é a VPS.
- **Um comando por vez, e peça a saída** (ou um print) antes de seguir. Quase todo erro foi
  resolvido olhando a mensagem exata.
- **Nunca peça nem aceite senhas, frases-senha, chave privada ou token.** Quando algo sensível
  puder aparecer numa saída, peça para apagar antes de colar. Se aparecer, avise para trocar.
- **Seja honesto sobre o que foi testado.** O sandbox do Claude não roda Docker, então scripts e
  código só são verificados em sintaxe e lógica. Diga isso e peça a saída da primeira execução real.
- **Confira na fonte antes de afirmar.** Clone o repositório do OpenMU (`--depth 1`) no scratchpad e leia
  `docs-website/docs/` e o código. A documentação mudou coisas que a memória erra (portas dos game
  servers agora são 45901+, senhas padrão foram trocadas). Cite o que foi conferido e o que não foi.
- **Dados pessoais não entram em arquivos de repositório** (IP da VPS, usuário, e-mail). Use
  marcadores como `IP_DA_VPS`, porque o repositório pode ficar público.

## Limites e riscos que precisam ser ditos

- O OpenMU é MIT e escrito do zero, mas **o cliente e a marca "MU Online" são da Webzen**. Estudar e
  testar localmente é uma coisa. Abrir ao público, e principalmente cobrar por VIP ou itens, traz risco
  de notificação ou processo. Avise antes de o usuário abrir o servidor.
- O nome do servidor não deve usar "OpenMU". O projeto pede um nome próprio.
- Não indique links de download do cliente. Aponte o canal **#faq** do Discord do projeto
  (o link está no README do OpenMU) e recomende passar antivírus nos arquivos.
- Contas de teste (`test0`…`test9`, `test300`, `test400`, `testgm`…) têm senha igual ao login e
  algumas são GM. Apague-as, ou reinstale pela página *Setup* sem elas, antes de abrir ao público.

## Fluxo recomendado

1. **Entender o pedido:** versão (Season 6 Episode 3 ENG é o padrão e a mais completa; 0.95d e 0.75
   existem), onde vai rodar e o objetivo (estudo, amigos, público).
2. **Escolher a VPS.** Precisa ser Linux **KVM** (Ubuntu 24.04 recomendado). Windows Server não roda os
   containers Linux do OpenMU: recomende reinstalar com Ubuntu. Se o plano for OpenVZ/Virtuozzo ("VZ"
   no nome), o Docker pode não funcionar. Com 4 GB de RAM e 4 vCPU sobra folga (o servidor usou
   cerca de 1 GB).
3. **Instalar.** Use o kit em `assets/kit/` (cópia do que está em `openmu/` do repositório do usuário):
   `setup-vps.sh` (instala Docker, swap, UFW, clona o OpenMU, gera `.env` com senhas aleatórias e sobe
   tudo) e `docker-compose.vps.yml`. Detalhes e motivos no `README.md` do kit.
4. **Acessar o painel** pelo túnel SSH (abaixo).
5. **Proteger a VPS** (abaixo).
6. **Instalar o backup diário** (abaixo).
7. **Conectar o cliente** (abaixo).
8. **Configurar o jogo** pelo painel e **estudar o código** (referências).

## Por que o override `docker-compose.vps.yml`

O compose original é para teste local. Numa VPS ele publica o PostgreSQL numa porta aleatória com a
senha padrão, e o painel (porta 80) sem HTTPS. E **o Docker ignora o UFW**: porta publicada fica aberta
mesmo com o firewall fechado. O override tira o banco da internet, prende o painel em `127.0.0.1`,
publica só as portas do jogo e reinicia os containers sozinho.
Portas públicas: 44405 e 44406 (connect servers), 45901–45903 (game servers), 45980 (chat).

## Acessar o painel (túnel SSH)

No **PowerShell do PC, como administrador**, deixando a janela aberta:

```powershell
ssh -L 80:127.0.0.1:80 root@IP_DA_VPS
```

Depois, `http://127.0.0.1` no navegador (usuário `admin`, senha gerada no `.env`).

**A porta local tem que ser 80.** Com `-L 8888:...` o painel abre a tela de login mas redireciona para
`http://127.0.0.1/login` sem a porta, e o navegador dá `ERR_CONNECTION_REFUSED`. Se um `dotnet run`
local estiver ativo, ele ocupa a porta 80: feche um dos dois. A senha do painel se recupera na VPS com
`grep OPENMU_ADMIN_PASSWORD /opt/OpenMU/deploy/all-in-one/.env`.

## Segurança da VPS (ordem importa)

1. **Chave SSH ed25519 com frase-senha**, uma por computador (`ssh-keygen -t ed25519 -C "pc-1"`).
2. **Cadastrar a chave pública.** Com a senha ainda ativa: `scp` do `.pub` para a VPS, depois
   `cat ~/pc1.pub >> ~/.ssh/authorized_keys`, `sed -i 's/\r$//'` (arquivos do Windows trazem CRLF) e
   `chmod 600`. Num segundo computador, com a senha já desligada, a chave pública é cadastrada **a
   partir do primeiro**: copie a linha `ssh-ed25519 AAAA... pc-2` e acrescente com `nano`
   (evite `echo "..."` com texto colado, porque aspas curvas quebram o comando).
3. **Testar antes de desligar a senha**, em outra janela: `ssh root@IP`. Só prossiga se entrar.
4. **Desligar o login por senha:**
   `printf 'PasswordAuthentication no\nPermitRootLogin prohibit-password\n' > /etc/ssh/sshd_config.d/00-hardening.conf`,
   depois `sshd -t && systemctl restart ssh` e `sshd -T | grep -E "^(passwordauthentication|permitrootlogin)"`.
   O prefixo `00-` é de propósito: vale o primeiro valor lido, e o arquivo do provedor pode ter
   `PasswordAuthentication yes`. **Mantenha a janela antiga aberta** até testar a nova.
5. **fail2ban:** `apt-get install -y fail2ban && systemctl enable --now fail2ban`, e
   `fail2ban-client status sshd`. Bloqueia por 10 min após 5 falhas. Cuidado: o próprio usuário pode se
   bloquear (`fail2ban-client unban IP`).
6. **Plano B de acesso:** o login da área do cliente do provedor (console VNC, troca de senha do root,
   reinstalar). O console do painel não aceita colar texto. Ajude o usuário a listar o que guardar:
   frases-senha, chave privada (`id_ed25519`), login do provedor, senha do painel e o `.env`.

## Backup

`install-backup.sh` instala `/usr/local/bin/openmu-backup` e um cron diário às 04:00: faz `pg_dump` do
banco e `pg_dumpall --globals-only` (os usuários internos do PostgreSQL), valida o `.gz`, mantém 14
dias e nunca deixa arquivo parcial. **Não use** `--no-owner`/`--no-privileges`: o OpenMU usa vários
roles (config, account, friend, guild) e perderia as permissões na restauração.
Copie os arquivos para o PC de vez em quando (`scp "root@IP:/var/backups/openmu/*.gz" ...`), porque
backup só na VPS se perde junto com ela. Restauração e teste seguro num PostgreSQL temporário estão no
`README.md` do kit. A restauração em si não foi testada contra um PostgreSQL real.

## Cliente do jogo

- OpenMU não traz cliente. O FAQ oficial do Discord indica o cliente Season 6 Episode 3, um `main.exe`
  corrigido (*patched*) e um `ItemTooltip_eng.bmd` corrigido. O launcher oficial é o
  `MUnique.OpenMU.ClientLauncher`, que precisa do .NET (o SDK 10 já inclui o runtime).
- O zip do launcher **não** tem `main.exe`. Esse arquivo vem no cliente, junto com a pasta `Data` e o
  `wzAudio.dll`. O `main.exe` corrigido tem que ficar **na pasta do cliente**, substituindo o original
  (senão aparece "wzAudio.dll não foi encontrado"). Abra sempre pelo launcher, não pelo `main.exe`.
- No launcher: host da VPS, porta **44405** (cliente original) ou **44406** (MuMain, open source).
  No mesmo PC do servidor use `127.127.127.127` (nunca `127.0.0.1`, o cliente bloqueia).
- Mantenha o cliente fora de pastas sincronizadas (OneDrive): são centenas de MB. O antivírus pode
  apagar o `main.exe` corrigido (veja o Histórico de proteção). Eu não verifico esses arquivos:
  a decisão de confiar é do usuário.
- Se cair logo depois de escolher o servidor: *Configuration → System → IP resolver* (`Public` ou
  `Custom` com o IP).

## Configurar o jogo pelo painel

Menu **Configuration**: *General* (taxas de experiência), *Monsters*, *Items* (editor gráfico),
*Item set groups*, *Item options*, *Merchant stores* (loja dos NPCs, com Export/Import em JSON),
*Map editor*, *Item drops*, *Plugins* (ativar/desativar mecânicas e eventos) e *Chat commands*.
Toda mudança só vale depois de **Reload configuration and restart all game servers** na página *Servers*.
Faça `openmu-backup` antes de mudanças grandes. O modo `-demo` perde tudo ao reiniciar, então
configurações que devem ficar salvas são feitas no painel da VPS.

- **Castle Siege:** já existe; o estado aparece no painel inicial. Os horários usam o fuso de
  *Configuration → System → Time zone id*.
- **Eventos** (Blood Castle, Devil Square, invasões, Happy Hour): são plugins periódicos em *Plugins*,
  com horários no ⚙ e uma lista *Active on servers*.
- **Sets novos:** são criados em *Item set groups* e *Items*. O servidor aplica os bônus, mas o cliente
  calcula e mostra por conta própria nomes e valores, então a descrição pode ficar errada. Itens com
  modelos novos geralmente exigem mexer nos arquivos do cliente. O caminho seguro é remontar sets
  com itens que o cliente já conhece.

## Resets, níveis, "igual aos outros servidores"

Leia `references/resets-e-niveis.md`. Resumo: o plugin de reset vem **desligado**, o limite de resets é
**global**, e o que costuma ser pedido além disso (Master Reset, VIP com reset em nível menor, limite
por nível, bônus automático por nível, Zen por faixas) exige plugin.

## Estudar ou modificar o código

Leia `references/estudo-do-codigo.md` (ambiente no Windows, ordem de leitura, primeiro plugin `/hora`).
Para colocar o plugin na VPS é preciso construir uma imagem própria do OpenMU, pois a VPS usa a imagem
oficial. Isso fica para depois que o plugin funcionar no PC.

## Quando algo der errado

`references/troubleshooting.md` tem os sintomas já vistos, a causa e o conserto.
