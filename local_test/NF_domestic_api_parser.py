import json
import time
import os
from NF_api_params import domastic_payload_form, return_header
from NF_functions import *
from local_test.NF_db_params import get_db_connection, execute_db_query, query_dict
from multiprocessing import Process, Queue
from psycopg2 import sql

def fetch_domestic_flights(departure, arrival, date, today, cnt):
    headers = return_header(departure, arrival, date)
    
    # 첫 번째 요청
    payload1 = domastic_payload_form(departure=departure, arrival=arrival, date=date)
    response_data1 = send_request(payload1, headers)

    # 디렉토리 생성
    directory = os.path.join(os.getcwd(), 'domestic_test', departure)
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = f'{departure}_{arrival}_{date}.json'
    filepath = os.path.join(directory, filename)
    # 결과를 저장할 리스트 생성
    flight_data = []

    for air in response_data1['data']['domesticFlights']['departures']:
        air_id=air['departureDate']+air['depCity']+air['arrCity']+air['airlineCode']+air['fitName']
        fetched_date=today.strftime('%Y%m%d')
        
        flight_info = {
            'air_id':air_id,
            'airline_name': air['airlineName'],
            
            'depart_country':airport_region_map[air['depCity']]['country'],
            'depart_airport': airport_region_map[air['depCity']]['name'],
            'depart_timestamp': timestamp_to_iso8601(return_time_stamp(air['departureDate'])),
            
            'arrival_airport': airport_region_map[air['arrCity']]['name'],
            'arrival_country':airport_region_map[air['arrCity']]['country'],
            'arrival_timestamp': timestamp_to_iso8601(return_time_stamp(air['arrivalDate'])),

            'journey_time': int(air['journeyTime'][:2])*60 + int(air['journeyTime'][2:]),
            # 'connect_time': None,
            'fetched_date':fetched_date,
            'fares': []
        }

        for agt_option in air['fare']:
            discountFare = agt_option['discountFare'] or 0
            adult_fare = agt_option['adultFare'] + agt_option['aTax'] + agt_option['aFuel'] + discountFare
            child_fare = agt_option['childFare'] + agt_option['cTax'] + agt_option['cFuel'] + discountFare

            fare_info = {
                'agt_code': agt_option['agtCode'],
                # 'booking_class': agt_option['bookingClass'],
                # 'adult_base_fare': agt_option['adultFare'],
                # 'atax': agt_option['aTax'],
                # 'afuel': agt_option['aFuel'],
                # 'child_base_fare': agt_option['childFare'],
                # 'ctax': agt_option['cTax'],
                # 'cfuel': agt_option['cFuel'],
                # 'publish_free': agt_option['publishFee'],
                # 'discountFare': discountFare,
                'adult_fare': adult_fare,
                'child_fare': child_fare
            }

            flight_info['fares'].append(fare_info)

        flight_data.append(flight_info)

    # JSON 파일로 저장
    with open(filepath, 'w', encoding='utf-8-sig') as file:
        json.dump(flight_data, file, ensure_ascii=False, indent=4)

    print(f"File saved: {filepath}")
    return 0 # cnt