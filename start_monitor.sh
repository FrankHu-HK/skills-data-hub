#!/bin/bash
# SkillHub monitor service daemon script：auto-restart on crash, keep resident
cd "$(dirname "$0")"
PORT=8866
PY="C:/Users/hu_ji/.workbuddy/binaries/python/versions/3.13.12/python.exe"

# release occupied'sport：if 8866 already listened by some process（mostly old instance frozen not exited), first taskkill release, 
# avoid the new instance  bind failedfall into"startthen-crash"loop. This is "data freeze from recurring"'sNo.second line of defense。
cleanup_port() {
  pid=$(netstat -ano 2>/dev/null | grep -E ":$PORT.*LISTEN" | awk '{print $5}' | head -1)
  if [ -n "$pid" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') release occupied port $PORT 'sprocess $pid" >> server.log
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
  echo "$(date '+%Y-%m-%d %H:%M:%S') server.py abnormal exit, 2seconds afterauto restart" >> server.log
  sleep 2
done
