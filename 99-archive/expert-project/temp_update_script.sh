#!/bin/bash

echo "[$(date)] Обновление начато" >> /root/update.log

docker login -u argonpower -p "dckr_pat_e334NSYChZBY9OcSCVnCHpyhUqQ" >> /root/update.log 2>&1
docker pull argonpower/ad-content-generator:latest >> /root/update.log 2>&1
docker stop myapp >> /root/update.log 2>&1
docker rm myapp >> /root/update.log 2>&1
docker run -d \
  --network host \
  --restart unless-stopped \
  --name myapp \
  argonpower/ad-content-generator:latest >> /root/update.log 2>&1

echo "[$(date)] Обновление завершено" >> /root/update.log
