from collections import deque
# 배치 insert 큐
class Batch_Queue:
    def __init__(self, db_instance, query_map, logger, batch_size=3000):
        self.db_instance = db_instance
        self.query_map = query_map
        self.logger = logger
        self.batch_size = batch_size
        self.queue_dict = {
            "flight_info": deque(),
            "fare_info": deque(),
            "layover_info": deque()
        }
        self.total_length = 0  # 세개의 큐 길이 합 (업데이트) 목적 : flight_info부터 insert되는 것을 강제하기 위함 (데이터 무결성)
        self.air_id_check_set=set() # 

    def add_to_queue(self, queue_name, query_params):
        origin_check_length=len(self.air_id_check_set) # 큐에 넣기전 air_id 체크 리스트 길이
        self.air_id_check_set.add(query_params[0]) # 셋에 새로울지 아닐지 모르는 air_id 추가
        if len(self.air_id_check_set)==origin_check_length+1: # 기존과 다른 air_id가 추가되었다는 의미
            try:
                self.queue_dict[queue_name].append(query_params)
                self.total_length += 1
                if self.total_length > self.batch_size:
                    self.flush_total_queues()
                    self.total_length = 0
            except Exception as e:
                self.logger.error(f"큐에 항목 추가 및 insert 중 오류 발생: {e}")

    def flush_queue(self, queue_name):
        queue = self.queue_dict[queue_name]
        if not queue:
            self.logger.warning(f"{queue_name} 큐가 비어 있습니다.")
            return True
        
        query = self.query_map[queue_name]
        success_flag = self.db_instance.execute_values_query(query, list(queue))
        if success_flag:
            self.queue_dict[queue_name].clear()  # deque를 비움
            self.logger.info(f"{queue_name} 큐를 성공적으로 플러시했습니다.")
            return True
        else:
            self.logger.error(f"{queue_name} 큐 플러시 실패")
            return False
    
    def flush_total_queues(self):
        try:
            for queue_name in self.queue_dict.keys():
                if not self.flush_queue(queue_name):
                    self.logger.error(f"{queue_name} 큐 플러시 중 오류 발생")
                    return False
            self.air_id_check_set=set()
            return True
        except Exception as e:
            self.logger.error(f"전체 큐 플러시 중 오류 발생: {e}")
            return False