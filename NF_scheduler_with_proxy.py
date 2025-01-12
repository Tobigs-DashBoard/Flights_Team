import sys
import threading
import time
import os
import random
from datetime import timedelta
import traceback
from queue import Queue, Empty
from NF_international_api_parser import fetch_international_flights
from NF_domestic_api_parser import fetch_domestic_flights
from utils.multi_request import origin_send_request, send_request_with_proxy
from config.api_params import return_header, domastic_payload_form, international_payload_form
from NF_global_objects import (
    get_logger, 
    get_today, 
    get_request_airport_map, 
    get_airport_map, 
    get_db, 
    get_batch_queue,
    get_proxy,
    init_total_combi_length, init_progress,
    get_proxy_queue_size, return_proxy_index, get_failed_proxy_index
)

# 전역 변수 설정
logger = get_logger()
airport_map = get_airport_map()
today = get_today()
request_airport_map = get_request_airport_map()
db = get_db()
batch_queue = get_batch_queue()
total_korea_airport = ["SEL", "CJU", "PUS", "CJJ", "KWJ", "TAE", "RSU", "USN", "HIN", "KPO", "WJU", "KUV", "MWX"]
error_set = set()  # api 요청 에러
none_error_count = {}  # 노선 없음 에러 카운트 딕셔너리: {(출발지, 도착지, 날짜, 국내/국제, 좌석등급): 횟수}

response_done_event = threading.Event()

def multi_request_worker(request_queue, response_queue, worker_done_event):
    """
    request 큐에 있는 요청을 보내고 받은 데이터를 response 큐에 넣는 스레드 함수
    """
    thread_id = threading.current_thread().name
    random_sec = random.randint(1, 10)
    while True:
        try:
            request = request_queue.get(timeout=1)
            departure, arrival, target_date, is_domestic, seat_class, proxy_index, proxy = request
            route_key = (departure, arrival, target_date, is_domestic, seat_class)

            # 이미 실패한 프록시인 경우 에러 세트에 추가하고 다음 요청으로 넘어감
            if proxy_index in get_failed_proxy_index():
                logger.error(f"[Thread-{thread_id}] 이미 실패한 프록시 입니다.")
                error_set.add((departure, arrival, target_date, is_domestic, seat_class))
                continue

            formatted_date = target_date.strftime('%Y%m%d')
            departure_name = airport_map[departure]['name']
            arrival_name = airport_map[arrival]['name']

            if is_domestic:
                # 국내선 항공편 처리
                headers = return_header(is_domestic, departure, arrival, formatted_date, seat_class)
                payload1 = domastic_payload_form(departure=departure, arrival=arrival, date=formatted_date, fare_type=seat_class)
                response = (
                    origin_send_request(payload1, headers, proxy_index)
                    if proxy == "my_ip"
                    else send_request_with_proxy(payload1, headers, proxy, proxy_index)
                )
                if response:
                    schedules = response['data']['domesticFlights']['departures']
                    if len(schedules) == 0:
                        time.sleep(random_sec)
                        logger.info(f"[Thread-{thread_id}] {target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 없음")
                        none_error_count[route_key] = none_error_count.get(route_key, 0) + 1
                        if none_error_count[route_key] < 30:
                            error_set.add((departure, arrival, target_date, is_domestic, seat_class))
                    else:
                        time.sleep(random_sec)
                        while True:
                            if response_queue.qsize() <= 5:
                                flight_text = f"[Thread-{thread_id}] {target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 데이터 수집 완료"
                                response_queue.put((response, True, flight_text, seat_class))
                                break
                else:
                    time.sleep(random_sec)
                    logger.error(f"[Thread-{thread_id}] {target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 탐색 중 API 에러")
                    error_set.add((departure, arrival, target_date, is_domestic, seat_class))
            
            else:
                # 국제선 항공편 처리
                headers = return_header(is_domestic, departure, arrival, formatted_date, seat_class)
                payload1 = international_payload_form(first=True, departure=departure, arrival=arrival, date=formatted_date, fare_type=seat_class)
                response = (
                    origin_send_request(payload1, headers, proxy_index)
                    if proxy == "my_ip"
                    else send_request_with_proxy(payload1, headers, proxy, proxy_index)
                )
                if response:
                    international_list = response.get("data", {}).get("internationalList", {})
                    galileo_key = international_list.get("galileoKey")
                    travel_biz_key = international_list.get("travelBizKey")
                    payload2 = international_payload_form(
                        first=False,
                        departure=departure,
                        arrival=arrival,
                        date=formatted_date,
                        fare_type=seat_class,
                        galileo_key=galileo_key,
                        travel_biz_key=travel_biz_key
                    )
                    time.sleep(3)
                    response = (
                        origin_send_request(payload2, headers, proxy_index)
                        if proxy == "my_ip"
                        else send_request_with_proxy(payload2, headers, proxy, proxy_index)
                    )
                    if response:
                        schedules = response.get("data", {}).get("internationalList", {}).get("results", {}).get("schedules", [])
                        if len(schedules) == 0:
                            time.sleep(random_sec)
                            logger.info(f"[Thread-{thread_id}] {target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 없음")
                            none_error_count[route_key] = none_error_count.get(route_key, 0) + 1
                            if none_error_count[route_key] < 30:
                                error_set.add((departure, arrival, target_date, is_domestic, seat_class))
                        else:
                            time.sleep(random_sec)
                            while True:
                                if response_queue.qsize() <= 5:
                                    flight_text = f"[Thread-{thread_id}] {target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 데이터 수집 완료"
                                    response_queue.put((response, False, flight_text, seat_class))
                                    break
                    else:
                        time.sleep(random_sec)
                        logger.error(f"[Thread-{thread_id}] {target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 탐색 중 API 에러")
                        error_set.add((departure, arrival, target_date, is_domestic, seat_class))
                else:
                    time.sleep(random_sec)
                    logger.error(f"[Thread-{thread_id}] {target_date}에 '{departure_name}'에서 '{arrival_name}'로 가는 노선 탐색 중 API 에러")
                    error_set.add((departure, arrival, target_date, is_domestic, seat_class))

        except Empty:
            worker_done_event.set()
            logger.info(f"[Thread-{thread_id}] 작업 완료")
            break
        except Exception as e:
            logger.error(f"[Thread-{thread_id}] 스레드 내부 작업 중 오류 발생: {e}")
            traceback.print_exc()

