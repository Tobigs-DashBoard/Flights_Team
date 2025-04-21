from NF_global_objects import get_db, get_airport_map, get_query_map
airport_map=get_airport_map()
db=get_db()
query_map=get_query_map()
query=query_map['airport_info']
input_list=[]
for code, value in airport_map.items():
    insert_data=(code, value['name'],value['country'], value['time_zone'])
    input_list.append(insert_data)

db.execute_values_query('airport_info', query, input_list)