#!/usr/bin/env bash
# Instala o backup diário do OpenMU (roda todo dia às 04:00, horário da VPS).
# Uso: sudo bash install-backup.sh
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Rode com sudo: sudo bash $0" >&2; exit 1; }
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

apt-get install -y cron >/dev/null
systemctl enable --now cron

install -m 755 "$SCRIPT_DIR/backup.sh" /usr/local/bin/openmu-backup
cat > /etc/cron.d/openmu-backup <<'CRON'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
0 4 * * * root /usr/local/bin/openmu-backup >> /var/log/openmu-backup.log 2>&1
CRON
chmod 644 /etc/cron.d/openmu-backup

echo "==> Fazendo um backup agora para testar"
/usr/local/bin/openmu-backup
echo
echo "Pronto. Backups em /var/backups/openmu (14 dias), log em /var/log/openmu-backup.log"
