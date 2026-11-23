# OpenMU na VPS — guia de estudo

Guia para subir o [OpenMU](https://github.com/MUnique/OpenMU) (emulador open source de
MU Online, em C#/.NET, licença MIT) numa VPS, estudar o código e, mais tarde, abrir
para o público.

## 1. Requisitos da VPS

| | Mínimo | Recomendado |
|---|---|---|
| Sistema | Ubuntu 22.04+ ou Debian 12+ | Ubuntu 24.04 LTS |
| RAM | 2 GB (com swap) | 4 GB |
| CPU | 1 vCPU | 2 vCPU |
| Disco | 20 GB | 40 GB SSD |

Portas usadas (TCP):

| Porta | Uso | Aberta para a internet? |
|---|---|---|
| 44405 | Connect server (cliente original) | Sim |
| 44406 | Connect server (cliente open source MuMain) | Sim |
| 45901–45903 | Game servers 1 a 3 | Sim |
| 45980 | Chat server | Sim |
| 80 | Painel admin | **Não**, só por túnel SSH (ou HTTPS depois) |
| 5432 | PostgreSQL | **Nunca** |

## 2. Instalação

Na VPS:

```bash
git clone <este repositório>
cd hello-world/openmu
sudo bash setup-vps.sh
```

O script:
1. instala Docker, Git e UFW;
2. cria 2 GB de swap se a VPS não tiver nenhuma;
3. libera no firewall só as portas do jogo e o SSH;
4. baixa o OpenMU em `/opt/OpenMU`;
5. cria um `.env` com **senhas aleatórias** para o banco e para o painel admin
   (a senha do painel aparece na tela; guarde-a);
6. sobe tudo com o override `docker-compose.vps.yml`.

### Por que existe o `docker-compose.vps.yml`?

O `docker-compose.yml` original foi feito para teste local. Numa VPS ele tem dois problemas:

- **Publica o PostgreSQL** numa porta aleatória, com a senha padrão `admin`.
- O painel admin fica na porta 80 sem HTTPS, então a senha trafega sem criptografia.

E um detalhe importante: **o Docker ignora o UFW**. Uma porta publicada pelo Docker fica
aberta mesmo que o firewall diga o contrário. Por isso o override tira o banco da internet
e prende o painel em `127.0.0.1`.

## 3. Acessar o painel admin

Do **seu computador**:

```bash
ssh -L 80:127.0.0.1:80 root@IP_DA_VPS
```

Deixe esse terminal aberto e acesse **http://127.0.0.1** no navegador (a porta local precisa ser 80: o painel redireciona para o login sem a porta). Entre com
`admin` e a senha que o script mostrou.

O banco é inicializado automaticamente para a **Season 6**. Pela página *Setup* você troca
a versão (0.75, 0.95d, Season 6), o número de game servers e escolhe se quer contas de teste.

## 4. Conectar o cliente

1. Baixe o [ClientLauncher do OpenMU](https://github.com/MUnique/OpenMU/releases/download/v0.9.0/MUnique.OpenMU.ClientLauncher_0.9.6.zip)
   e instale o [.NET 10 runtime](https://dotnet.microsoft.com/download/dotnet/10.0).
2. Host: o IP da VPS. Porta: `44405`. Selecione o `main.exe` do seu cliente Season 6.
3. Contas de teste: `test0` a `test9`, `test300`, `test400`, `testgm`... A **senha é igual ao
   login**.

O OpenMU não vem com cliente. O Discord do projeto indica onde conseguir um.

**Se cair logo após escolher o servidor:** o IP que o servidor informa ao cliente está
errado. Ajuste em *Configuration → System → IP resolver* (use `Public` ou `Custom` com o IP
da VPS) ou mude `RESOLVE_IP` no `.env`.

## 5. Comandos do dia a dia

```bash
cd /opt/OpenMU/deploy/all-in-one
alias dc='docker compose -f docker-compose.yml -f docker-compose.vps.yml'

dc ps                          # status
dc logs -f openmu-startup      # logs do servidor
dc restart openmu-startup      # reiniciar
dc pull && dc up -d --no-build # atualizar para a imagem mais nova

# backup do banco
dc exec -T database pg_dump -U postgres openmu | gzip > backup-$(date +%F).sql.gz
```

## 6. Roteiro para estudar o código

Rode a partir do código-fonte no seu PC (precisa do .NET SDK e de um PostgreSQL). Veja
`docs-website/docs/getting-started/from-source.md` no repositório do OpenMU.

Ordem sugerida de leitura, em `src/`:

| Ordem | Projeto | O que você aprende |
|---|---|---|
| 1 | `Network` | TCP, pacotes binários, criptografia do protocolo do MU |
| 2 | `ConnectServer` | Um servidor simples: lista de servidores e redirecionamento |
| 3 | `GameServer/MessageHandler` | Pacote do cliente → ação do jogador (`IPacketHandlerPlugIn`) |
| 4 | `GameLogic/PlayerActions` | Regras do jogo, sem saber nada de rede |
| 5 | `GameServer/RemoteView` | Servidor → cliente (padrão "views") |
| 6 | `DataModel` + `Persistence` | Modelagem e Entity Framework Core com PostgreSQL |
| 7 | `PlugIns` | Sistema de plugins: o jeito certo de customizar sem fazer fork |
| 8 | `Web` | Painel admin em Blazor |

Primeiro projeto prático: crie um plugin pequeno, por exemplo um comando de chat novo.
Os comandos existentes são bons exemplos, e a documentação está em
`docs-website/docs/development/`.

## 7. Checklist antes de abrir para o público

- [ ] **Jurídico:** o OpenMU é legal (MIT, escrito do zero), mas o **cliente e a marca
      "MU Online" são da Webzen**. Um servidor público, principalmente com doações, VIP ou
      venda de itens, pode receber notificação ou processo. Avalie esse risco.
- [ ] Não use "OpenMU" no nome do servidor. O projeto pede um nome próprio; "Powered by
      OpenMU" é bem-vindo.
- [ ] Apague ou bana **todas as contas de teste**, porque as senhas são públicas e algumas
      têm GM. Melhor ainda: reinstale pelo *Setup* sem contas de teste.
- [ ] Ative o segundo fator (TOTP) no usuário admin.
- [ ] Tenha um domínio e use HTTPS (`docker-compose.prod.yml` + certbot; veja
      `docs-website/docs/deployment/all-in-one.md`). Combine com o override da VPS só depois
      de entender o que cada arquivo publica.
- [ ] Configure backup automático diário do banco (cron + `pg_dump`) **fora** da VPS.
- [ ] SSH só com chave (desative o login por senha) e instale o `fail2ban`.
- [ ] Monitore os recursos (`docker stats`, ou o Grafana opcional em
      `docker-compose.monitoring.yml`, que usa cerca de 1 GB a mais de RAM).
- [ ] Lembre que o OpenMU ainda **não tem release estável**. Atualizações podem mudar o
      banco, então faça backup antes de cada `pull`.

## 8. Backup do banco

Tudo do jogo (contas, personagens, itens) fica no PostgreSQL. Sem backup, um erro no
*Setup* do painel, um disco com problema ou uma atualização ruim apagam tudo.

### Instalar o backup diário

Na VPS, dentro da pasta `hello-world/openmu`:

```bash
git pull
sudo bash install-backup.sh
```

O script instala o `openmu-backup`, agenda a execução **todo dia às 04:00** (horário da VPS) e
já faz um backup de teste. Os arquivos ficam em `/var/backups/openmu/`:

- `openmu-DATA.sql.gz`: o banco inteiro
- `openmu-globals-DATA.sql.gz`: os usuários internos do PostgreSQL (necessários para restaurar)

Backups com mais de 14 dias são apagados. O log fica em `/var/log/openmu-backup.log`.

```bash
openmu-backup                      # backup manual, a qualquer hora
ls -lh /var/backups/openmu         # ver os backups
tail /var/log/openmu-backup.log    # ver se o último deu certo
```

### Copiar para o seu PC (importante)

Backup que está só na VPS se perde junto com ela. De vez em quando, no **PowerShell do seu PC**:

```powershell
scp "root@IP_DA_VPS:/var/backups/openmu/*.gz" "C:\Muonline\Backups\"
```

### Restaurar

Troque `ARQUIVO` pelas datas dos arquivos que você quer usar. Isso **substitui o banco atual**.

```bash
cd /opt/OpenMU/deploy/all-in-one
DC="docker compose -f docker-compose.yml -f docker-compose.vps.yml"
$DC stop openmu-startup

# 1) usuários internos (avisos "role already exists" são normais)
zcat /var/backups/openmu/openmu-globals-ARQUIVO.sql.gz | docker exec -i database psql -U postgres

# 2) recriar o banco vazio e carregar o backup
docker exec database psql -U postgres -c "DROP DATABASE IF EXISTS openmu WITH (FORCE)" -c "CREATE DATABASE openmu"
zcat /var/backups/openmu/openmu-ARQUIVO.sql.gz | docker exec -i database psql -U postgres -d openmu -v ON_ERROR_STOP=1

$DC start openmu-startup
```

### Testar o backup sem risco

Para ter certeza de que o arquivo funciona, restaure-o num PostgreSQL **temporário**, sem tocar no
servidor de verdade:

```bash
docker run -d --name pgtest -e POSTGRES_PASSWORD=teste postgres:18
sleep 8
zcat /var/backups/openmu/openmu-globals-ARQUIVO.sql.gz | docker exec -i pgtest psql -U postgres
docker exec pgtest psql -U postgres -c "CREATE DATABASE openmu"
zcat /var/backups/openmu/openmu-ARQUIVO.sql.gz | docker exec -i pgtest psql -U postgres -d openmu -v ON_ERROR_STOP=1
docker exec pgtest psql -U postgres -d openmu -c "SELECT count(*) FROM account.\"Account\""
docker rm -f pgtest
```

Se o `SELECT` mostrar um número (as contas), o backup está bom.
