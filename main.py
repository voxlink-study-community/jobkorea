import argparse
import functions as fc
import crawl as cr
import parse as ps
import os
import notion as nt
from crawl import setup_driver_with_proxy
import requests
import time

def main():
    parser = argparse.ArgumentParser(description="Main module to process output directory.")
    parser.add_argument("output_dir", type=str, help="Path to the output directory")
    args = parser.parse_args()

    output_dir = args.output_dir
    max_pages=17
    href_list=[]

    all_data = []


    def get_proxy_list():
        response = requests.get(
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all"
        )
        proxy_list = response.text.split("\n")
        return [proxy.strip() for proxy in proxy_list if proxy.strip()]  # 빈 줄 제거

    proxy_list = get_proxy_list()


    batch_size = 40  # 한 번에 저장할 데이터 개수


    batch_index = 0  # 저장 배치 인덱스
    print(f"Output directory set to: {output_dir}") 
    fc.ensure_directory(output_dir)  # 디렉토리 생성

    # 전체 실행 시간 측정 시작
    overall_start_time = time.time()
    # crawl.py 실행
    href_list=cr.crawl_href(max_pages)
    
    count_sum=0 #notion insert 합계 세기
    for i, url in enumerate(href_list):
    
        print('=' * 20)
        print(f"접속 중: {url} ({i+1}/{len(href_list)})")


        # 페이지별 실행 시간 측정 시작
        page_start_time = time.time()
        # crawl_pages 호출 및 보안 코드 처리
        page_data = cr.crawl_pages(i, url)

         # 페이지별 실행 시간 측정 종료
        page_end_time = time.time()
        print(f"[Timing] Page {i+1} processed in {page_end_time - page_start_time:.2f} seconds.")

        if page_data is None:
            print(f"URL 처리 실패: {url}")
            setup_driver_with_proxy(proxy_list)  # 새로운 driver 설정
            continue

        processed_item=ps.process_raw_data(output_dir, page_data)
        all_data.append(processed_item)


        page_data=cr.crawl_pages(i, url)
        processed_item=ps.process_raw_data(output_dir, page_data)
        all_data.append(processed_item)


       
        # batch_size개씩 데이터를 저장
        if (i + 1) % batch_size == 0 or (i + 1) == len(href_list):
            batch_index += 1
            processed_file=fc.save_to_json(all_data, batch_index, output_dir)
            # 노션 업로드
            count_in_this_batch=nt.upload_to_notion(processed_file, batch_size)
            

            all_data = []  # 저장 후 리스트 초기화
            count_sum+=count_in_this_batch
            print(f'<Database> 현재까지{count_sum}행이 notion에 삽입되었습니다')

        # if i==batch_size-1: # 간단하게 돌려볼 때
        #     break


    # 전체 실행 시간 측정 종료
    overall_end_time = time.time()
    print(f"[Timing] Total execution time: {overall_end_time - overall_start_time:.2f} seconds.")

    
    
    # 후가공
    # processed_files=[]
    # raw_data_files=fc.raw_data_files(output_dir)    
    # for i, file in enumerate(raw_data_files):

    #     processed_file=ps.process_raw_data(output_dir, file)
    #     processed_files.append(processed_file)
        
    #     # 노션 업로드
    #     nt.upload_to_notion(processed_file,count)
    
    

if __name__ == "__main__":
    main()
