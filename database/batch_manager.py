from collections import deque
import time
import os
class BaseQueue:
   def __init__(self, db_instance, batch_manager, query_text):
       self.queue = deque()
       self.db_instance = db_instance
       self.batch_manager = batch_manager
       self.query_text = query_text

   def flush_queue(self):
       if not self.queue:
        #    print(f"{self.__class__.__name__} 큐가 비어 있습니다.")
           return True

       insert_start = time.time()
       first_attempt_queue = list(self.queue)
       success_flag, error_text = self.db_instance.execute_values_query(self.__class__.__name__, self.query_text, first_attempt_queue)
       insert_end = time.time()
       
       if success_flag:
           self.queue.clear()
           print(f"{self.__class__.__name__} 큐를 성공적으로 플러시했습니다. (소요 시간 : {round(insert_end-insert_start, 2)}초)\n")
       else:
           self.batch_manager.logger.insert_error_log(f'flush_queue({self.__class__.__name__})', error_text)
           print(error_text)
       self.unique_check_dict = {}
       return success_flag

class Flight_Info_Queue(BaseQueue):
    def __init__(self, db_instance, batch_manager, query_text):
        super().__init__(db_instance, batch_manager, query_text)
        self.unique_check_dict = {}

    def check_duplicate(self, record):
        key = record[0]  # air_id
        if key in self.unique_check_dict:
            #    print(f"Duplicate flight_info record found:")
            #    print(f"Existing: {self.unique_check_dict[key]}")
            #    print(f"Duplicate: {record}")
            return False
        else:
            self.unique_check_dict[key] = record
            return True
    
    def add_to_queue(self, air_id, airline, layover_depart_airport, layover_depart_timestamp,
                    layover_arrival_airport, layover_arrival_timestamp, total_journey_time, is_layover):
        record = (air_id, airline, layover_depart_airport, layover_depart_timestamp, layover_arrival_airport, layover_arrival_timestamp, total_journey_time, is_layover)
        
        # 새로운 레코드 (큐에 들어있지 않았던 경우)
        if self.check_duplicate(record): 
            self.queue.append(record)
            self.batch_manager.total_length += 1
            if self.batch_manager.total_length >= self.batch_manager.batch_size:
                self.batch_manager.flush_total_queues()
                self.batch_manager.total_length = 0
        
        # 이미 큐에 들어있는 레코드인 경우
        else: 
            pass
           
class Fare_Info_Queue(BaseQueue):
    def __init__(self, db_instance, batch_manager, query_text):
        super().__init__(db_instance, batch_manager, query_text)
        self.unique_check_dict = {}
       
    def check_duplicate(self, record):
        # air_id, seat_class, agt_code, fetched_date, fare_class
        key = (record[0], record[1], record[2], record[4], record[5])
        
        # 중복된 요금 정보 (근데 다름 미상의 원인)
        if key in self.unique_check_dict:
            existing_record = self.unique_check_dict[key]
            # 모든 필드 값이 같은지 비교
            if existing_record != record:
                # print(f"Duplicate fare_info record found with different values:")
                # print(f"Existing: {existing_record}")
                # print(f"New Record: {record}")
                # 새로 들어온 값이 더 저렴한 경우 -> 기존 큐에서 레코드 제거, unique dict 값 변경
                if record[3]<existing_record[3]:
                    # print('새로운 데이터의 가격이 더 저렴함\n')
                    remove_record=(existing_record[0], existing_record[1], existing_record[2],existing_record[3], existing_record[4], existing_record[5])
                    self.queue.remove(remove_record)
                    self.unique_check_dict[key] = record
                    return True
                else:
                    # print('기존 데이터의 가격이 더 저렴함\n')
                    return False
            else:
                # print('완전히 같은 데이터임\n')
                return False
        
        # 아예 새로운 요금정보
        else:
            self.unique_check_dict[key] = record
            return True
        
    def add_to_queue(self, air_id, seat_class, agt_code, adult_fare, fetched_date, fare_class='n', purchase_url=None):
        check_record = (air_id, seat_class, agt_code, adult_fare, fetched_date, fare_class, purchase_url)
        record=(air_id, seat_class, agt_code, adult_fare, fetched_date, fare_class)
        
        # 새로운 레코드 (큐에 들어있지 않았던 경우)
        if self.check_duplicate(check_record):
            self.queue.append(record)
            self.batch_manager.total_length += 1
            if self.batch_manager.total_length >= self.batch_manager.batch_size:
                self.batch_manager.flush_total_queues()
                self.batch_manager.total_length = 0
        
        # 이미 큐에 들어있는 레코드인 경우
        else: 
            pass

