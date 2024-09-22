
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

def crawl_flights(departure, arrival, is_domestic):
    cnt = 0  # 예외처리용 카운터
    start_time = time.time()
    departure_name=airport_map[departure]['name']
    arrival_name=airport_map[arrival]['name']
    logger.info(f"출발지:{departure_name} 도착지:{arrival_name}")
    # print(f"출발지:{airport_map[departure]['name']} 도착지:{airport_map[arrival]['name']}")

    for i in range(1, 181):
        if cnt >= 10:  # 연속으로 10일간의 항공편이 없으면 해당 출발지 도착지 조합은 검색 중단
            logger.info(f"'{departure_name}'에서 '{arrival_name}'로 가는 노선 검색 중단: 연속 10일 항공편 없음")
            # print(f"{departure}에서 {arrival}로 가는 노선 검색 중단: 연속 10일 항공편 없음")
            break
        
        target_date = today + timedelta(days=i)
        formatted_date = target_date.strftime('%Y%m%d')
        
        if is_domestic:
            origin_cnt=cnt
            cnt = fetch_domestic_flights(departure, arrival, formatted_date, cnt)
            if origin_cnt==cnt+1:
                logger.info(f"{target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 없음")
            elif origin_cnt==cnt+2:
                logger.info(f"{target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 탐색 중 api 에러")
                time.sleep(300) # TODO api 에러 걸렸을 때 어떻게 처리할지 (안걸리는게 베스트이지만, 어쩔 수 없다면 재시작을 몇분뒤에 해야하는지 찾아내야함)
            # else:
                # logger.info(f"{target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 데이터 수집 완료")
        else:
            origin_cnt=cnt
            cnt = fetch_international_flights(departure, arrival, formatted_date, cnt)
            if origin_cnt==cnt+1:
                logger.info(f"{target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 없음")
            elif origin_cnt==cnt+2:
                logger.info(f"{target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 탐색 중 api 에러")
                time.sleep(300) # TODO api 에러 걸렸을 때 어떻게 처리할지 (안걸리는게 베스트이지만, 어쩔 수 없다면 재시작을 몇분뒤에 해야하는지 찾아내야함)
            # else:
                # logger.info(f"{target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 데이터 수집 완료")
        
        random_sec = random.randint(3, 7)
        time.sleep(random_sec)

    end_time = time.time()
    duration = (end_time - start_time) // 60
    logger.info(f"소요시간: {duration} 분\n150초간 중지\n")
    # print(f"소요시간: {duration} 분\n") 

if __name__ == "__main__":
    try:
        target_regions = os.environ.get('TARGET_REGION', '대한민국').split(',')
        time.sleep(60)  # 매일 자정 00시에 실행되기 때문에 1분 늦게 시작시킴
        korea_airport_list = ["SEL", "CJU", "PUS", "CJJ", "KWJ", "TAE", "RSU", "USN", "HIN", "KPO", "WJU", "KUV", "MWX"]
        arrival_target_list = target_regions  # "대한민국", "일본", "동남아", "중국", "유럽", "미주", "대양주", "남미", "아시아", "중동", "아프리카"

        # 모든 공항 조합을 한 번에 처리
        for departure in korea_airport_list:
            for arrival_target in arrival_target_list:
                for airport in request_airport_map[arrival_target]:
                    arrival = airport['IATA']
                    if arrival == departure:  # 출발지와 도착지가 같은 경우 스킵
                        continue
                    
                    is_domestic = arrival in korea_airport_list and departure in korea_airport_list
                    
                    # 정방향 크롤링
                    crawl_flights(departure, arrival, is_domestic)
                    time.sleep(150) # 180일 수집 후 150초 휴식
                    
                    if not is_domestic:
                        # 역방향 크롤링
                        crawl_flights(arrival, departure, is_domestic)
                        time.sleep(150) # 180일 수집 후 150초 휴식

        logger.info('\n\n크롤링 완료!!!!')
        batch_queue.flush_total_queues() # 큐에 남아있는 모든 데이터 마지막으로 삽입
        db.close()

    except Exception as e:
        logger.error('\n\n오류로 인한 프로그램 종료')
        logger.error('상세 오류 정보:')
        logger.error(traceback.format_exc())  # 이 줄이 상세한 오류 정보를 로그에 기록합니다.
        batch_queue.flush_total_queues()
        db.close()