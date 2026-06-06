#!/bin/bash
HOST=stu@nuc.home
TARGET_DIR=/AppData/Kuma

ssh ${HOST} << !EOF
mkdir -p ${TARGET_DIR}/data
!EOF

scp docker-compose.yml ${HOST}:${TARGET_DIR}
