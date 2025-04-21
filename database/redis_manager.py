import redis
import json
import time
import random
sleep_duration = random.uniform(0.1, 0.5)
class Redis_Manager:
    def __init__(self, host='10.0.0.9', port=6379, db=0):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        self.schedule_queue = "flight:schedule:queue"
        self.schedule_processing = "flight:schedule:processing"
        self.insert_flag_key = "flight:insert:flag"
        self.proxy_queue = "proxy:list"
        self.proxy_processing = "proxy:processing"
        self.crawling_status_key = "crawling:status"
        self.running_crawler_cnt_key = "running_crawler_cnt"


    def clear_schedule_queue(self):
        """
        스케줄 큐의 내용을 원자적으로 비움
        """
        try:
            # 파이프라인으로 원자적 실행
            pipe = self.redis_client.pipeline()
            pipe.llen(self.schedule_queue)
            pipe.llen(self.schedule_processing)
            pipe.delete(self.schedule_queue)
            pipe.delete(self.schedule_processing)
            results = pipe.execute()
            
            queue_length = results[0] + results[1]
            print(f"Current queue size before clearing: {queue_length}")
            print("Schedule queue content cleared successfully")
            
            return queue_length
        except Exception as e:
            print(f"Error clearing schedule queue content: {str(e)}")
            return None


    def get_schedule_params(self, timeout=15):
        """
        다음 스케줄을 원자적으로 가져옴 (FIFO)
        """
        try:
            result = self.redis_client.blmove(
                first_list=self.schedule_queue,
                second_list=self.schedule_processing,
                timeout=timeout,
                src="LEFT",
                dest="RIGHT"
            )
            if result:
                return json.loads(result)
            return None
        except Exception as e:
            print(f"Error getting next schedule: {str(e)}")
            return None

    def get_next_proxy(self):
        """
        다음 프록시를 원자적으로 가져옴 (FIFO)
        """
        try:
            result = self.redis_client.blmove(
                first_list=self.proxy_queue,
                second_list=self.proxy_processing,
                timeout=1,
                src="LEFT",
                dest="RIGHT"
            )
            if result:
                return json.loads(result)
            return None
        except Exception as e:
            print(f"Error getting next proxy: {str(e)}")
            return None

    def init_insert_flag(self):
        """
        Insert 플래그를 원자적으로 초기화
        """
        self.redis_client.set(self.insert_flag_key, '1')
        
    def check_insert_available_status(self):
        """
        Insert 가능 상태를 원자적으로 체크
        """
        lua_script = """
        if redis.call('get', KEYS[1]) == '1' then
            redis.call('set', KEYS[1], '0')
            return 1
        end
        return 0
        """
        while True:
            result = self.redis_client.eval(lua_script, 1, self.insert_flag_key)
            if result:
                # print('키 가져옴')
                return True
            time.sleep(sleep_duration)
            

    def reset_insert_status(self):
        """
        Insert 상태를 원자적으로 리셋
        """
        # print('키 반납')
        self.redis_client.set(self.insert_flag_key, '1')

    def requeue_proxy(self, proxy):
        """
        프록시를 원자적으로 재사용 큐에 추가
        """
        try:
            proxy_str = json.dumps(proxy)
            pipe = self.redis_client.pipeline()
            
            # 처리 중 큐에서 제거하고 메인 큐로 이동
            pipe.lrem(self.proxy_processing, 1, proxy_str)
            pipe.rpush(self.proxy_queue, proxy_str)
            
            pipe.execute()
            # print(f"Successfully requeued proxy: {proxy}")
            return True
            
        except Exception as e:
            print(f"Error requeueing proxy: {str(e)}")
            return False

    def finish_schedule_processing(self, schedule, success=True):
        """
        스케줄 처리 완료를 원자적으로 처리
        """
        try:
            schedule_str = json.dumps(schedule)
            pipe = self.redis_client.pipeline()
            
            # 처리 중 큐에서 제거
            pipe.lrem(self.schedule_processing, 1, schedule_str)
            
            # 실패한 경우 다시 메인 큐로
            if not success:
                pipe.rpush(self.schedule_queue, schedule_str)
                
            pipe.execute()
            return True
            
        except Exception as e:
            print(f"Error finishing schedule processing: {str(e)}")
            return False
        
    def get_proxy_queue_count(self):
        """
        프록시 큐에 남은 프록시 수를 반환합니다.
        메인 큐(proxy:list)와 처리 중인 큐(proxy:processing)의 총 개수를 반환합니다.
        
        Returns:
            tuple: (메인 큐 개수, 처리 중인 큐 개수, 전체 개수)
        """
        try:
            pipe = self.redis_client.pipeline()
            pipe.llen(self.proxy_queue)
            pipe.llen(self.proxy_processing)
            results = pipe.execute()
            
            main_queue_count = results[0]
            processing_queue_count = results[1]
            total_count = main_queue_count + processing_queue_count
            
            return main_queue_count, processing_queue_count, total_count
        except Exception as e:
            print(f"Error getting proxy queue count: {str(e)}")
            return None, None, None
            
    def remove_from_processing(self, proxy):
        """
        프록시를 processing 큐에서만 제거
        """
        try:
            proxy_str = json.dumps(proxy)
            # 처리 중 큐에서만 제거 (메인 큐로 이동하지 않음)
            self.redis_client.lrem(self.proxy_processing, 1, proxy_str)
            # print(f"Successfully removed proxy from processing: {proxy}")
            return True
        except Exception as e:
            print(f"Error removing proxy from processing: {str(e)}")
            return False
        
        
    def check_all_schedules_processed(self):
        """
        모든 스케줄이 처리되었는지 확인
        
        Returns:
            bool: 모든 스케줄이 처리되었으면 True, 아니면 False
        """
        try:
            pipe = self.redis_client.pipeline()
            pipe.llen(self.schedule_queue)
            pipe.llen(self.schedule_processing)
            results = pipe.execute()
            
            queue_length = results[0]
            processing_length = results[1]
            
            # 양쪽 큐 모두 비어있으면 모든 스케줄 처리 완료
            if queue_length == 0 and processing_length == 0:
                print("모든 스케줄이 처리되었습니다.")
                return True
            else:
                print(f"아직 처리되지 않은 스케줄이 있습니다. (대기 중: {queue_length}, 처리 중: {processing_length})")
                return False
        except Exception as e:
            print(f"스케줄 처리 상태 확인 중 오류 발생: {str(e)}")
            return False

    def set_crawling_completed(self, status='completed'):
        """
        크롤링 작업 완료 상태를 Redis에 저장
        
        Args:
            status: 상태 문자열 (기본값: 'completed')
        """
        try:
            self.redis_client.set(self.crawling_status_key, status)
            print(f"크롤링 상태를 '{status}'로 설정했습니다.")
            return True
        except Exception as e:
            print(f"크롤링 상태 설정 중 오류 발생: {str(e)}")
            return False

    def init_running_crawler_cnt(self):
        """
        running_crawler_cnt 키가 없다면 생성하고, 있다면 값을 0으로 초기화합니다.
        
        Returns:
            bool: 초기화 성공 시 True, 실패 시 False
        """
        try:
            self.redis_client.set(self.running_crawler_cnt_key, 0)
            print(f"Initialized {self.running_crawler_cnt_key} to 0")
            return True
        except Exception as e:
            print(f"Error initializing {self.running_crawler_cnt_key}: {str(e)}")
            return False

    def increment_crawler_cnt(self):
        """
        running_crawler_cnt 값을 1 증가시킵니다.
        
        Returns:
            int: 증가 후의 값, 오류 발생 시 None
        """
        try:
            # INCR 명령어는 원자적으로 값을 1 증가시킴
            # 키가 없을 경우 자동으로 생성하고 0으로 초기화한 후 1 증가
            new_value = self.redis_client.incr(self.running_crawler_cnt_key)
            return new_value
        except Exception as e:
            print(f"Error incrementing {self.running_crawler_cnt_key}: {str(e)}")
            return None

    def decrement_crawler_cnt(self):
        """
        running_crawler_cnt 값을 1 감소시킵니다.
        값이 0보다 작아지지 않도록 Lua 스크립트를 사용합니다.
        
        Returns:
            int: 감소 후의 값, 오류 발생 시 None
        """
        lua_script = """
        local key = KEYS[1]
        local exists = redis.call('EXISTS', key)
        
        if exists == 0 then
            redis.call('SET', key, 0)
            return 0
        end
        
        local current = tonumber(redis.call('GET', key))
        
        if current > 0 then
            local new_value = redis.call('DECR', key)
            return new_value
        else
            return 0
        end
        """
        
        try:
            new_value = self.redis_client.eval(lua_script, 1, self.running_crawler_cnt_key)
            return new_value
        except Exception as e:
            print(f"Error decrementing {self.running_crawler_cnt_key}: {str(e)}")
            return None

    def get_crawler_cnt(self):
        """
        running_crawler_cnt 현재 값을 조회합니다.
        
        Returns:
            int: 현재 값, 키가 없을 경우 0, 오류 발생 시 None
        """
        try:
            value = self.redis_client.get(self.running_crawler_cnt_key)
            if value is None:
                return 0
            return int(value)
        except Exception as e:
            print(f"Error getting {self.running_crawler_cnt_key}: {str(e)}")
            return None
    
    def reset_crawling_status(self):
        """
        크롤링 상태를 초기화 (크롤링 시작 시 호출)
        """
        try:
            self.redis_client.set(self.crawling_status_key, "running")
            print("크롤링 상태를 'running'으로 초기화했습니다.")
            return True
        except Exception as e:
            print(f"크롤링 상태 초기화 중 오류 발생: {str(e)}")
            return False