#!/bin/sh

# 환경 변수 설정 (필요에 따라 수정)
LOG_DIR="/home/gunu/logs"
IMAGE_NAME="gunu1003/naver_flights:latest"
CONTAINER_NAME="naver_flights"
TARGET_REGION="대한민국" #"대한민국", "일본", "동남아", "중국", "유럽", "미주", "대양주", "남미", "아시아", "중동", "아프리카"

# 현재 날짜를 YYYYMMDD 형식으로 가져오기
CURRENT_DATE=$(date +%Y%m%d)

# Docker 실행 명령어
docker run --rm -d \
  --name $CONTAINER_NAME \
  -v $LOG_DIR:/app/logs \
  -e LOG_PATH=/app/logs/naver_flights_$CURRENT_DATE.log \
  -e TARGET_REGION="$TARGET_REGION" \
  $IMAGE_NAME

echo "Docker container '$CONTAINER_NAME' started with TARGET_REGION: $TARGET_REGION"