# 기본 이미지
FROM python:3.8-slim

# 컨테이너 내부 작업 경로
WORKDIR /app

# 라이브러리 설치
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 컨테이너 내부 vim 추가 설치
RUN apt-get update && apt-get install -y vim

# 프로젝트 복제
COPY . /app/

# 컨테이너 생성 시 명령어
CMD ["python", "NF_scheduler.py"]