def start_workers(num_workers, request_queue, response_queue):
    """
    요청 보내는 스레드를 시작하는 함수
    
    * num_workers: 시작할 워커 스레드의 수
    * request_queue: 요청 큐
    * response_queue: 응답 큐
    :return: 생성된 스레드와 완료 이벤트의 리스트
    """
    threads = []
    worker_done_events = []
    for i in range(num_workers):
        worker_done_event = threading.Event()
        t = threading.Thread(target=multi_request_worker, args=(request_queue, response_queue, worker_done_event), name=f"Worker-{i+1}")
        t.start()
        threads.append(t)
        worker_done_events.append(worker_done_event)
    return threads, worker_done_events

def wait_for_request_threads(threads, worker_done_events):
    """
    모든 워커 스레드가 완료될 때까지 기다립니다.
    
    * threads: 워커 스레드 리스트
    * worker_done_events: 워커 완료 이벤트 리스트
    """
    for t, event in zip(threads, worker_done_events):
        event.wait()

def process_responses(response_queue):
    """
    응답 큐에서 순차적으로 응답 하나씩을 처리하는 함수
    
    * response_queue: 처리할 응답이 들어있는 큐
    * target_regions: 대상 지역 리스트
    """
    while True:
        try:
            response, is_domestic, flight_text, seat_class = response_queue.get(timeout=1)
            if is_domestic:
                fetch_domestic_flights(response, flight_text)
            else:
                fetch_international_flights(response, flight_text, seat_class)
        except Empty:
            if response_done_event.is_set():
                break
        except Exception as e:
            logger.error(f"응답 처리 중 오류 발생: {e}")
            traceback.print_exc()
            exit()
    logger.info("응답 처리 스레드가 종료되었습니다.")

