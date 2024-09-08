import requests
import json
from datetime import datetime, timedelta
import os
from SS_functions import airport_map

pxhd = "ZkRkD20fcA5H84yPv8Psvh3tc54iYneuiQAeWHVwtskQ1RT8ytG6Muc2tgeI0PLyBV9Xr/94aN0-RLjmGcbNcQ==:fPmY7xnQT7Ou4IXW/OsopoJOYlgqtnlCWtbtmTQqQs4/UGmXac50dqjHT/WqmvWKAMQX19qVcGDeg/dt/QllB6sMviZ4thHMVdvUy/7P-bU="

traveller_context = ""

secure_anon_token = ""

secure_anon_csrf_token = ""

ssab = ""

ssaboverrides = ""

abgroup = ""

ssculture = ""

experiment_allocation_id = ""

secure_ska = ""

device_guid = ""

gcl_gs = ""

gcl_au = ""

pxcts = ""

pxvid = ""

QSI_S_ZN_0VDsL2Wl8ZAlxlA = ""

scanner = ""

preferences = ""

gid = ""

gat = "1"

gsas = ""

QSI_S_ZN_8fcHUNchqVNRM4S = ""

cto_bundle = ""

gads = ""

gpi = ""

eoi = ""

uetsid = ""

uetvid = ""

clck = ""

ga_GJJLCKYWVW = ""

clsk = ""

gcl_aw = ""

gcl_dc = ""

ga = ""

ga_XEEM7L2YCB = ""

def return_header_payload(origin, destination, date, adults, cabin_class):
    origin_entity_id = airport_map[origin]['entity_id']
    destination_entity_id = airport_map[destination]['entity_id']
    date_input=date.replace('-','')
    headers = {
        "authority": "www.skyscanner.co.kr",
        "accept": "application/json",
        "method":"post",
        "scheme": "https",
        "path": "/g/radar/api/v2/web-unified-search/",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "origin": "https://www.skyscanner.co.kr",
        "referer": f"https://www.skyscanner.co.kr/transport/flights/{origin.lower()}/{destination.lower()}/{date_input[2:]}/?adultsv2={adults}&cabinclass={cabin_class.lower()}&childrenv2=&ref=home&rtn=0&preferdirects=false&outboundaltsenabled=false&inboundaltsenabled=false",
        "cookie" : f"_pxhd={pxhd}; traveller_context={traveller_context}; __Secure-anon_token={secure_anon_token}; __Secure-anon_csrf_token={secure_anon_csrf_token}; ssab={ssab}; ssaboverrides={ssaboverrides}; abgroup={abgroup}; ssculture={ssculture}; experiment_allocation_id={experiment_allocation_id}; __Secure-ska={secure_ska}; device_guid={device_guid}; _gcl_gs={gcl_gs}; _gcl_au={gcl_au}; pxcts={pxcts}; _pxvid={pxvid}; QSI_S_ZN_0VDsL2Wl8ZAlxlA={QSI_S_ZN_0VDsL2Wl8ZAlxlA}; scanner={scanner}; preferences={preferences}; _gid={gid}; _gat={gat}; __gsas={gsas}; QSI_S_ZN_8fcHUNchqVNRM4S={QSI_S_ZN_8fcHUNchqVNRM4S}; cto_bundle={cto_bundle}; __gads={gads}; __gpi={gpi}; __eoi={eoi}; _uetsid={uetsid}; _uetvid={uetvid}; _clck={clck}; _ga_GJJLCKYWVW={ga_GJJLCKYWVW}; _clsk={clsk}; _gcl_aw={gcl_aw}; _gcl_dc={gcl_dc}; _ga={ga}; _ga_XEEM7L2YCB={ga_XEEM7L2YCB}",
        "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "x-skyscanner-market":"KR",
        "x-skyscanner-channelid":"website",
        "x-skyscanner-locale":"ko-KR",
        "x-skyscanner-currency":"KRW",
        "x-skyscanner-traveller-context": "04db2757-0cb0-47a2-94f6-64ddfea48eeb",
        "x-skyscanner-trustedfunnelid":"aac317f2-d0f8-4d16-8b1f-8dc670f2739b",
        "x-skyscanner-viewid": "aac317f2-d0f8-4d16-8b1f-8dc670f2739b",
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