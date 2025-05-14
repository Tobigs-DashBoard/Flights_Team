import threading
import time
import sys
sys.stdout.reconfigure(line_buffering=True)  # Python 3.7+
import traceback
from queue import Queue, Empty
from NF_international_api_parser import parsing_international_flights
from NF_domestic_api_parser import parsing_domestic_flights
from utils.multi_request import send_request
from config.api_params import return_header, domastic_payload_form, international_payload_form
from NF_global_objects import (
    get_today,
    get_airport_map, 
    get_db,
    get_bigquery_logger, 
    get_batch_manager, 
    get_schedule_params, 
    get_next_proxy, 
    finish_schedule_processing, 
    init_logger_params, 
    requeue_proxy,remove_from_processing,
    get_proxy_queue_count,
    get_max_thread_count,
    check_crawling_done,
    increment_crawler_cnt,
    decrement_crawler_cnt,
    crawler_running_check
)
from datetime import datetime
import psutil

def mem_monitoring():
    # 전체 시스템 메모리와 스왑 사용량 정보 가져오기
    virtual_memory = psutil.virtual_memory()
    swap_memory = psutil.swap_memory()
    
    # 전체 메모리 + 스왑 사용량 비율 계산
    total_memory = virtual_memory.total + swap_memory.total
    used_memory = virtual_memory.used + swap_memory.used
    
    # 전체 메모리 사용 비율
    memory_usage_percent = (used_memory / total_memory) * 100
    if memory_usage_percent < 70:
        return True
    else:
        print('총 메모리:', total_memory)
        print('사용중인 메모리:', used_memory)
        print('메모리 사용률:', round(memory_usage_percent, 2))
        return False


def check_response(response, is_domestic):
    # 재시도 필요 X
    if not response:
        return None
    
    if response=='retry':
        return 'retry'
    
    # 정상적인 응답값인지 확인
    if is_domestic:
        try:
            schedules = response['data']['domesticFlights']['departures']
            return response
        except Exception as e:
            # print(e)
            # print(response)
            return None
    else:
        try:
            schedules = response['data']['internationalList']['results']['schedules']
            return response
        except Exception as e:
            # print(e)
            # print(response)
            return None
    
    
