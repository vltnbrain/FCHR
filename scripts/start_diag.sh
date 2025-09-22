#!/usr/bin/env bash
# FCHR: one‑shot launcher + self‑diagnostics for GCE VM (SSH in browser)
set -euo pipefail

TS="$(date +%Y%m%d-%H%M%S)"
REPORT="/tmp/fchr_diag_${TS}.log"
REPO_URL="https://github.com/vltnbrain/FCHR.git"
REPO_DIR="${REPO_DIR:-$HOME/FCHR}"
COMPOSE_FILE="infra/prod/docker-compose.yml"

log() { echo -e "$*" | tee -a "$REPORT"; }
ok()  { log "[ OK ] $*"; }
warn(){ log "[WARN] $*"; }
fail(){ log "[FAIL] $*"; }

section(){ log "\n===== $* ====="; }

run() {
  local desc="$1"; shift
  log "-- $desc"
  if "$@" >>"$REPORT" 2>&1; then ok "$desc"; else fail "$desc"; return 1; fi
}

section "Environment"
{
  echo "DATE: $(date)"
  echo "USER: $(id)"
  echo "HOST: $(hostname)"
  echo "OS: $(uname -a)"
  [ -f /etc/os-release ] && cat /etc/os-release
} >>"$REPORT" 2>&1
ok "Collected environment info (report: $REPORT)"

section "Prerequisites"
if ! command -v docker >/dev/null 2>&1; then
  run "Install Docker" bash -lc "curl -fsSL https://get.docker.com | sh" || true
else ok "Docker present: $(docker --version)"; fi

run "Install docker-compose plugin" sudo apt-get update -y || true
run "Install docker-compose-plugin + git + curl" sudo apt-get install -y docker-compose-plugin git curl || true

if ! groups | grep -q docker; then
  warn "User not in docker group. Using sudo for docker commands."
  DOCK="sudo docker"
else
  DOCK="docker"
fi

section "Fetch repository"
if [ -d "$REPO_DIR/.git" ]; then
  run "Git pull" bash -lc "cd '$REPO_DIR' && git pull --ff-only" || true
else
  run "Git clone" git clone "$REPO_URL" "$REPO_DIR" || true
fi

if [ ! -f "$REPO_DIR/$COMPOSE_FILE" ]; then
  fail "Compose file not found: $REPO_DIR/$COMPOSE_FILE"
  exit 1
fi

section ".env setup"
if [ ! -f "$REPO_DIR/.env" ]; then
  run "Seed .env from example" cp "$REPO_DIR/.env.example" "$REPO_DIR/.env" || true
fi
if ! grep -q '^SECRET_KEY=' "$REPO_DIR/.env"; then
  SK=$(openssl rand -hex 32 2>/dev/null || echo devsecret)
  echo "SECRET_KEY=$SK" >> "$REPO_DIR/.env"
  ok "SECRET_KEY appended to .env"
fi

section "Build & start stack"
run "docker compose up -d --build" bash -lc "cd '$REPO_DIR' && $DOCK compose -f '$COMPOSE_FILE' up -d --build" || true

section "Containers status"
run "docker compose ps" bash -lc "cd '$REPO_DIR' && $DOCK compose -f '$COMPOSE_FILE' ps" || true

section "Health checks"
# backend health from inside container (more reliable)
run "backend /healthz" bash -lc "cd '$REPO_DIR' && $DOCK compose exec -T backend curl -sf http://localhost:8000/healthz" || true
# nginx health from host
run "nginx /healthz (host)" curl -sf http://localhost/healthz || true

section "Ports"
run "Listening 80/8000" bash -lc "ss -ltnp | grep -E ':(80|8000)\s' || true" || true

section "Quick diagnostics"
# If nginx down, show last logs
if ! curl -sf http://localhost/healthz >/dev/null 2>&1; then
  warn "nginx health failed — printing nginx logs"
  bash -lc "cd '$REPO_DIR' && $DOCK compose logs --tail=200 nginx" >>"$REPORT" 2>&1 || true
fi
# If backend down, show backend logs
if ! (bash -lc "cd '$REPO_DIR' && $DOCK compose exec -T backend curl -sf http://localhost:8000/healthz" >/dev/null 2>&1); then
  warn "backend health failed — printing backend logs"
  bash -lc "cd '$REPO_DIR' && $DOCK compose logs --tail=200 backend" >>"$REPORT" 2>&1 || true
fi

section "Summary"
NGX="UP"; (curl -sf http://localhost/healthz >/dev/null 2>&1) || NGX="DOWN"
BE="UP"; (bash -lc "cd '$REPO_DIR' && $DOCK compose exec -T backend curl -sf http://localhost:8000/healthz" >/dev/null 2>&1) || BE="DOWN"
log "Nginx: $NGX | Backend: $BE"
log "Report saved to: $REPORT"
if [ "$NGX" = "UP" ]; then ok "Open: http://$(curl -s http://ifconfig.me 2>/dev/null || echo '<VM-IP>')"; fi

exit 0

