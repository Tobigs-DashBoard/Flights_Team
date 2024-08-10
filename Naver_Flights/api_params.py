import requests
from datetime import datetime, timezone
import urllib.parse
'''api 요청 페이로드 형식'''
def payload_form(first, departure, arrival, date, galileo_key="", travel_biz_key=""):
    if first:
        galileo_flag=True
        galileo_key=""
        travel_biz_flag=False
        travel_biz_key=""
    else:
        galileo_key=galileo_key
        galileo_flag=galileo_key!=""
        travel_biz_key=travel_biz_key
        travel_biz_flag=travel_biz_key!=""

    payload={
        "operationName": "getInternationalList",
        "variables": {
            "adult": 1,
            "child": 0,
            "fareType": "Y",
            "galileoFlag": galileo_flag,
            "galileoKey": galileo_key, # 인증키
            "infant": 0,
            "isDirect": False, # 직항 여부
            "itinerary": [
                {
                    "departureAirport": departure,
                    "arrivalAirport": arrival,
                    "departureDate": date
                }
            ],
            "stayLength": "", # 편도
            "travelBizKey": travel_biz_key,
            "travelBizFlag": travel_biz_flag,
            "where": "pc",
            "trip": "OW",
        },
        "query": """
        query getInternationalList($trip: InternationalList_TripType!, $itinerary: [InternationalList_itinerary]!, $adult: Int = 1, $child: Int = 0, $infant: Int = 0, $fareType: InternationalList_CabinClass!, $where: InternationalList_DeviceType = pc, $isDirect: Boolean = false, $stayLength: String, $galileoKey: String, $galileoFlag: Boolean = true, $travelBizKey: String, $travelBizFlag: Boolean = true) {
          internationalList(
            input: {trip: $trip, itinerary: $itinerary, person: {adult: $adult, child: $child, infant: $infant}, fareType: $fareType, where: $where, isDirect: $isDirect, stayLength: $stayLength, galileoKey: $galileoKey, galileoFlag: $galileoFlag, travelBizKey: $travelBizKey, travelBizFlag: $travelBizFlag}
          ) {
            galileoKey
            galileoFlag
            travelBizKey
            travelBizFlag
            totalResCnt
            resCnt
            results {
              airlines
              airports
              fareTypes
              schedules
              fares
              errors
            }
          }
        }
        """
    }
    return payload

def return_header(departure, arrival, date):
    headers = {
        "authority": "airline-api.naver.com",
        "method": "POST",
        "path": "/graphql",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://flight.naver.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": f"https://flight.naver.com/flights/international/{departure}-{arrival}-{date}?adult=1&isDirect=true&fareType=Y",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        # "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    return headers

'''네이버 API 서버에 request를 보냄'''
def send_request(payload, headers):
    url = "https://airline-api.naver.com/graphql"
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("API 요청 오류", e)
        exit()

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
    return date, hour, minute, timestamp

def decode_url_text(text):
    return urllib.parse.unquote(text)