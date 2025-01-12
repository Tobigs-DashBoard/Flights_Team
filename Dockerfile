# 기본 이미지
FROM python:3.11

# 컨테이너 내부 작업 경로
WORKDIR /app

# 시스템 패키지 업데이트 및 vim 설치
RUN apt-get update && apt-get install -y \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 라이브러리 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 로그 디렉토리 생성
RUN mkdir -p /app/logs

# 프로젝트 복제
COPY . /app/

# 컨테이너 생성 시 명령어
# CMD ["sh", "-c", "while true; do sleep 3600; done"]
CMD ["python", "NF_scheduler_with_proxy.py"]