#!/bin/ksh
TARGET_USER_HOST=stu@nuc.home

ssh ${TARGET_USER_HOST} << !EOF
mkdir -p /AppData/BinNotifications/Credentials
!EOF

scp docker-compose.yml Dockerfile \
    GetBinCollections.py .env bincollections.env \
    requirements.txt \
        ${TARGET_USER_HOST}:/AppData/BinNotifications/
scp Credentials/* ${TARGET_USER_HOST}:/AppData/BinNotifications/Credentials


