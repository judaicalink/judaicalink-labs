#!/bin/bash
start() {
	cd /data/judaicalink-labs/labs
	source /data/judaicalink-labs/venv/bin/activate
	nohup daphne -p 8000 labs.asgi:application |& tee -a /var/log/daphne/daphne.log &
	 _pid=$!
	 echo "$_pid" > /var/run/judaicalink-labs.pid
}
stop() {
	_pid=`cat /var/run/judaicalink-labs.pid`
	pkill -3 $_pid
	rm /var/run/judaicalink-labs.pid
}
case $1 in
	  start|stop) "$1" ;;
  esac

