#!/bin/sh

# 환경 변수 설정 (필요에 따라 수정)
LOG_DIR="/home/gunu/logs"
IMAGE_NAME="vimcat23/naver_flights:latest"
CONTAINER_NAME="naver_flights"
TARGET_REGION="대한민국"  # 사용할 지역
DB_HOST="10.165.112.3"
DB_NAME="naver_db"
DB_USER="gunu"
DB_PASSWORD="rjsdn5994!"

# 현재 날짜를 YYYYMMDD 형식으로 가져오기
CURRENT_DATE=$(date +%Y%m%d)

# Docker 실행 명령어
docker run --rm \
  --name $CONTAINER_NAME -d \
  -v $LOG_DIR:/app/logs \
  -v /home/gunu/total_proxy_map.json:/app/total_proxy_map.json \
  -e LOG_PATH=/app/logs/naver_flights_$CURRENT_DATE.log \
  -e PROXY_PATH=/app/total_proxy_map.json \
  -e TARGET_REGION="$TARGET_REGION" \
  -e DB_HOST="$DB_HOST" \
  -e DB_NAME="$DB_NAME" \
  -e DB_USER="$DB_USER" \
  -e DB_PASSWORD="$DB_PASSWORD" \
  $IMAGE_NAME

echo "Docker container '$CONTAINER_NAME' started with TARGET_REGION: $TARGET_REGION"