class CrawlerManager:
    def __init__(self):
        self.threads = []
        self.worker_done_events = []
        self.response_queue = Queue()
        
        # 전역 객체들 초기화
        self.airport_map = get_airport_map()
        self.today = get_today()
        self.db = get_db()
        self.batch_manager = get_batch_manager()
        self.logger = get_bigquery_logger()
        self.seat_class_map = {'Y':'일반석', 'C':'비즈니스석','YC':'일반/비즈니스'}

    def multi_request_worker(self, worker_done_event):
        """워커 스레드 함수"""
        thread_id = threading.current_thread().name
        while True:
            if not mem_monitoring():  # 메모리 사용량이 높으면
                time.sleep(10)  # 잠시 대기
                continue
            try:
                process_start = time.time()
                active_count = sum(1 for t in self.threads if t.is_alive())
                proxy = get_next_proxy()
                schedule = get_schedule_params()
                
                if not proxy or not schedule:
                    if not proxy:
                        print('프록시 없음')
                    if not schedule:
                        print('스케줄 없음')
                    worker_done_event.set()
                    break

                depart_airport = schedule['depart_airport']
                arrival_airport = schedule['arrival_airport']
                is_domestic = schedule['is_domestic']
                seat_class = schedule['seat_class']
                target_date = schedule['target_date']
                route_key = depart_airport.upper() + '_' + arrival_airport.upper()

                if is_domestic:
                    self._process_domestic_flight(thread_id, schedule, proxy, process_start, 
                                               depart_airport, arrival_airport, target_date, 
                                               seat_class, route_key, is_domestic)
                else:
                    self._process_international_flight(thread_id, schedule, proxy, process_start, 
                                                    depart_airport, arrival_airport, target_date, 
                                                    seat_class, route_key, is_domestic)

            except Exception as e:
                print(f"[{thread_id}] 스레드 내부 작업 중 오류 발생: {e}")
                traceback.print_exc()

    def _process_domestic_flight(self, thread_id, schedule, proxy, process_start, 
                               depart_airport, arrival_airport, target_date, 
                               seat_class, route_key, is_domestic):
        """국내선 항공편 처리"""
        headers = return_header(is_domestic, depart_airport, arrival_airport, target_date, seat_class)
        payload = domastic_payload_form(departure=depart_airport, arrival=arrival_airport, 
                                    date=target_date, fare_type=seat_class)
        response = send_request(payload=payload, headers=headers, proxy=proxy)
        response=check_response(response, is_domestic)
        if response and response!='retry':
            # schedules = response['data']['domesticFlights']['departures']
            while True:
                if self.response_queue.qsize() <= get_max_thread_count():
                    process_end = time.time()
                    duration = process_end - process_start
                    self.response_queue.put((response, is_domestic, seat_class, route_key, target_date, duration))
                    print(proxy['http'], thread_id, schedule, 'response 성공')
                    finish_schedule_processing(schedule, success=True)
                    requeue_proxy(proxy=proxy)
                    break
                else:
                    time.sleep(0.5)
                    continue
        else:
            finish_schedule_processing(schedule, success=False)
            requeue_proxy(proxy=proxy) # if response=='retry' else remove_from_processing(proxy=proxy)


    def _process_international_flight(self, thread_id, schedule, proxy, process_start, 
                                    depart_airport, arrival_airport, target_date, 
                                    seat_class, route_key, is_domestic):
        """국제선 항공편 처리"""
        headers = return_header(is_domestic, depart_airport, arrival_airport, target_date, seat_class)
        payload1 = international_payload_form(first=True, departure=depart_airport, arrival=arrival_airport, 
                                           date=target_date, fare_type=seat_class)
        response = send_request(payload=payload1, headers=headers, proxy=proxy)
        response=check_response(response, is_domestic) # 정상적인 응답값인지 확인
        time.sleep(3)
        if response and response!='retry':
            international_list = response.get("data", {}).get("internationalList", {})
            galileo_key = international_list.get("galileoKey")
            travel_biz_key = international_list.get("travelBizKey")
            
            payload2 = international_payload_form(
                first=False,
                departure=depart_airport,
                arrival=arrival_airport,
                date=target_date,
                fare_type=seat_class,
                galileo_key=galileo_key,
                travel_biz_key=travel_biz_key
            )
            
            response = send_request(payload=payload2, headers=headers, proxy=proxy)
            response=check_response(response, is_domestic)
            if response and response!='retry':
                # schedules = response.get("data", {}).get("internationalList", {}).get("results", {}).get("schedules", [])
                while True:
                    if self.response_queue.qsize() <= get_max_thread_count():
                        process_end = time.time()
                        duration = process_end - process_start
                        self.response_queue.put((response, is_domestic, seat_class, route_key, target_date, duration))
                        finish_schedule_processing(schedule, success=True)
                        print(proxy['http'], thread_id, schedule, 'response 성공')
                        requeue_proxy(proxy=proxy)
                        break
                    else:
                        time.sleep(0.5)
                        continue
            else:
                finish_schedule_processing(schedule, success=False)
                requeue_proxy(proxy=proxy) # if response=='retry' else remove_from_processing(proxy=proxy)
        else:
            finish_schedule_processing(schedule, success=False)
            requeue_proxy(proxy=proxy) # if response=='retry' else remove_from_processing(proxy=proxy)

    def process_responses(self, worker_threads):
        """응답 처리 스레드 함수"""
        # cnt = 1
        while True:
            try:
                response, is_domestic, seat_class, route_key, target_date, duration = self.response_queue.get(timeout=5)
                init_logger_params(
                    route_key=route_key, 
                    target_date=datetime.strptime(target_date, '%Y%m%d').date().isoformat(), 
                    seat_class=self.seat_class_map[seat_class]
                )
                
                start = time.time()
                if is_domestic:
                    try:
                        schedules = response['data']['domesticFlights']['departures']
                    except Exception as e:
                        print(response)
                else:
                    schedules = response['data']['internationalList']['results']['schedules']
                
                # 노선이 없는 경우
                if len(schedules)==0:
                    end = time.time()
                    total_duration = (end-start) + duration
                    self.logger.insert_success_log(int(total_duration), 'N')
                else:
                    if is_domestic:
                        parsing_domestic_flights(response)
                    else:
                        parsing_international_flights(response, seat_class)
                
                    end = time.time()
                    total_duration = (end-start) + duration
                    main_queue_count, processing_queue_count, total_count = get_proxy_queue_count()
                    print('잉여 프록시 수:', main_queue_count)
                    self.logger.insert_success_log(int(total_duration), 'Y')
                
            except Empty:
                if all(not t.is_alive() for t in worker_threads):
                    print('요청 스레드 다 꺼져있음')
                    break
                continue
            except Exception as e:
                print(f"응답 처리 중 오류 발생: {e}")
                print(traceback.format_exc())
                break
                
        print('응답처리 스레드 종료')
        self.batch_manager.flush_total_queues()
        self.db.close()

    def start_workers(self, num_workers):
        """워커 스레드들 시작"""
        for i in range(num_workers):
            worker_done_event = threading.Event()
            t = threading.Thread(
                target=self.multi_request_worker, 
                args=(worker_done_event,),
                name=f"Worker-{i+1}"
            )
            self.threads.append(t)
            self.worker_done_events.append(worker_done_event)
            t.start()
        return self.threads, self.worker_done_events

    def wait_for_request_threads(self):
        """모든 워커 스레드 완료 대기"""
        for t, event in zip(self.threads, self.worker_done_events):
            event.wait()

    def run(self):
        """크롤러 실행"""
        try:
            # 프록시 개수 확인 및 워커 수 설정
            main_queue_count, processing_queue_count, total_count = get_proxy_queue_count()
            num_workers = min(main_queue_count, get_max_thread_count())
            # 워커 스레드 시작
            threads, _ = self.start_workers(num_workers)
            # 응답 처리 스레드 시작
            response_thread = threading.Thread(target=self.process_responses, args=(threads,))
            response_thread.start()

            # 워커 스레드 완료 대기
            self.wait_for_request_threads()
            
            # 응답 처리 스레드 완료 대기
            response_thread.join()
            self.db.close()

        except Exception as e:
            print(f"크롤러 실행 중 오류 발생: {e}")
            print(traceback.format_exc())
            self.batch_manager.flush_total_queues()
            self.db.close()

if __name__ == "__main__":
    crawler = CrawlerManager()
    crawler_running_check()
    increment_crawler_cnt() # 실행중인 크롤러 수 1증가
    crawler.run()
    crawler.batch_manager.flush_total_queues()
    crawler.db.close()
    decrement_crawler_cnt() # 종료 후 크롤러 수 1감소
    check_crawling_done() # 스케줄 큐가 비었고, 크롤러가 모두 꺼졌으면 크롤링 종료 표시