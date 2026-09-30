#!/usr/bin/env bash
# Deploy Meta comment moderation to GCE protocol-app.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${GCP_PROJECT:-protocol-home-e1}"
ZONE="${GCP_ZONE:-europe-central2-a}"
VM="${GCP_VM:-protocol-app}"
REMOTE="/opt/kravira-meta-comments"
SA_SRC="${GOOGLE_APPLICATION_CREDENTIALS:-$HOME/.config/mcp-google-sheets/service-account.json}"

gcloud config set project "$PROJECT" --quiet >/dev/null
STATUS="$(gcloud compute instances describe "$VM" --zone="$ZONE" --format='get(status)')"
if [[ "$STATUS" != "RUNNING" ]]; then
  echo "Starting $VM ..."
  gcloud compute instances start "$VM" --zone="$ZONE" --quiet
  sleep 20
fi

ssh() { gcloud compute ssh "$VM" --zone="$ZONE" --quiet --command="$1"; }

echo "[1] remote dirs"
ssh "sudo mkdir -p '$REMOTE/src' '$REMOTE/logs' && sudo chown -R \"\$(whoami):\$(whoami)\" '$REMOTE'"

echo "[2] sync code"
gcloud compute scp --zone="$ZONE" --recurse --quiet \
  "$ROOT/src/comment_moderation" "$VM:$REMOTE/src/"

echo "[3] env from Secret Manager + SA (values not printed)"
gcloud compute scp --zone="$ZONE" --quiet \
  "$ROOT/scripts/assemble_comments_env_from_sm.sh" \
  "$VM:/tmp/assemble_comments_env_from_sm.sh"
gcloud compute scp --zone="$ZONE" --quiet "$SA_SRC" "$VM:$REMOTE/service-account.json"
ssh "chmod 700 /tmp/assemble_comments_env_from_sm.sh
COMMENTS_ENV='$REMOTE/.env' bash /tmp/assemble_comments_env_from_sm.sh
chmod 600 '$REMOTE/service-account.json'"

echo "[4] venv + deps"
ssh "python3 -m venv '$REMOTE/.venv' 2>/dev/null || true
'$REMOTE/.venv/bin/pip' install -q -U pip
'$REMOTE/.venv/bin/pip' install -q -r '$REMOTE/src/comment_moderation/requirements.txt'"

echo "[5] systemd timer: 09/15/21 МСК"
UNIT_TMP="$(mktemp)"
cat >"$UNIT_TMP" <<'EOF'
[Unit]
Description=Kravira Meta comment moderation
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/opt/kravira-meta-comments
Environment=PYTHONUNBUFFERED=1
Environment=TZ=Europe/Minsk
ExecStart=/opt/kravira-meta-comments/.venv/bin/python /opt/kravira-meta-comments/src/comment_moderation/__main__.py
Nice=10

[Install]
WantedBy=multi-user.target
EOF
TIMER_TMP="$(mktemp)"
cat >"$TIMER_TMP" <<'EOF'
[Unit]
Description=Kravira Meta comment moderation (3x daily)

[Timer]
# VM в UTC; 06/12/18 UTC = 09:00, 15:00, 21:00 Europe/Minsk
OnCalendar=*-*-* 06,12,18:00:00
Persistent=true
RandomizedDelaySec=60

[Install]
WantedBy=timers.target
EOF
gcloud compute scp --zone="$ZONE" --quiet "$UNIT_TMP" "$VM:/tmp/kravira-meta-comments.service"
gcloud compute scp --zone="$ZONE" --quiet "$TIMER_TMP" "$VM:/tmp/kravira-meta-comments.timer"
rm -f "$UNIT_TMP" "$TIMER_TMP"
ssh "sudo mv /tmp/kravira-meta-comments.service /etc/systemd/system/kravira-meta-comments.service
sudo mv /tmp/kravira-meta-comments.timer /etc/systemd/system/kravira-meta-comments.timer
sudo systemctl daemon-reload
sudo systemctl enable --now kravira-meta-comments.timer
systemctl list-timers kravira-meta-comments.timer --no-pager"

echo "[6] first remote run"
ssh "cd '$REMOTE' && .venv/bin/python src/comment_moderation/__main__.py" || true
echo "done"