def add_request_to_queue(request_queue, target_regions, korea_airport_list, time_gap=181):
    """
    요청 큐에 항공편 요청을 추가하는 함수
    
    * request_queue: 요청을 추가할 큐
    * target_regions: 대상 지역 리스트
    * korea_airport_list: 한국 공항 리스트
    * time_gap: 검색할 날짜 범위 (기본값: 181일)
    :return: 총 추가된 요청의 수
    """
    cnt = 0
    for departure in korea_airport_list:
        for arrival_target in target_regions:
            for airport in request_airport_map[arrival_target]:
                arrival = airport['IATA']
                if arrival == departure:
                    continue
                is_domestic = arrival in total_korea_airport and departure in total_korea_airport
                for i in range(2, time_gap):
                    target_date = today + timedelta(days=i)
                    proxy_1_index, proxy_1 = get_proxy()
                    return_proxy_index(proxy_1_index)
                    proxy_2_index, proxy_2 = get_proxy()
                    return_proxy_index(proxy_2_index)
                    if is_domestic:
                        seat_class = 'YC'
                        request_queue.put((departure, arrival, target_date, is_domestic, seat_class, proxy_1_index, proxy_1))
                        request_queue.put((arrival, departure, target_date, is_domestic, seat_class, proxy_2_index, proxy_2))
                        cnt += 2
                    else:
                        seat_class_list = ['Y', 'C']  # 일반석, 프리미엄 일반석, 비즈니스석(P), 일등석(F)
                        for seat_class in seat_class_list:
                            request_queue.put((departure, arrival, target_date, is_domestic, seat_class, proxy_1_index, proxy_1))
                            request_queue.put((arrival, departure, target_date, is_domestic, seat_class, proxy_2_index, proxy_2))
                            cnt += 2
    return cnt

def add_only_tomorrow_request_to_queue(request_queue, target_regions, korea_airport_list, time_gap=181):
    """
    요청 큐에 항공편 요청을 추가하는 함수
    
    * request_queue: 요청을 추가할 큐
    * target_regions: 대상 지역 리스트
    * korea_airport_list: 한국 공항 리스트
    * time_gap: 검색할 날짜 범위 (기본값: 181일)
    :return: 총 추가된 요청의 수
    """
    cnt = 0
    for departure in korea_airport_list:
        for arrival_target in target_regions:
            for airport in request_airport_map[arrival_target]:
                arrival = airport['IATA']
                if arrival == departure:
                    continue
                is_domestic = arrival in total_korea_airport and departure in total_korea_airport
                target_date = today + timedelta(days=1)
                proxy_1_index, proxy_1 = get_proxy()
                return_proxy_index(proxy_1_index)
                proxy_2_index, proxy_2 = get_proxy()
                return_proxy_index(proxy_2_index)
                if is_domestic:
                    seat_class = 'YC'
                    request_queue.put((departure, arrival, target_date, is_domestic, seat_class, proxy_1_index, proxy_1))
                    request_queue.put((arrival, departure, target_date, is_domestic, seat_class, proxy_2_index, proxy_2))
                    cnt += 2
                else:
                    seat_class_list = ['Y', 'C']  # 일반석, 프리미엄 일반석, 비즈니스석(P), 일등석(F)
                    for seat_class in seat_class_list:
                        request_queue.put((departure, arrival, target_date, is_domestic, seat_class, proxy_1_index, proxy_1))
                        request_queue.put((arrival, departure, target_date, is_domestic, seat_class, proxy_2_index, proxy_2))
                        cnt += 2
    return cnt


def add_error_combi_to_queue(error_set, request_queue):
    """
    에러가 발생한 요청들을 다시 요청 큐에 추가하는 함수
    
    * error_set: 에러가 발생한 요청들의 집합
    * request_queue: 요청을 추가할 큐
    """
    for error_combi in error_set:
        proxy_index, proxy = get_proxy()
        departure, arrival, target_date, is_domestic, seat_class = error_combi
        request_queue.put((departure, arrival, target_date, is_domestic, seat_class, proxy_index, proxy))
        return_proxy_index(proxy_index)

