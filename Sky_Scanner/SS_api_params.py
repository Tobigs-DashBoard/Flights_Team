import requests
import json
from datetime import datetime, timedelta
import os

def return_header_payload(origin_entity_id, destination_entity_id, date, adults, cabin_class):
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
        "childAges": [], # 어린이 나이를 입력하면 성인 + 어린이 항공권 정보가 나옴 (가격은 합쳐져서 나옴)
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