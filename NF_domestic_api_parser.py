from utils.fetch_process_functions import convert_to_timestamp, convert_to_utc
from NF_global_objects import get_today, get_batch_queue, get_logger, get_progress, get_total_combi_length, update_progress
import time
today=get_today()
batch_queue=get_batch_queue()
logger=get_logger()


def fetch_domestic_flights(response, flight_text):
    start=time.time()
    schedules=response['data']['domesticFlights']['departures']
    for air in schedules:
        seat_class=air['seatClass'] # 좌석 등급
        seat_cnt=air['seatCnt'] # 잔여 좌석수 # TODO 해외 항공권이랑 비교 필요
        air_id=air['departureDate']+air['depCity']+air['arrCity']+air['airlineCode']+air['fitName']+air['seatClass']
        fetched_date=today.strftime('%Y%m%d')

        # 항공권 정보 삽입
        air_id=air_id
        airline_name = air['airlineName']
        # depart_country=airport_map[air['depCity']]['country']
        depart_airport= air['depCity'] # airport_map[air['depCity']]['name']
        
        depart_timestamp= convert_to_utc(convert_to_timestamp(air['departureDate'], air['depCity'])) # UTC 기준 출발 시간
        
        arrival_airport= air['arrCity'] # airport_map[air['arrCity']]['name']
        # arrival_country=airport_map[air['arrCity']]['country']
        arrival_timestamp= convert_to_utc(convert_to_timestamp(air['arrivalDate'], air['depCity'])) # UTC 기준 출발 시간
        if seat_class == "Y":
            option_type="일반석"
        elif seat_class == "D":
            option_type="할인석"
        elif seat_class=="L":
            option_type="특가석"
        elif seat_class=="C":
            option_type="비즈니스석"

        journey_time= int(air['journeyTime'][:2])*60 + int(air['journeyTime'][3:])
        
        insert_data_to_flight_info=(
                air_id, airline_name, 
                depart_airport, depart_timestamp,
                arrival_airport, arrival_timestamp,
                journey_time,
                False
            )
        batch_queue.add_to_queue('flight_info', insert_data_to_flight_info) # 배치큐에 삽입
        for agt_option in air['fare']:
            discountFare = agt_option['discountFare'] or 0
            publish_fee=agt_option['publishFee']
            adult_fare = agt_option['adultFare'] + agt_option['aTax'] + agt_option['aFuel'] + discountFare + publish_fee
            child_fare = agt_option['childFare'] + agt_option['cTax'] + agt_option['cFuel'] + discountFare + publish_fee
            agt_code= agt_option['agtCode']
            # booking_class= agt_option['bookingClass'],
            # adult_base_fare= agt_option['adultFare'],
            # atax= agt_option['aTax'],
            # afuel= agt_option['aFuel'],
            # child_base_fare= agt_option['childFare'],
            # ctax= agt_option['cTax'],
            # cfuel= agt_option['cFuel'],
            # publish_free= agt_option['publishFee'],
            # discountFare= discountFare,
            child_fare=None
            purchase_url=None
            insert_data_to_fare_info=(air_id, option_type, agt_code, adult_fare, fetched_date)
            batch_queue.add_to_queue('fare_info', insert_data_to_fare_info)
    update_progress()
    progress=get_progress()
    total_combi_length=get_total_combi_length()
    progress_ratio = progress / total_combi_length * 100
    end=time.time()
    logger.info(f"{flight_text}\n처리된 항공권 일정 비율 : {progress}/{total_combi_length}\n소요 시간 : {round(end-start, 2)}초")
    return 0