import requests
from datetime import datetime, timezone
import urllib.parse
import os
import json
import time

def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
airport_region_map = read_json_file('Naver_Flights/maps/airport_region_map.json') # 공항 코드 <-> 이름, 지역 맵
request_airport_map = read_json_file('Naver_Flights/maps/request_airport_map.json') # 네이버 항공권 검색 공항 코드 맵

'''네이버 API 서버에 request를 보냄'''
def send_request(payload, headers):
    url = "https://airline-api.naver.com/graphql"
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("API 요청 오류", e)

'''보기 쉽게 타임스템프 형식 변환'''
def timestamp_to_iso8601(timestamp):
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def return_time_stamp(time):
    date = time[:-4]
    hour = time[-4:-2]
    minute = time[-2:]
    datetime_str = f"{date} {hour}:{minute}"
    datetime_form = datetime.strptime(datetime_str, "%Y%m%d %H:%M").replace(tzinfo=timezone.utc)
    timestamp = datetime_form.timestamp()
    return timestamp

def decode_url_text(text):
    return urllib.parse.unquote(text)

'''디버깅용 파일 저장'''
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)