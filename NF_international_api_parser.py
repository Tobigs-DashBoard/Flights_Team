# import json
import time
from utils.fetch_process_functions import convert_to_timestamp, convert_to_utc, decode_url_text
from NF_global_objects import get_batch_manager, get_today, get_airport_map

batch_manager=get_batch_manager()
today=get_today()
airport_map=get_airport_map()

def check_airport_info_exist(airport_code):
    if airport_code not in airport_map.keys():
        return False
    else:
        return True

def parse_fare_class(url):
    """Extract fare class from the booking URL."""
    import re
    try:
        match = re.search(r'FareRuleItnInfo=([^&]+)', url)
        if not match:
            return 'n'
        
        fare_info = match.group(1)
        parts = fare_info.split('/')
        if len(parts) >= 3:
            return parts[2]
        return 'n'
    except Exception:
        return 'n'

def save_flight_info(schedules, airline_map):
    '''비행 정보 저장'''
    skipped_air_id=set()
    for schedule in schedules[0].values():
        details = schedule['detail']
        total_journey_time = int(schedule['journeyTime'][0])*60 + int(schedule['journeyTime'][1])
        air_id = schedule['id']
        air_id_list = air_id.split('+')
        is_layover = "+" in schedule['id'] and len(details) > 1  # 경유 여부 확인

        '''편도 일 경우 -> 편도 항공권만 flights_info 테이블에 저장'''
        '''경유 일 경우 -> 전체 항공권 정보, 각각의 편도 항공권을 flights_info 테이블에 저장'''
        '''이때 경유 정보 (경유 항공권, 경유 시간)을 layover_info 테이블에 저장'''
        if is_layover:
            # 경유 전체 항공권 정보
            first_detail = details[0]
            last_detail = details[-1]
            layover_depart_airport = first_detail['sa']
            layover_arrival_airport = last_detail['ea']
            
            if not (check_airport_info_exist(layover_depart_airport) and check_airport_info_exist(layover_arrival_airport)):
                skipped_air_id.add(air_id)
                continue

            layover_depart_timestamp = convert_to_utc(convert_to_timestamp(first_detail['sdt'], first_detail['sa']))
            layover_arrival_timestamp = convert_to_utc(convert_to_timestamp(last_detail['edt'], last_detail['ea']))
            
            airline_list=[]
            for detail in details:
                airline_list.append(airline_map.get(detail['av']))
            if len(set(airline_list))==1: # 경유시 모든 항공사가 같으면 db에 넣고 아니면 안넣음 (join문으로 구간별 항공사를 알아낼 수 있음)
                airline=airline_list[0]
            else:
                airline=None


            batch_manager.flight_info_queue.add_to_queue(
                    air_id, airline,
                    layover_depart_airport, layover_depart_timestamp,
                    layover_arrival_airport, layover_arrival_timestamp,
                    total_journey_time,
                    is_layover
                )

            # 각각의 항공권 정보
            for index, detail in enumerate(details):
                depart_airport = detail['sa']
                arrival_airport = detail['ea'] 
                if not (check_airport_info_exist(depart_airport) and check_airport_info_exist(arrival_airport)): # 기본 공항외의 공항을 경유할 경우 처리하지 않음
                    skipped_air_id.add(air_id_list[index])
                    continue
                depart_timestamp = convert_to_utc(convert_to_timestamp(detail['sdt'], detail['sa']))
                arrival_timestamp = convert_to_utc(convert_to_timestamp(detail['edt'], detail['ea']))
                journey_time = int(detail['jt'][:2])*60 + int(detail['jt'][2:])
                connect_time=int(detail['ct'][:2])*60 + int(detail['ct'][2:])
                
                # flight_info 테이블에 삽입
                batch_manager.flight_info_queue.add_to_queue(
                    air_id_list[index], 
                    airline_map.get(detail['av']), 
                    depart_airport, depart_timestamp,
                    arrival_airport, arrival_timestamp,
                    journey_time,
                    False
                )
                
                # layover_info 테이블에 경유 항공권내의 편도 항공권 id, connect_time 정보 삽입
                batch_manager.layover_info_queue.add_to_queue(
                    air_id, air_id_list[index], index, connect_time
                )
            
        else:
            detail=details[0]
            depart_airport = detail['sa']
            arrival_airport = detail['ea']
            if not (check_airport_info_exist(depart_airport) and check_airport_info_exist(arrival_airport)): # 기본 공항외의 공항을 경유할 경우 처리하지 않음
                skipped_air_id.add(air_id)
                continue
            depart_timestamp = convert_to_utc(convert_to_timestamp(detail['sdt'], detail['sa'])) # UTC 기준 출발 시간
            arrival_timestamp = convert_to_utc(convert_to_timestamp(detail['edt'], detail['ea'])) # UTC 기준 도착 시간
            journey_time = int(detail['jt'][:2])*60 + int(detail['jt'][2:]) # 비행 시간
            
            batch_manager.flight_info_queue.add_to_queue(
                    air_id, airline_map.get(detail['av']), 
                    depart_airport, depart_timestamp,
                    arrival_airport, arrival_timestamp,
                    journey_time,
                    False
                )
            
    return skipped_air_id

