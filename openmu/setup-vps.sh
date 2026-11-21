#!/usr/bin/env bash
# Instala o OpenMU numa VPS Ubuntu/Debian limpa.
# Uso (na VPS, como root ou com sudo):
#   sudo bash setup-vps.sh
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/OpenMU}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $EUID -ne 0 ]]; then
  echo "Rode com sudo: sudo bash $0" >&2
  exit 1
fi

echo "==> Atualizando pacotes"
apt-get update -y
apt-get install -y ca-certificates curl git ufw openssl

echo "==> Instalando Docker (se ainda não tiver)"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker

echo "==> Swap de 2 GB (se a VPS não tiver nenhuma)"
if [[ -z "$(swapon --show)" ]]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> Firewall (UFW)"
ufw allow OpenSSH
ufw allow 44405:44406/tcp   # connect servers
ufw allow 45901:45903/tcp   # game servers
ufw allow 45980/tcp         # chat server
ufw --force enable

echo "==> Baixando o OpenMU em $INSTALL_DIR"
if [[ -d "$INSTALL_DIR/.git" ]]; then
  git -C "$INSTALL_DIR" pull --ff-only
else
  git clone https://github.com/MUnique/OpenMU.git "$INSTALL_DIR"
fi
cd "$INSTALL_DIR/deploy/all-in-one"

cp "$SCRIPT_DIR/docker-compose.vps.yml" .

if [[ ! -f .env ]]; then
  echo "==> Gerando .env com senhas aleatórias"
  DB_PW="$(openssl rand -hex 24)"
  ADMIN_PW="$(openssl rand -base64 18 | tr -d '/+=')"
  cat > .env <<ENV
DB_HOST=database
DB_ADMIN_USER=postgres
DB_ADMIN_PW=$DB_PW
DB_NAME=openmu
OPENMU_ADMIN_USER=admin
OPENMU_ADMIN_PASSWORD=$ADMIN_PW
OPENMU_ADMIN_TOTP_SECRET=
RESOLVE_IP=public
ENV
  chmod 600 .env
  echo
  echo "  Usuário do painel admin: admin"
  echo "  Senha do painel admin:   $ADMIN_PW"
  echo "  (também está salva em $INSTALL_DIR/deploy/all-in-one/.env)"
  echo
fi

echo "==> Subindo os containers"
docker compose -f docker-compose.yml -f docker-compose.vps.yml pull
docker compose -f docker-compose.yml -f docker-compose.vps.yml up -d --no-build
docker compose -f docker-compose.yml -f docker-compose.vps.yml ps

IP="$(curl -fsS https://api.ipify.org || echo IP_DA_VPS)"
cat <<MSG

Pronto! Próximos passos:
 1. No SEU computador, abra um túnel para o painel admin:
      ssh -L 8080:localhost:80 SEU_USUARIO@$IP
    e acesse http://localhost:8080
 2. No launcher do OpenMU, use o host $IP e a porta 44405.
 3. Ver logs:  cd $INSTALL_DIR/deploy/all-in-one && docker compose logs -f openmu-startup
MSG