def main():
    """
    전체 크롤링 프로세스를 관리하는 함수
    """
    process_start = time.time()
    try:
        logger.info(f"남은 프록시 서버 수 : {get_proxy_queue_size()}")
        target_regions = os.environ.get('TARGET_REGION', '일본').split(',')
        korea_airport_list = ["SEL"]
        request_queue = Queue()
        response_queue = Queue()
        num_workers = min(get_proxy_queue_size(), 30)

        # 1. 내일 출발 항공권 처리
        logger.info("\n\n\n내일 출발 항공권 수집을 시작합니다.\n\n\n")
        threads, worker_done_events = start_workers(num_workers, request_queue, response_queue)
        
        # 내일 항공편만 요청 큐에 추가
        tomorrow_combi_length = add_only_tomorrow_request_to_queue(request_queue, target_regions, korea_airport_list)
        logger.info(f"내일 출발 항공권 일정 조합 수 : {tomorrow_combi_length}")
        init_total_combi_length(tomorrow_combi_length)
        init_progress()

        # 응답 처리 스레드 시작
        response_thread = threading.Thread(target=process_responses, args=(response_queue,))
        response_thread.start()

        # 내일 항공권 요청 처리 대기
        wait_for_request_threads(threads, worker_done_events)

        # 내일 항공권 API 에러 처리
        try_cnt = 1
        while len(error_set) >= 1:
            logger.info(f'\n\n\n내일 출발 API 에러 리스트 재시도 {try_cnt}번째')
            logger.info(f"api 오류난 항공권 일정 수 : {len(error_set)}")
            request_queue = Queue()
            current_error_set = error_set.copy()
            add_error_combi_to_queue(current_error_set, request_queue)
            error_set.clear()
            threads, worker_done_events = start_workers(min(len(current_error_set), num_workers), request_queue, response_queue)
            wait_for_request_threads(threads, worker_done_events)
            batch_queue.flush_total_queues()
            try_cnt += 1

        logger.info("\n\n\n내일 출발 항공권 수집이 완료되었습니다. 이제 나머지 기간의 항공권 수집을 시작합니다.\n\n\n")

        # 2. 나머지 기간 항공권 처리
        request_queue = Queue()  # 새로운 큐 생성
        threads, worker_done_events = start_workers(num_workers, request_queue, response_queue)

        # 전체 기간 항공편 요청 추가
        total_combi_length = add_request_to_queue(request_queue, target_regions, korea_airport_list)
        logger.info(f"나머지 기간 항공권 일정 조합 수 : {total_combi_length}")
        init_total_combi_length(total_combi_length)
        init_progress()
        # 나머지 기간 요청 처리 대기
        wait_for_request_threads(threads, worker_done_events)

        # 나머지 기간 API 에러 처리
        try_cnt = 1
        while len(error_set) >= 1:
            logger.info(f'\n\n\nAPI 에러 리스트 재시도 {try_cnt}번째')
            logger.info(f"api 오류난 항공권 일정 수 : {len(error_set)}")
            request_queue = Queue()
            current_error_set = error_set.copy()
            add_error_combi_to_queue(current_error_set, request_queue)
            error_set.clear()
            threads, worker_done_events = start_workers(min(len(current_error_set), num_workers), request_queue, response_queue)
            wait_for_request_threads(threads, worker_done_events)
            batch_queue.flush_total_queues()
            try_cnt += 1

        # 크롤링 완료 처리
        response_done_event.set()
        response_thread.join()
        batch_queue.flush_total_queues()
        db.close()
        
        # 프로세스 소요 시간 계산
        process_end = time.time()
        process_time_seconds = process_end - process_start
        hours, remainder = divmod(process_time_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        logger.info(f"총 프로세스 소요 시간 : {int(hours)}시간 {int(minutes)}분 {int(seconds)}초")

        # 노선 없음 통계 로깅
        total_no_route = len([k for k, v in none_error_count.items() if v >= 30])
        if total_no_route > 0:
            logger.info(f"\n총 {total_no_route}개의 노선에서 항공편이 없는 것으로 확인되었습니다.")
            for route_key, count in none_error_count.items():
                if count >= 30:
                    departure, arrival, target_date, is_domestic, seat_class = route_key
                    departure_name = airport_map[departure]['name']
                    arrival_name = airport_map[arrival]['name']
                    logger.info(f"노선 없음 확정: {departure_name}-{arrival_name} ({seat_class}) - {target_date}")

    except Exception as e:
        logger.error(f"오류로 인한 프로그램 종료: {e}")
        logger.error(traceback.format_exc())
        batch_queue.flush_total_queues()
        db.close()

if __name__ == "__main__":
    main()