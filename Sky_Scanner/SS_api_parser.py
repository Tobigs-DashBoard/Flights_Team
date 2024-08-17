import requests
import json
from datetime import datetime, date
import time
from SS_api_params import *

'''검색 용 공항 코드'''
with open('Sky_Scanner/airport_entityId_map.json', 'r', encoding='utf-8') as f:
    airport_entity_id_map=json.load(f)

def fetch_skyscanner_data(origin, destination, date, adults=1, cabin_class="ECONOMY"):
    origin_entity_id = airport_entity_id_map[origin]['entity_id']
    destination_entity_id = airport_entity_id_map[destination]['entity_id']
    headers, payload=return_header_payload(origin_entity_id, destination_entity_id, date, adults, cabin_class)
    
    data=send_request(payload=payload, headers=headers)
    # 디버깅용 원본 데이터 저장
    with open('sky_test_origin.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    # 운항 정보가 들어있는 부분
    itin_data=data['itineraries']

    flight_info_list = [] # 항공권 정보
    fare_info_list = [] # 요금 정보

    if len(itin_data['results'])==0: # 항공권 정보가 없는 경우 종료
        time.sleep(10)  
        return 0
    for result in itin_data['results']:
        flight_info = {}  # 운항 정보
        fare_info = {}  # 요금 정보

        leg = result['legs'][0]
        common_id = result['id']
        flight_info['id'] = common_id
        flight_info['is_layover'] = leg['stopCount'] > 0
        flight_info['flights'] = []
        
        for i, segment in enumerate(leg['segments']):
            flight = {
                'air_id': f"{segment['departure'][:10].replace('-', '')}{segment['origin']['displayCode']}{segment['destination']['displayCode']}{segment['flightNumber']}",
                'airline': segment['marketingCarrier']['name'],
                'depart_region': segment['origin']['country'],
                'depart_airport': segment['origin']['name'],
                'arrival_region': segment['destination']['country'],
                'arrival_airport': segment['destination']['name'],
                'journey_time': segment['durationInMinutes'],
                'depart_timestamp': format_timestamp(parse_timestamp(segment['departure'])),
                'arrival_timestamp': format_timestamp(parse_timestamp(segment['arrival']))
            }
            # 환승 시간 계산
            if i < len(leg['segments']) - 1:
                next_segment = leg['segments'][i + 1]
                flight['connect_time'] = calculate_connect_time(segment['arrival'], next_segment['departure'])
            else:
                flight['connect_time'] = 0
            
            flight_info['flights'].append(flight)
        
        # 요금 정보 파싱
        fare_info['id'] = common_id  # 공통 ID 추가
        fare_info['options'] = []
        for option in result['pricingOptions']:
            fare_option = {
                'price': int(option['price']['amount']),
                'agent_ids': option['agentIds'],
                'items': []
            }
            for item in option['items']:
                fare_item = {
                    'agent_id': item['agentId'],
                    'price': int(item['price']['amount']),
                    # 'booking_proposition': item['bookingProposition'],
                    'url': "https://www.skyscanner.co.kr"+item['url']
                }
                fare_option['items'].append(fare_item)
            fare_info['options'].append(fare_option)
        
        flight_info_list.append(flight_info)
        fare_info_list.append(fare_info)

    origin_name=airport_entity_id_map[origin]['name']
    destination_name=airport_entity_id_map[destination]['name']
    file_path = f'Sky_Results/test/{destination_name}/flight_info/{origin_name}_{destination_name}_{date}.json'
    ensure_dir(file_path)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(flight_info_list, f, ensure_ascii=False, indent=4)
    print(f"항공편 정보가 '{file_path}' 파일로 저장되었습니다.")

    file_path = f'Sky_Results/test/{destination_name}/fare_info/{origin_name}_{destination_name}_{date}.json'
    ensure_dir(file_path)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(fare_info_list, f, ensure_ascii=False, indent=4)
    print(f"항공편 정보가 '{file_path}' 파일로 저장되었습니다.")

    time.sleep(10)
    return 0
    

# if __name__ == "__main__":
#     '''검색 용 공항 코드'''
#     with open('Naver_Flights/request_airport_map.json', 'r', encoding='utf-8') as f:
#         request_airport_map=json.load(f)
#     for airport in request_airport_map['일본']:
#         origin = 'ICN'
#         destination= airport['IATA']
#         adults = 1
#         cabin_class = "ECONOMY"
#         '''오늘 날짜 기준 3일 뒤의 데이터까지 수집'''
#         today = date.today()
#         for i in range(1, 4): 
#             target_date = today + timedelta(days=i)
#             formatted_date = target_date.strftime('%Y-%m-%d')  # YYYY-MM-DD 형식으로 변경
#             fetch_skyscanner_data(origin, destination, formatted_date, adults, cabin_class)

test_airport_list=['DFW','MSN','DGA','LIR','TAC','DCY','DQA','DBR','NLF','DAU','DRW','SRY','TAZ','DAT','RTI','KUT','DWD','YDA','GDV','YDQ','GSM','DAY','DAB','DAX','DZH','SCC','LGI','DOL','DEB','DEC','YVZ','YDF','DRG','LUM','PDK','BJX','CEC','NTR','DRT','YWJ','HXD','ESC','DEM','DNZ','DEN','DGH','PGK','SSA','DPT','DRB','DSM','CPO','DSI','VPS','DTW','IDR','DVL','DPO','KWB','DEF','DDD','DHI','DRV','DIB','IQQ','DIN','DKS','DLG','DLY','DMU','DNR','NIM','DPL','DIG','DIU','ROR','DCA','RNB','RRS','RVK','ROS','TJM','RET','RLG','ROW','ROP','ROT','RTM','RTA']
if __name__ == "__main__":
    '''검색 용 공항 코드'''
    for departure in test_airport_list:
        for arrival in test_airport_list:
            adults = 1
            cabin_class = "ECONOMY"
            '''오늘 날짜 기준 3일 뒤의 데이터까지 수집'''
            if departure == arrival:
                continue
            today = date.today()
            for i in range(1, 4): 
                target_date = today + timedelta(days=i)
                formatted_date = target_date.strftime('%Y-%m-%d')  # YYYY-MM-DD 형식으로 변경
                fetch_skyscanner_data(departure, arrival, formatted_date, adults, cabin_class)

