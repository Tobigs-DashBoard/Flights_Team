from google.cloud import bigquery
from datetime import datetime
from zoneinfo import ZoneInfo

class Big_Query_Logger:

    def __init__(self, project_id, success_table_id, error_table_id, instance_id):
        self.project_id=project_id
        self.client=bigquery.Client(project=project_id)
        self.success_table_id=success_table_id
        self.error_table_id=error_table_id
        self.instance_id=instance_id
        self.base_logger_params={'route_key': None, 'target_date':None, 'seat_class':None}
    

    def insert_success_log(self, total_duration, status):
        row = {
            'instance_id': self.instance_id,
            'route_key': self.base_logger_params['route_key'],
            'target_date': self.base_logger_params['target_date'],
            'seat_class': self.base_logger_params['seat_class'],
            'created_at': datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
            'total_duration': total_duration,
            'status' : status
        }
        
        
        errors = self.client.insert_rows_json(self.success_table_id, [row])
        if len(errors)!=0:
            print(errors)
        # print(errors)

    def insert_error_log(self, error_func, error_log):
        
        row = {
            'instance_id': self.instance_id,
            'route_key': self.base_logger_params['route_key'],
            'target_date': self.base_logger_params['target_date'],
            'seat_class': self.base_logger_params['seat_class'],
            'created_at': datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
            'error_func': error_func,
            'error_log': error_log
        }
        
        errors = self.client.insert_rows_json(self.error_table_id, [row])
        

# if __name__ == '__main__':
#    # 먼저 테이블 존재 확인 및 생성
#    ensure_tables_exist()
   
#    # Success 로그 테스트
#    insert_success_log(
#        instance_id="crawler-1",
#        route_key='ICN_KIX',
#        target_date='20251022',
#        seat_class='일반석',
#        total_duration=200,
#        data_count=2345
#    )
   
#    # Error 로그 테스트
#    insert_error_log(
#        instance_id="crawler-1",
#        route_key='ICN_KIX',
#        target_date='20251022',
#        seat_class='일반석',
#        error_func='batch_insert()',
#        error_log='traceback ~~'
#    )