class Layover_Info_Queue(BaseQueue):
    def __init__(self, db_instance, batch_manager, query_text):
        super().__init__(db_instance, batch_manager, query_text)
        self.unique_check_dict = {}

    def check_duplicate(self, record):
        key = (record[0], record[1], record[2]) # (air_id, segment_id, layover_order)
        if key in self.unique_check_dict:
            #    print(f"Duplicate layover_info record found:")
            #    print(f"Existing: {self.unique_check_dict[key]}")
            #    print(f"Duplicate: {record}")
            return False
        else:
            self.unique_check_dict[key] = record
            return True
        
    def add_to_queue(self, air_id, segment_id, layover_order, connect_time):
        record = (air_id, segment_id, layover_order, connect_time)
        
        # 새로운 레코드 (큐에 들어있지 않았던 경우)
        if self.check_duplicate(record): 
            self.queue.append(record)
            self.batch_manager.total_length += 1
            if self.batch_manager.total_length >= self.batch_manager.batch_size:
                self.batch_manager.flush_total_queues()
                self.batch_manager.total_length = 0
        # 이미 큐에 들어있는 레코드인 경우
        else: 
            pass

class Batch_Manager:
   def __init__(self, db_instance, query_map, logger, redis_manager,tomorrow_flag, batch_size=30000):
       self.db_instance = db_instance
       self.batch_size = batch_size
       self.total_length = 0
       self.logger=logger
       self.redis_manager=redis_manager
       # Initialize queues
       self.flight_info_queue = Flight_Info_Queue(db_instance, self, query_map['flight_info'])
       self.layover_info_queue = Layover_Info_Queue(db_instance, self, query_map['layover_info'])
       
       # 내일 출발하는 항공권 일정일때 -> 전체 fare_info 테이블에 insert 후 cloud storage로 마이그레이션
       if tomorrow_flag=='Y':
           print('fare_info에 바로 insert합니다!')
           self.fare_info_queue = Fare_Info_Queue(db_instance, self, query_map['fare_info'])
        # 내일 모레 이후부터 출발하는 항공권 일정은 insert 최적화를 위해 temp_fare_info 테이블에 1차 삽입, 이후 전체 테이블로 마이그레이션
       else:
           print('temp_fare_info에 insert를 경유합니다!')
           self.fare_info_queue = Fare_Info_Queue(db_instance, self, query_map['temp_fare_info'])

   def flush_total_queues(self):
       check_start=time.time()
       self.redis_manager.check_insert_available_status()
       check_end=time.time()
       check_duration=int(check_end-check_start)
       flush_start = time.time()
       print("전체 큐 플러시를 시작합니다!")
       try:
           # 순서대로 플러시 (데이터 무결성을 위해)
           if not self.flight_info_queue.flush_queue():
               print("flight_info 큐 플러시 중 오류 발생")
               return False
               
           if not self.fare_info_queue.flush_queue():
               print("fare_info 큐 플러시 중 오류 발생")
               return False
               
           if not self.layover_info_queue.flush_queue():
               print("layover_info 큐 플러시 중 오류 발생")
               return False

           flush_end = time.time()
           print(f"insert 대기 시간 : {round(check_duration, 2)}초\n전체 큐 플러시 소요 시간 : {round(flush_end-flush_start, 2)}초")
           self.redis_manager.reset_insert_status()
           return True

       except Exception as e:
           print(f"전체 큐 플러시 중 오류 발생: {e}")
           self.redis_manager.reset_insert_status()
           return False
