#!/bin/ksh
HOST=stu@192.168.1.5

ssh ${HOST} << !EOF
mkdir -p /AppData/BinNotifications/Credentials
!EOF

scp docker-compose.yml Dockerfile GetBinNotifications.py .env bincollections.env \
        ${HOST}:/AppData/BinNotifications/
scp Credentials/* ${HOST}:/AppData/BinNotifications/Credentials
