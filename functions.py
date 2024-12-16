import os
import json
import time

# JSON 저장 함수
def save_to_json(data, batch_index, output_dir):
    output_file_name = f'all_data_batch_{batch_index}_{time.localtime().tm_mon}{time.localtime().tm_mday}{time.localtime().tm_hour}{time.localtime().tm_min}{time.localtime().tm_sec}.json'
    output_path = os.path.join('output', output_dir, output_file_name)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"  <save point> JSON 파일 저장 완료: {output_path}")

# 작업 디렉토리 생성 함수
def ensure_directory(directory):
    """Ensures that the specified directory exists. Creates it if it doesn't."""
    output_dir=os.path.join('output',directory)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

def raw_data_files(output_dir):
    raw_data_path = os.path.join("output", output_dir)
    
    # 디렉토리 내 JSON 파일 리스트 생성
    raw_data_files = [
        os.path.join(raw_data_path, file)  # 파일 경로 포함
        for file in os.listdir(raw_data_path)
        if file.endswith(".json")
    ]
    print('raw_data_files: ',raw_data_files)

    return raw_data_files

