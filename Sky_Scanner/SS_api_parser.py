import requests
import json
from datetime import datetime, date
import time
from SS_api_params import *
from SS_functions import *

def fetch_skyscanner_data(origin, destination, date, today, cnt, adults, cabin_class):
    origin_entity_id = airport_map[origin]['entity_id']
    destination_entity_id = airport_map[destination]['entity_id']
    headers, payload=return_header_payload(origin_entity_id, destination_entity_id, date, adults, cabin_class)
    
    data=send_request(payload=payload, headers=headers)
    # 디버깅용 원본 데이터 저장
    file_path=f"sky_test/{origin}/{origin}_{destination}_{date}.json"
    itin_data=data['itineraries']

    if len(itin_data['results'])==0: # 항공권 정보가 없는 경우 종료
        return cnt + 1
    
    # ensure_dir(file_path)
    # with open(file_path, 'w', encoding='utf-8') as f:
    #     json.dump(data, f, ensure_ascii=False, indent=4)
    # print(f"항공편 정보가 '{file_path}' 파일로 저장되었습니다.")
    
    fetched_date=today.strftime('%Y%m%d')
    print('크롤링 날짜:', fetched_date)
    # 운항 정보가 들어있는 부분
    for result in itin_data['results']:
        for leg in result['legs']:
            origin_code = leg['origin']['id']
            dest_code = leg['destination']['id']
            print("\n--- 전체 비행 정보 ---")
            print('unique_air_id:', leg['id'])
            print('출발 공항 코드:', origin_code)
            print('출발 공항 이름:', airport_map[origin_code]['name'])
            print('출발 나라:', airport_map[origin_code]['country'])
            print('도착 공항 코드:', dest_code)
            print('도착 공항 이름:', airport_map[dest_code]['name'])
            print('도착 나라:', airport_map[dest_code]['country'])
            departure_utc = convert_to_utc(leg['departure'], origin_code) # 출발지 공항 기준으로 되어있는 출발 시간을 UTC 기준으로 변환
            print(f"출발 타임스탬프 (UTC): {departure_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            arrival_utc = convert_to_utc(leg['arrival'], dest_code)
            print(f"도착 타임스탬프 (UTC): {arrival_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print('총 소요 시간:', leg['durationInMinutes'])
            print(f"경유 횟수: {leg['stopCount']}")

            print("\n--- 세부 비행 정보 ---")
            for index, segment in enumerate(leg['segments']):
                print("segment_id:", segment['id'].replace(str(segment['marketingCarrier']['id']), str(segment['operatingCarrier']['id'])))
                print('출발 공항 코드:', segment['origin']['flightPlaceId'])
                print('도착 공항 코드:', segment['destination']['flightPlaceId'])
                departure_utc = convert_to_utc(segment['departure'], segment['origin']['flightPlaceId']) # 출발지 공항 기준으로 되어있는 출발 시간을 UTC 기준으로 변환
                arrival_utc = convert_to_utc(segment['arrival'], segment['destination']['flightPlaceId'])
                print(f"출발 타임스탬프 (UTC): {departure_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                print(f"도착 타임스탬프 (UTC): {arrival_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                print("소요 시간:", segment['durationInMinutes'])
                print()
                # 환승 시간 계산
                if index < len(leg['segments']) - 1:
                    next_segment = leg['segments'][index + 1]
                    connect_time = calculate_connect_time(segment['arrival'], next_segment['departure'])
                else:
                    connect_time = 0
                
                print("환승 시간:", connect_time)
        
            # 요금 정보 파싱
            # fare_info['id'] = leg['id']
            for option in result['pricingOptions']:
                # fare_option = {
                #     'price': int(option['price']['amount']),
                #     'agent_ids': option['agentIds'],
                #     'items': []
                # }
                for item in option['items']:
                    print('agent_id: ', item['agentId'])
                    print('price: ', int(item['price']['amount']))
                    print('url', "https://www.skyscanner.co.kr"+item['url'])
    return cnt