def save_fare_info(fares, fare_types, seat_class, skipped_air_id):
    '''운임 정보 저장'''
    seat_class_map={'Y':'일반석',
                    'P': '이코노미',
                    'C': '비즈니스석',
                    'F': '일등석'}
    fetched_date=today.strftime('%Y%m%d')
    for key, values in fares.items():
        if key in skipped_air_id:
            continue
        for option, fare_list in values['fare'].items():
            option=decode_url_text(fare_types[option])
            if option !="성인/모든 결제수단": # 카드사 제휴는 제외함
                continue
            for fare in fare_list:
                try:
                    agt=fare['AgtCode']
                    adult = fare['Adult']
                    child= fare['Child']
                    infant=fare['Infant']
                    
                    adult_base_fare = int(adult['Fare'])
                    adult_naver_fare = int(adult['NaverFare'])
                    adult_tax = int(adult['Tax'])
                    adult_Qcharge = int(adult['QCharge'])
                    adult_fare = adult_base_fare + adult_naver_fare + adult_tax + adult_Qcharge

                    child_base_fare = int(child['Fare'])
                    child_naver_fare = int(child['NaverFare'])
                    child_tax = int(child['Tax'])
                    child_Qcharge = int(child['QCharge'])
                    child_fare = child_base_fare + child_naver_fare + child_tax + child_Qcharge

                    infant_base_fare = int(infant['Fare'])
                    infant_naver_fare = int(infant['NaverFare'])
                    infant_tax = int(infant['Tax'])
                    infant_Qcharge = int(infant['QCharge'])
                    infant_fare = infant_base_fare + infant_naver_fare + infant_tax + infant_Qcharge
                    
                    purchase_url = fare['ReserveParameter']['#cdata-section']
                    fare_class=parse_fare_class(purchase_url)
                    if infant_fare > 0:
                        continue
                    batch_manager.fare_info_queue.add_to_queue(key, seat_class_map[seat_class], agt, adult_fare, fetched_date, fare_class, purchase_url)
                except Exception as e:
                    print(f"운임 정보 처리 중 오류: {e}")
                    continue
    return True

def parsing_international_flights(response, seat_class):
    international_list = response.get("data", {}).get("internationalList", {})
    results = international_list.get("results", {})
    
    airline_map = results.get('airlines', {})
    # airport_map = results.get('airports', {})
    schedules = results.get("schedules", [])
    fares = results.get("fares", [])
    fare_types = results.get("fareTypes", [])
    
    skipped_air_id=save_flight_info(schedules=schedules, airline_map=airline_map)
    next_flag=save_fare_info(fares=fares, fare_types=fare_types, seat_class=seat_class, skipped_air_id=skipped_air_id)

    return 0