import json
import time
import urllib.parse
from datetime import datetime, timezone
from api_parmas import *

def crawl_naver_flights(departure, arrival, date):
    # 요청 헤더
    headers = return_header(departure, arrival, date)
    '''첫번재 요청'''
    # 첫번째 api 파싱용 페이로드
    payload1 = payload_form(first=True, departure=departure, arrival=arrival, date=date)
    # 첫번재 파싱 결과
    response_data1 = send_request(payload1, headers)
    if not response_data1:
        return []
    
    # with open('test_1.json', 'w', encoding='utf-8-sig') as file:
    #     json.dump(response_data1, file, ensure_ascii=False, indent=4)
    # 첫번째 파싱 결과에서 두번째 파싱 요청에 필요한 파라미터 추출
    international_list = response_data1.get("data", {}).get("internationalList", {})
    galileo_key = international_list.get("galileoKey")
    travel_biz_key = international_list.get("travelBizKey")

    print("galileo key: ", galileo_key)
    print("travel key: ", travel_biz_key)
    
    # 5초 대기
    time.sleep(5)

    '''두번째 요청'''
    payload2 = payload_form(first=False, departure=departure, arrival=arrival, date=date, galileo_key=galileo_key, travel_biz_key=travel_biz_key)
    
    response_data2 = send_request(payload2, headers)
    if not response_data2:
        return []
    # with open('test_2.json', 'w', encoding='utf-8-sig') as file:
    #     json.dump(response_data2, file, ensure_ascii=False, indent=4)

    international_list = response_data2.get("data", {}).get("internationalList", {})
    results = international_list.get("results", {})
    
    airline_map = results.get('airlines', {}) # 항공사 코드와 항공사 이름이 매칭된 딕셔너리
    
    airport_map = results.get('airports', {}) # 공항 코드와 공항 이름이 매칭된 딕셔너리
    schedules = results.get("schedules", []) # 항공권 스케줄
    fares=results.get("fares", []) # 항공권 id 별 운임 정보
    fare_types=results.get("fareTypes", [])
    '''비행 정보 저장'''
    # 비행 정보를 저장할 리스트
    all_flights = []
    for schedule in schedules[0].values():
        details = schedule['detail']
        air_id=schedule['id']
        air_id_list=air_id.split('+')
        
        flight_group = {
            "id": air_id,
            "is_layover": "+" in schedule['id'] and len(details) > 1,  # 경유 여부 확인
            "flights": []
        }

        # 경유, 직항 모두 출발지와 도착지가 입력값과 다른 경우 스킵
        if len(details)>1:    
            if details[0]['sa']!=departure and details[len(details)-1] != arrival:
                continue
        else:
            if details[0]['sa']!=departure and details[0] != arrival:
                continue
        for index, detail in enumerate(details):
            depart_airport = detail['sa']  # 출발 공항
            arrival_airport = detail['ea']  # 도착 공항
            
            depart_airport = urllib.parse.unquote(airport_map.get(depart_airport, "Unknown"))  # url 변환 값 역변환
            arrival_airport = urllib.parse.unquote(airport_map.get(arrival_airport, "Unknown"))  # url 변환 값 역변환
            
            # 출발 시각 타임 스탬프 변환
            depart_date, depart_hour, depart_minute, depart_timestamp = return_time_stamp(detail['sdt'])
            # 도착 시각 타임 스탬프 변환
            arrival_date, arrival_hour, arrival_minute, arrival_timestamp = return_time_stamp(detail['edt'])
            
            flight_info = {
                "air_id": air_id_list[index],  # 항공편 ID
                "airline": airline_map.get(detail['av'], "Unknown"),  # 항공사
                "depart_airport": depart_airport,
                "arrival_airport": arrival_airport,
                "depart_date": f"{depart_date[:4]}-{depart_date[4:6]}-{depart_date[6:]}",
                "depart_time": f"{detail['sdt'][-4:-2]}:{detail['sdt'][-2:]}",
                "arrival_date": f"{arrival_date[:4]}-{arrival_date[4:6]}-{arrival_date[6:]}",
                "arrival_time": f"{detail['edt'][-4:-2]}:{detail['edt'][-2:]}",
                "journey_time": f"{detail['jt'][:2]}시간 {detail['jt'][2:]}분",  # 소요 시간
                "depart_timestamp": timestamp_to_iso8601(depart_timestamp),
                "arrival_timestamp": timestamp_to_iso8601(arrival_timestamp),
                "connect_time": detail['ct']  # 환승 시간
            }
            
            flight_group["flights"].append(flight_info)

        
        if flight_group["flights"]:
            all_flights.append(flight_group)

    # JSON 파일로 저장
    with open('flight_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_flights, f, ensure_ascii=False, indent=4)
    print("항공편 정보가 'flights_data.json' 파일로 저장되었습니다.")

    '''운임 정보 저장'''
    total_fare_info = []
    # 운임 정보 처리
    for key, values in fares.items():
        air_id_info = {"air_id": key, "options": []}
        
        for option, fare_list in values['fare'].items():
            fare_option_info = {"option": decode_url_text(fare_types[option]), "purchases": []}
            
            for i in fare_list:
                purchase_info = {}
                try:
                    adult = i['Adult']
                    base_fare = int(adult['Fare'])
                    naver_fare = int(adult['NaverFare'])
                    tax = int(adult['Tax'])
                    Qcharge = int(adult['QCharge'])
                    adult_fare = base_fare + naver_fare + tax + Qcharge
                    
                    reserve = i['ReserveParameter']['#cdata-section']
                    
                    purchase_info['purchase_url'] = reserve
                    purchase_info['total_fare'] = adult_fare
                    purchase_info['base_fare'] = base_fare
                    purchase_info['naver_fare'] = naver_fare
                    purchase_info['tax'] = tax
                    purchase_info['Qcharge'] = Qcharge
                    
                    fare_option_info["purchases"].append(purchase_info)
                except Exception as e:
                    print("오류", e)
                    continue
            
            air_id_info["options"].append(fare_option_info)
        
        total_fare_info.append(air_id_info)

    # JSON으로 저장
    with open('total_fare_info.json', 'w', encoding='utf-8') as f:
        json.dump(total_fare_info, f, ensure_ascii=False, indent=4)

    print('운임 정보 파일이 저장되었습니다.')

    return 0
# 실행
if __name__ == "__main__":
    departure = "ICN"
    arrival = "KIX"
    date = "20240818"  # 날짜 변경
    df_flights = crawl_naver_flights(departure, arrival, date)