#!/usr/bin/env bash
# Backup do banco do OpenMU (PostgreSQL dentro do container "database").
# Gera dois arquivos comprimidos por execução:
#   openmu-AAAA-MM-DD_HHMM.sql.gz          -> o banco inteiro (contas, personagens, itens)
#   openmu-globals-AAAA-MM-DD_HHMM.sql.gz  -> usuários/roles do PostgreSQL
# Apaga backups mais antigos que KEEP_DAYS dias.
#
# Variáveis opcionais: BACKUP_DIR, KEEP_DAYS, DB_CONTAINER, DB_USER, DB_NAME, ENV_FILE
set -euo pipefail

ENV_FILE="${ENV_FILE:-/opt/OpenMU/deploy/all-in-one/.env}"
env_value() { [[ -f "$ENV_FILE" ]] && grep -E "^$1=" "$ENV_FILE" | tail -1 | cut -d= -f2- || true; }

BACKUP_DIR="${BACKUP_DIR:-/var/backups/openmu}"
KEEP_DAYS="${KEEP_DAYS:-14}"
DB_CONTAINER="${DB_CONTAINER:-database}"
DB_USER="${DB_USER:-$(env_value DB_ADMIN_USER)}"; DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-$(env_value DB_NAME)}";       DB_NAME="${DB_NAME:-openmu}"

STAMP="$(date +%F_%H%M)"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
umask 077

dump() { # $1 = arquivo final, demais = comando
  local final="$1"; shift
  local tmp="$final.part"
  if "$@" | gzip -9 > "$tmp" && gzip -t "$tmp" && [[ -s "$tmp" ]]; then
    mv "$tmp" "$final"
  else
    rm -f "$tmp"
    echo "ERRO: falha ao gerar $final" >&2
    return 1
  fi
}

dump "$BACKUP_DIR/openmu-$STAMP.sql.gz" \
  docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME"
dump "$BACKUP_DIR/openmu-globals-$STAMP.sql.gz" \
  docker exec "$DB_CONTAINER" pg_dumpall -U "$DB_USER" --globals-only

find "$BACKUP_DIR" -name 'openmu-*.sql.gz' -mtime +"$KEEP_DAYS" -delete

echo "$(date '+%F %T') backup ok: $BACKUP_DIR/openmu-$STAMP.sql.gz ($(du -h "$BACKUP_DIR/openmu-$STAMP.sql.gz" | cut -f1))"
