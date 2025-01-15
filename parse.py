import json
import os
import re

def truncate_text(text, limit=2000):
    """텍스트가 limit을 초과하면 잘라서 반환"""
    if len(text) > limit:
        return text[:limit - 2] + ".."
    return text

def is_relevant_line(line):
    """문장이 의미 있는지 확인하는 함수"""
    # 길이가 너무 짧거나, 특정 패턴만 있는 경우 무시
    if len(line) < 5:  # 5자 이하 문장은 의미 없는 것으로 간주
        return False
    if re.match(r"^[ㆍ*-]+$", line):  # 목록 기호만 있는 경우 무시
        return False
    if "지원" in line and "가능" in line:  # 지원 안내 템플릿 필터링
        return False
    if "제출" in line and "필수" in line:  # 제출 서류 관련 템플릿 필터링
        return False
    # 기본적으로 유효한 문장으로 간주
    return True

def extract_requirements_from_table(tables):
    """테이블 데이터를 기반으로 직무요건과 우대사항 추출."""
    job_requirements = []
    preferred_qualifications = []

    for table in tables:
        table_data = table.get("table_data", [])
        if not table_data or len(table_data) <= 1:  # 데이터가 없거나 헤더만 있는 경우
            continue

        # 첫 번째 행은 헤더로 사용
        headers = table_data[0]
        rows = table_data[1:]

        # 헤더에 특정 열이 포함된 경우 데이터를 추출
        for row in rows:
            row_dict = {headers[i]: row[i] if i < len(row) else "N/A" for i in range(len(headers))}

           # 직무요건
            if "업무" in headers or "업무내용" in headers:
                if row_dict.get("업무내용", "N/A") != "N/A":
                    job_requirements.append(row_dict["업무내용"])
            if "자격요건" in headers:
                if row_dict.get("자격요건", "N/A") != "N/A":
                    job_requirements.append(row_dict["자격요건"])

                 # 자격요건에 우대사항이 포함된 경우 처리
                if "우대" in row_dict.get("자격요건", ""):
                    parts = row_dict["자격요건"].split("우대사항")
                    job_requirements.append(parts[0].strip())  # "우대사항" 이전 부분은 직무요건
                    if len(parts) > 1:
                        preferred_qualifications.append(parts[1].strip())  # 이후 부분은 우대사항

            # 우대사항
            if "우대사항" in headers:
                if row_dict.get("우대사항", "N/A") != "N/A":
                    preferred_qualifications.append(row_dict["우대사항"])

    # 중복 제거 및 정리
    job_requirements = list(set(filter(None, job_requirements)))  # 빈 문자열 제거
    preferred_qualifications = list(set(filter(None, preferred_qualifications)))

    return "\n".join(job_requirements), "\n".join(preferred_qualifications)

def extract_sections(article_text):
    """텍스트에서 직무요건과 우대사항을 추출."""
    job_requirements = []
    preferred_qualifications = []
    current_section = None  # 현재 섹션 추적

    # 줄 단위로 텍스트 분리
    lines = article_text.split("\n")

    for line in lines:
        line = line.strip()  # 공백 제거
        if not is_relevant_line(line):  # 필터링 로직 추가
            continue

        # 새로운 섹션 시작 확인
        if re.search(r"(업무|직무|역할|책임)", line):  # 직무요건 키워드
            current_section = "job_requirements"
            job_requirements.append(line)
        elif re.search(r"(우대|기술|skill|경험|능력)", line):  # 우대사항 키워드
            current_section = "preferred_qualifications"
            preferred_qualifications.append(line)
        elif line:  # 빈 줄이 아니면 현재 섹션에 추가
            if current_section == "job_requirements":
                job_requirements.append(line)
            elif current_section == "preferred_qualifications":
                preferred_qualifications.append(line)

    # 직무요건과 우대사항 정리
    job_requirements = truncate_text("\n".join(filter(None, job_requirements)))  # 빈 줄 제거 및 제한
    preferred_qualifications = truncate_text("\n".join(filter(None, preferred_qualifications)))

    return job_requirements, preferred_qualifications



def process_raw_data(output_dir, input_file):
    job_requirements="N/A"
    preferred_qualifications="N/A"
    # 입력 JSON 로드
    with open(input_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    processed_data = []

    # 데이터 처리
    for item in raw_data:
        company_info = item.get("company_info", [{}])
        first_info = company_info[0] if company_info else {}

        # article_text에서 직무요건과 우대사항 추출
        article_text = item.get("article_text", "N/A")
        if article_text!="N/A":
            job_requirements, preferred_qualifications = extract_sections(article_text)
        else:
            # 테이블 데이터에서 추출
            tables = item.get("tables", [])
            if tables !=[]:
                job_requirements, preferred_qualifications = extract_requirements_from_table(tables)

        job_requirements = truncate_text(job_requirements)
        preferred_qualifications = truncate_text(preferred_qualifications)

        # title에서 comma를 대체
        raw_title = first_info.get("기업명", "N/A")
        if raw_title != "N/A":
            titles = [title.replace(",", "-") for title in raw_title.split(",")]
            title_result = ",".join(titles)
        else:
            title_result = "N/A"
        # 근무지에서 comma를 대체
        raw_locations = first_info.get("근무지역", "N/A")
        if raw_locations != "N/A":
            locations = [location.replace(",", "-") for location in raw_locations.split(",")]
        else:
            locations = ["N/A"]

        # 산업(업종) 필드 처리: '·'를 기준으로 나누기
        raw_industry = first_info.get("산업(업종)", "N/A")
        if raw_industry != "N/A":
            industries = [industry.strip() for industry in raw_industry.split("·")]
        else:
            industries = ["N/A"]

        processed_item = {
            "기업명": title_result,
            "유형": industries,
            "직함": [first_info.get("직무", "N/A")],
            "도메인(분야)": [item.get("title", "").split("-")[0].strip()],
            "지원 자격(요구)": job_requirements,
            "우대사항": preferred_qualifications,
            "근무지": locations,
            "고용형태": first_info.get("고용형태", "N/A"),
            "경력": first_info.get("경력", "N/A"),
            "기업규모": 0,  # 추가 정보가 필요할 경우 추출 로직 작성
            "stack": [],  # 기술 스택은 별도 처리 필요
            "기업규모(종업원수)": 0,
            "URL": item.get("url", "N/A"),
            "복리후생": [],  # 복리후생은 별도 처리 필요
        }

        processed_data.append(processed_item)
    
    # 출력 파일 경로
    processed_dir = os.path.join('processed_output',output_dir)
    os.makedirs(processed_dir, exist_ok=True)  # 디렉토리 생성 (없으면 생성)

    # 입력 파일에서 파일명 추출
    _, file_with_ext = os.path.split(input_file)
    file_name, _ = os.path.splitext(file_with_ext)

    # 출력 파일명 생성
    processed_output_file = os.path.join(processed_dir, f"{file_name}_processed.json")
    with open(processed_output_file, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=4)
    print(f"Processed data saved to {processed_output_file}")
    
    return processed_output_file

