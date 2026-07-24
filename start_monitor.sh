#!/bin/bash
# SkillHub 监控服务守护脚本：崩溃自动重启，保证常驻
cd "$(dirname "$0")"
PORT=8866
PY="C:/Users/hu_ji/.workbuddy/binaries/python/versions/3.13.12/python.exe"

# 释放被占用的端口：若 8866 已被某进程监听（多为旧实例冻结未退出），先 taskkill 释放，
# 避免新实例 bind 失败陷入"启动即崩溃"循环。这是"数据冻结不再复发"的第二道保险。
cleanup_port() {
  pid=$(netstat -ano 2>/dev/null | grep -E ":$PORT.*LISTEN" | awk '{print $5}' | head -1)
  if [ -n "$pid" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') 释放占用端口 $PORT 的进程 $pid" >> server.log
    taskkill //F //PID "$pid" >/dev/null 2>&1
    sleep 1
  fi
}

echo $$ > daemon.pid
while true; do
  cleanup_port
  echo "$(date '+%Y-%m-%d %H:%M:%S') 启动 server.py" >> server.log
  "$PY" server.py >> server.log 2>&1 &
  SRV=$!
  echo $SRV > server.pid
  wait $SRV
  echo "$(date '+%Y-%m-%d %H:%M:%S') server.py 异常退出，2秒后自动重启" >> server.log
  sleep 2
done
