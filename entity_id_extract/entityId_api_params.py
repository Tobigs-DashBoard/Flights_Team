import requests
import json
from datetime import datetime, timedelta
import os
import time

def return_header_payload(destination, date):
    headers = {
        "authority": "www.skyscanner.co.kr",
        "accept": "application/json",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "origin": "https://www.skyscanner.co.kr",
        "referer": f"https://www.skyscanner.co.kr/transport/flights/sela/{destination.lower()}/{date}/?adultsv2=1&cabinclass=economy&childrenv2=&ref=home&rtn=0&preferdirects=False&outboundaltsenabled=False&inboundaltsenabled=False",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        # "x-skyscanner-market":"KR",
        # "x-skyscanner-channelid":"website",
        # "x-skyscanner-locale":"ko-KR",
        # "x-skyscanner-currency":"KRW",
        # "x-skyscanner-traveller-context": "5c2f44a8-c89d-4aad-a21c-22752da99943",
        # "x-skyscanner-trustedfunnelid":"639fcee5-7975-48b1-aa6e-ddd05fab2afd",
        "x-skyscanner-viewid": "639fcee5-7975-48b1-aa6e-ddd05fab2afd",
        }
    
    payload = {
            "id_placements": {
                "adslot-2a788e9a": "desktop.flights.dayview/leaderboard"
            },
            "targeting": {
                "culture_settings": {
                "country": "KR",
                "currency": "KRW",
                "locale": "ko-KR"
                },
                "os": "mac_os",
                "cabin_class": "ECONOMY",
                "destination": {
                "airport": {
                    "location_attribute": {
                    "location_attribute_encoding": "IATA",
                    "location_id": f"{destination}",
                    "location_name": ""
                    }
                },
                "city": {
                    "location_attribute": {
                    "location_attribute_encoding": "IATA",
                    "location_id": "",
                    "location_name": ""
                    }
                },
                "country": {
                    "location_attribute": {
                    "location_attribute_encoding": "IATA",
                    "location_id": "",
                    "location_name": ""
                    }
                }
                },
                "duration": 0,
                "itinerary_type": "ONE_WAY",
                "origin": {
                "city": {
                    "location_attribute": {
                    "location_attribute_encoding": "IATA",
                    "location_id": "SELA",
                    "location_name": ""
                    }
                },
                "country": {
                    "location_attribute": {
                    "location_attribute_encoding": "IATA",
                    "location_id": "KR",
                    "location_name": "KR"
                    }
                }
                },
                "page_type": "flights.dayview",
                "passengers": {
                "adult_count": 1,
                "child_count": 0,
                "infant_count": 0
                },
                "search_start_timestamp": {
                "unix_time_millis": 0,
                "date_time_kind": "DAY",
                "timezone_offset_mins": 0,
                "daylight_savings_offset_mins": 0
                }
            },
            "user_features": {
                "request_id": "55c6a336-79dd-49bd-95b3-2ebc98bfde37",
                "is_new_user": False,
                "authentication_status": "UNAUTHENTICATED",
                "client": {
                "browser_name": "Chrome",
                "is_browser": True,
                "is_mobilephone": False,
                "is_tablet": False,
                "display_height": 878,
                "display_width": 1352,
                "referrer_url": "www.skyscanner.co.kr"
                },
                "ga_cid": None,
                "is_optedin_for_personalised": True,
                "platform": "DESKTOP_WEB",
                "utid": "5c2f44a8-c89d-4aad-a21c-22752da99943"
            }
            }
    return headers, payload

'''sky scanner API 서버에 request를 보냄'''
def send_request(payload, headers):
    time.sleep(10)
    url = "https://www.skyscanner.co.kr/g/ars/public/api/v2/request"
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("API 요청 오류", e)
