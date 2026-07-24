#!/bin/bash
# Skills Data Hub monitor service daemon script: auto-restart on crash, keep resident
cd "$(dirname "$0")"
PORT=8866
PY="$(command -v python3 || command -v python)"

# Release occupied port: if 8866 is already listened to by some process (mostly an old
# instance frozen and not exited), first taskkill to release it, avoiding the new instance
# bind failing and falling into a start-then-crash loop. This is the second line of defense
# against recurring data freeze.
cleanup_port() {
  pid=$(netstat -ano 2>/dev/null | grep -E ":$PORT.*LISTEN" | awk '{print $5}' | head -1)
  if [ -n "$pid" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') release occupied port $PORT process $pid" >> server.log
    taskkill //F //PID "$pid" >/dev/null 2>&1
    sleep 1
  fi
}

echo $$ > daemon.pid
while true; do
  cleanup_port
  echo "$(date '+%Y-%m-%d %H:%M:%S') start server.py" >> server.log
  "$PY" server.py >> server.log 2>&1 &
  SRV=$!
  echo $SRV > server.pid
  wait $SRV
  echo "$(date '+%Y-%m-%d %H:%M:%S') server.py abnormal exit, auto restart in 2 seconds" >> server.log
  sleep 2
done
