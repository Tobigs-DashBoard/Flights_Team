import requests
from datetime import datetime, timezone
import urllib.parse
import os
import json
import logging
from pytz import timezone as py_timezone

def setup_logger():
    logging.basicConfig(
        filename='crawling_log.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # 루트 로거 반환
    return logging.getLogger()

logger=setup_logger()

def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)
    
airport_map = read_json_file('maps/airport_map.json') # 공항 코드 <-> 이름, 지역 맵
request_airport_map = read_json_file('maps/request_airport_map.json') # 네이버 항공권 검색 공항 코드 맵

'''네이버 API 서버에 request를 보냄'''
def send_request(payload, headers):
    url = "https://airline-api.naver.com/graphql"
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.info(f"API 요청 오류 {e}")

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

def get_airport_timezone(airport_code):
    return py_timezone(airport_map[airport_code]['time_zone'])

def convert_to_timestamp(time_str, airport_code):
    time_zone = get_airport_timezone(airport_code)
    date = time_str[:-4]
    hour = time_str[-4:-2]
    minute = time_str[-2:]
    datetime_str = f"{date} {hour}:{minute}"
    datetime_obj = datetime.strptime(datetime_str, "%Y%m%d %H:%M")
    localized_time = time_zone.localize(datetime_obj)
    return localized_time

def convert_to_utc(localized_time):
    return localized_time.astimezone(py_timezone('UTC')).isoformat()