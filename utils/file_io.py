import json
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)