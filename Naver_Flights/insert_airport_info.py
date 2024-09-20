from NF_functions import airport_map
from NF_db_params import get_db_connection, execute_db_query, query_dict
conn=get_db_connection()
cur=conn.cursor()
insert_query=query_dict['airport_info']

for code, value in airport_map.items():
    if value['entity_id']=="경로 없음":
        continue
    execute_db_query(conn, cur, insert_query,(code, value['name'],value['country'], value['time_zone']))
    conn.commit()