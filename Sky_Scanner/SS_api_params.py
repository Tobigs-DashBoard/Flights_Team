import requests
import json
from datetime import datetime, timedelta
import os

def return_header_payload(origin_entity_id, destination_entity_id, date, adults, cabin_class):
    # origin_entity_id="27538638"
    headers = {
        "authority": "www.skyscanner.co.kr",
        "accept": "application/json",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "origin": "https://www.skyscanner.co.kr",
        "referer": f"https://www.skyscanner.co.kr/transport/flights/{origin_entity_id}/{destination_entity_id}/{date}/?adultsv2={adults}&cabinclass={cabin_class.lower()}&childrenv2=&ref=home&rtn=0&preferdirects=false&outboundaltsenabled=false&inboundaltsenabled=false",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "x-skyscanner-market":"KR",
        "x-skyscanner-channelid":"website",
        "x-skyscanner-locale":"ko-KR",
        "x-skyscanner-currency":"KRW",
        "x-skyscanner-traveller-context": "5c2f44a8-c89d-4aad-a21c-22752da99943",
        "x-skyscanner-trustedfunnelid":"639fcee5-7975-48b1-aa6e-ddd05fab2afd",
        "x-skyscanner-viewid": "639fcee5-7975-48b1-aa6e-ddd05fab2afd",
        }
    
    payload = {
        "adults": int(adults),
        "cabinClass": cabin_class,
        "childAges": [],
        "legs": [
            {
                "legOrigin": {
                    "@type": "entity",
                    "entityId": origin_entity_id
                },
                "legDestination": {
                    "@type": "entity",
                    "entityId": destination_entity_id
                },
                "dates": {
                    "@type": "date",
                    "year": str(date[:4]),
                    "month": str(date[5:7]),
                    "day": str(date[8:])
                }
            }
        ]
    }
    return headers, payload

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


def parse_timestamp(timestamp_str):
    return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")

def format_timestamp(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def calculate_connect_time(arrival_time, next_departure_time):
    arrival = parse_timestamp(arrival_time)
    departure = parse_timestamp(next_departure_time)
    return int((departure - arrival).total_seconds() / 60)

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)