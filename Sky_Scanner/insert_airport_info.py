from SS_functions import *
from SS_db_params import *
conn=get_db_connection()
cur=conn.cursor()
insert_query=query_dict['airport_info']

for code, value in airport_map.items():
    if value['entity_id']=="경로 없음":
        continue
    execute_db_query(conn, cur, insert_query,(code, value['name'],value['country'], value['time_zone']))
    conn.commit()