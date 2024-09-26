
from NF_global_objects import get_logger, get_today, get_request_airport_map, get_airport_map, get_db, get_batch_queue
from NF_international_api_parser import fetch_international_flights
from NF_domestic_api_parser import fetch_domestic_flights
from datetime import timedelta
import random
import time
import os
import traceback

logger=get_logger()
airport_map=get_airport_map()
today=get_today()
request_airport_map=get_request_airport_map()
db=get_db()
batch_queue=get_batch_queue()
error_combi_list=[]
total_korea_airport=["SEL", "CJU", "PUS", "CJJ", "KWJ", "TAE", "RSU", "USN", "HIN", "KPO", "WJU", "KUV", "MWX"]
empty_combi_map={} # 항공권 노선마다 항공권이 없는 개수를 체크하기 위한 딕셔너리 (10일 이상 항공권이 없으면 해당 노선 자체가 뚫려있지 않다고 생각)
progress=0
def get_total_combi_length(target_regions, korea_airport_list, time_gap=181):
    arrival_length=0
    for target_region in target_regions:
        arrival_length+=len(request_airport_map[target_region])    
    return arrival_length*len(korea_airport_list)*time_gap

def make_random_combi_list(target_regions, korea_airport_list, total_combi_length, time_gap=181):
    global progress  # Declare 'progress' as global before using it
    for departure in korea_airport_list:
        for arrival_target in target_regions:
            for airport in request_airport_map[arrival_target]:
                arrival = airport['IATA']
                if arrival == departure:  # Skip if departure and arrival are the same
                    continue
                is_domestic = arrival in total_korea_airport and departure in total_korea_airport
                empty_combi_map[departure+arrival] = 0
                for i in range(1, time_gap):
                    target_date = today + timedelta(days=i)
                    crawl_flights(departure, arrival, target_date, is_domestic, 0)
                    progress += 1  # Modify 'progress'
                    progress_ratio = progress / total_combi_length * 100
                    logger.info(f"전체 항공권 중 {round(progress_ratio, 2)} 퍼센트 크롤링 완료")  # Log progress
                
                # If not domestic, switch departure and arrival
                if not is_domestic:
                    for i in range(1, time_gap):
                        target_date = today + timedelta(days=i)
                        crawl_flights(arrival, departure, target_date, is_domestic, 0)
                        progress += 1  # Modify 'progress'
                        progress_ratio = progress / total_combi_length * 100
                        logger.info(f"전체 항공권 중 {round(progress_ratio, 2)} 퍼센트 크롤링 완료")  # Log progress

def crawl_flights(departure, arrival, target_date, is_domestic, cnt=0):
    formatted_date = target_date.strftime('%Y%m%d')
    departure_name=airport_map[departure]['name']
    arrival_name=airport_map[arrival]['name']
    logger.info(f"{target_date} 출발지:{departure_name} 도착지:{arrival_name}")
    if is_domestic:
        if empty_combi_map[departure+arrival]<10:
            cnt = fetch_domestic_flights(departure, arrival, formatted_date, cnt)
            if cnt==1:
                logger.info(f"{target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 없음")
                error_combi_list.append((departure, arrival, target_date, is_domestic, 0))
                empty_combi_map[departure+arrival]+=1
            elif cnt==2:
                logger.info(f"{target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 탐색 중 api 에러")
                error_combi_list.append((departure, arrival, target_date, is_domestic, 0))
            else:
                empty_combi_map[departure+arrival]=0

    else:
        if empty_combi_map[departure+arrival]<10:
            cnt = fetch_international_flights(departure, arrival, formatted_date, cnt)
            empty_combi_map[departure+arrival]=0
            if cnt==1:
                logger.info(f"{target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 없음")
                error_combi_list.append((departure, arrival, target_date, is_domestic, 0))
                empty_combi_map[departure+arrival]+=1
            elif cnt==2:
                logger.info(f"{target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 탐색 중 api 에러")
                error_combi_list.append((departure, arrival, target_date, is_domestic, 0))
            else:
                empty_combi_map[departure+arrival]=0
        
    random_sec = random.randint(1, 2)
    time.sleep(random_sec)



if __name__ == "__main__":
    try:
        time.sleep(60)
        target_regions = os.environ.get('TARGET_REGION', '대한민국').split(',')
        korea_airport_list = ["SEL", "CJU"]#["SEL", "CJU", "PUS", "CJJ", "KWJ", "TAE", "RSU", "USN", "HIN", "KPO", "WJU", "KUV", "MWX"]
        total_combi_length=get_total_combi_length(target_regions, korea_airport_list, 181)
        logger.info(f"전체 항공권 조합 수 : {total_combi_length}")
        make_random_combi_list(target_regions, korea_airport_list, total_combi_length, 181)
        batch_queue.flush_total_queues() # 큐에 남아있는 모든 데이터 마지막으로 삽입
        db.close()
        logger.error('\n\n 오류난 조합들')
        for error_combi in error_combi_list:
            logger.error(str(error_combi)+"\n")

    except Exception as e:
        logger.error('\n\n오류로 인한 프로그램 종료')
        logger.error('상세 오류 정보:')
        logger.error(traceback.format_exc())
        batch_queue.flush_total_queues()
        db.close()
        logger.error('\n\n 오류난 조합들')
        for error_combi in error_combi_list:
            logger.error(str(error_combi)+"\n")
        logger.error('\n\n 아직 크롤링하지 못한 곳')