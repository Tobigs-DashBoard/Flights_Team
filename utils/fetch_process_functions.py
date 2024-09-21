import requests
from datetime import datetime, timezone
import urllib.parse
import os
from pytz import timezone as py_timezone
from NF_global_objects import get_logger, get_airport_map
logger=get_logger()
airport_map=get_airport_map()

'''네이버 API 서버에 request를 보냄'''
def send_request(payload, headers):
    url = "https://airline-api.naver.com/graphql"
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.info(f"API 요청 오류 {e}")
        print(f"API 요청 오류 {e}")
        return False

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


'''디버깅용 파일 저장'''
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)