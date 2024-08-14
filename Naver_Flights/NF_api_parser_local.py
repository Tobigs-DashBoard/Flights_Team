import json
import time
import urllib.parse
import os
from datetime import datetime, timezone, date, timedelta
from NF_api_params import *
from multiprocessing import Process, Queue

'''항공 코드와 국가를 1대 1 매칭한 딕셔너리'''
with open('Naver_Flights/airport_region_map.json', 'r', encoding='utf-8') as f:
    airport_region_map=json.load(f)


'''검색 용 공항 코드'''
with open('Naver_Flights/request_airport_map.json', 'r', encoding='utf-8') as f:
    request_airport_map=json.load(f)

def save_flight_info(schedules, airline_map, airport_map, departure, arrival, date,arrival_target, queue):
    '''비행 정보 저장'''
    # 비행 정보를 저장할 리스트
    all_flights = []
    for schedule in schedules[0].values():
        details = schedule['detail']
        air_id = schedule['id']
        air_id_list = air_id.split('+')
        
        flight_group = {
            "air_id": air_id,
            "is_layover": "+" in schedule['id'] and len(details) > 1,  # 경유 여부 확인
            "flights": []
        }

        # 경유, 직항 모두 출발지와 도착지가 입력값과 다른 경우 스킵
        if len(details) > 1:
            if departure == 'SEL': # 서울 -> 한국 전체 공항 ok
                if details[0]['sa'] not in ["CJU","GMP","PUS","CJJ","KWJ","TAE","RSU","USN","HIN","KPO","WJU","KUV","MWX","ICN"] and details[len(details)-1]['ea'] != arrival:
                    continue
            
            elif details[0]['sa'] != departure and details[len(details)-1]['ea'] != arrival:
                continue
        else:
            if details[0]['sa'] != departure and details[0]['ea'] != arrival:
                continue
        for index, detail in enumerate(details):
            depart_airport = detail['sa']  # 출발 공항
            depart_region = airport_region_map[detail['sa']]
            arrival_airport = detail['ea']  # 도착 공항
            arrival_region = airport_region_map[detail['ea']]
            
            depart_airport = urllib.parse.unquote(airport_map.get(depart_airport, "Unknown"))  # url 변환 값 역변환
            arrival_airport = urllib.parse.unquote(airport_map.get(arrival_airport, "Unknown"))  # url 변환 값 역변환
            
            # 출발 시각 타임 스탬프 변환
            depart_date, depart_hour, depart_minute, depart_timestamp = return_time_stamp(detail['sdt'])
            # 도착 시각 타임 스탬프 변환
            arrival_date, arrival_hour, arrival_minute, arrival_timestamp = return_time_stamp(detail['edt'])
            
            flight_info = {
                f"air_id_{index}": air_id_list[index],  # 항공편 ID
                "airline": airline_map.get(detail['av']),  # 항공사
                "depart_region": depart_region,
                "depart_airport": depart_airport,
                "arrival_region": arrival_region,
                "arrival_airport": arrival_airport,
                # "depart_date": f"{depart_date[:4]}-{depart_date[4:6]}-{depart_date[6:]}",
                # "depart_time": f"{detail['sdt'][-4:-2]}:{detail['sdt'][-2:]}",
                # "arrival_date": f"{arrival_date[:4]}-{arrival_date[4:6]}-{arrival_date[6:]}",
                # "arrival_time": f"{detail['edt'][-4:-2]}:{detail['edt'][-2:]}",
                # "journey_time": f"{detail['jt'][:2]}시간 {detail['jt'][2:]}분",  # 소요 시간
                "journey_time": int(detail['jt'][:2])*60 + int(detail['jt'][2:]),
                "connect_time": int(detail['ct'][:2])*60 + int(detail['ct'][2:]),
                # "connect_time": detail['ct']  # 환승 시간
                "depart_timestamp": timestamp_to_iso8601(depart_timestamp),
                "arrival_timestamp": timestamp_to_iso8601(arrival_timestamp),
            }
            
            flight_group["flights"].append(flight_info)

        
        if flight_group["flights"]:
            all_flights.append(flight_group)

    # JSON 파일로 저장
    file_path = f'Naver_Results/{arrival_target}/{arrival}/flight_info/{departure}_{arrival}_{date}.json'
    ensure_dir(file_path)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_flights, f, ensure_ascii=False, indent=4)
    print(f"항공편 정보가 '{file_path}' 파일로 저장되었습니다.")
    queue.put("Flight info saved")

def save_fare_info(fares, fare_types, departure, arrival, date, arrival_target, queue):
    '''운임 정보 저장'''
    total_fare_info = []
    # 운임 정보 처리
    for key, values in fares.items():
        air_id_info = {"air_id": key, "options": []}
        
        for option, fare_list in values['fare'].items():
            # if option != "A01": # 데이터 용량 확보 차원에서 우선 성인/일반 요금만 수집
            #     continue
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
    file_path = f'Naver_Results/{arrival_target}/{arrival}/fare_info/{departure}_{arrival}_{date}.json'
    ensure_dir(file_path)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(total_fare_info, f, ensure_ascii=False, indent=4)
    print(f"운임 정보가 '{file_path}' 파일로 저장되었습니다.")
    queue.put("Fare info saved")

def fetch_naver_flights_date(departure, arrival, date, arrival_target):
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
    with open('test_2.json', 'w', encoding='utf-8-sig') as file:
        json.dump(response_data2, file, ensure_ascii=False, indent=4)

    international_list = response_data2.get("data", {}).get("internationalList", {})
    results = international_list.get("results", {})
    
    airline_map = results.get('airlines', {}) # 항공사 코드와 항공사 이름이 매칭된 딕셔너리
    
    airport_map = results.get('airports', {}) # 공항 코드와 공항 이름이 매칭된 딕셔너리
    schedules = results.get("schedules", []) # 항공권 스케줄
    fares = results.get("fares", []) # 항공권 id 별 운임 정보
    fare_types = results.get("fareTypes", [])
    if len(schedules)==0:
        return 0

    # 멀티프로세싱 설정
    queue = Queue()
    p1 = Process(target=save_flight_info, args=(schedules, airline_map, airport_map, departure, arrival, date, arrival_target,queue)) # 항공권 정보 프로세스
    p2 = Process(target=save_fare_info, args=(fares, fare_types, departure, arrival, date,arrival_target,queue)) # 운임 정보 프로세스

    # 프로세스 시작
    p1.start()
    p2.start()
    
    # 프로세스 종료 대기
    p1.join()
    p2.join()

    return 0


# 오늘 기준 30일 뒤까지 크롤링
if __name__ == "__main__":
    departure = "SEL"
    arrival_list=["대한민국", "일본", "동남아", "중국", "유럽", "미주", "대양주", "남미", "아시아", "중동", "아프리카"]
    today = date.today()
    '''우선 일본 항공을 목적으로 디버깅'''
    for arrival_target in arrival_list:
        for airport in request_airport_map[arrival_target]:
            arrival = airport['IATA']
            if arrival=="SEL":
                continue
            '''오늘 날짜 기준 3일 뒤의 데이터까지 수집'''
            for i in range(1, 4):
                target_date = today + timedelta(days=i)
                formatted_date = target_date.strftime('%Y%m%d')
                fetch_naver_flights_date(departure, arrival, formatted_date, arrival_target)