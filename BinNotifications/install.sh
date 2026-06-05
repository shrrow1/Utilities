#!/bin/ksh
TARGET_USER_HOST=stu@nuc.home

ssh ${TARGET_USER_HOST} << !EOF
mkdir -p /AppData/BinNotifications/Credentials
mkdir -p /AppData/BinNotifications/Logs
mkdir -p /AppData/shared_logger
!EOF

scp docker-compose.yml Dockerfile \
    GetBinCollections.py .env bincollections.env \
    requirements.txt \
        ${TARGET_USER_HOST}:/AppData/BinNotifications/
scp Credentials/* ${TARGET_USER_HOST}:/AppData/BinNotifications/Credentials

scp -r ../shared_logger/*  ${TARGET_USER_HOST}:/AppData/shared_logger


