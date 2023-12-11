#!/bin/bash
cd /data/judaicalink-labs/labs
source /data/judaicalink-labs/venv/bin/activate
git fetch 
msg=`git pull`
#if [[ "$msg" == "Already up to date." ]]; then
#	echo "Nichts zu tun, Ende."
#	exit 0
#fi
sudo systemctl stop labs.service
pip3 install -r /data/judaicalink-labs/requirements.txt
python manage.py migrate --no-input
python manage.py collectstatic --no-input
sudo systemctl start labs.service
