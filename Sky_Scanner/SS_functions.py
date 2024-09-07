from datetime import datetime
from pytz import timezone as py_timezone
import requests
from datetime import datetime, timezone
import json
import logging
import os
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

'''sky scanner API 서버에 request를 보냄'''
def send_request(payload, headers):
    url = "https://www.skyscanner.co.kr/g/radar/api/v2/web-unified-search/"
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("API 요청 오류", e)
        exit()



# 공항별 시간대
def get_airport_timezone(airport_code):
    return py_timezone(airport_map[airport_code]['time_zone'])

# UTC 시간대로 변환
def convert_to_utc(timestamp_str, airport_code):
    local_tz = get_airport_timezone(airport_code)
    local_time = local_tz.localize(datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S"))
    utc_time = local_time.astimezone(py_timezone('UTC'))
    return utc_time


'''디버깅용 파일 저장'''
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def parse_timestamp(timestamp_str):
    return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")

def format_timestamp(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def calculate_connect_time(arrival_time, next_departure_time):
    arrival = parse_timestamp(arrival_time)
    departure = parse_timestamp(next_departure_time)
    return int((departure - arrival).total_seconds() / 60)