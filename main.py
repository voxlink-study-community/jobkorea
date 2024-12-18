import argparse
import functions as fc
import crawl as cr
import parse as ps
import os
import notion as nt

def main():
    parser = argparse.ArgumentParser(description="Main module to process output directory.")
    parser.add_argument("output_dir", type=str, help="Path to the output directory")
    args = parser.parse_args()

    output_dir = args.output_dir
    max_pages=17
    href_list=[]

    all_data = []


    batch_size = 40  # 한 번에 저장할 데이터 개수

    batch_index = 0  # 저장 배치 인덱스
    print(f"Output directory set to: {output_dir}") 
    fc.ensure_directory(output_dir)  # 디렉토리 생성

    # crawl.py 실행
    href_list=cr.crawl_href(max_pages)
    
    count_sum=0 #notion insert 합계 세기
    for i, url in enumerate(href_list):
    
        print('=' * 20)
        print(f"접속 중: {url} ({i+1}/{len(href_list)})")
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
