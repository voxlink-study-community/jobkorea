from notion_client import Client
from dotenv import load_dotenv
import os
import json

load_dotenv()

# 환경 변수 읽기
notion_api = os.getenv("NOTION_API_KEY")
database_id = os.getenv("NOTION_DATABASE_ID")

print(f"NOTION_API_KEY:{notion_api}")
print(f"DATABASE_ID:{database_id}")



def upload_to_notion(data_path, batch_size):
    # Notion API 클라이언트 초기화
    notion = Client(auth=notion_api)
    
    # .env 파일 로드
    
    count=0
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)


    for item in data:

        properties = {
            "기업명": {
                "title": [{"text": {"content": item["기업명"]}}]
            },
            "유형": {
                "multi_select": [{"name": t} for t in item.get("유형", [])]
            },
            "직함": {
                "multi_select": [{"name": t} for t in item.get("직함", [])]
            },
            "도메인(분야)": {
                "multi_select": [{"name": t} for t in item.get("도메인(분야)", [])]
            },
            "지원 자격(요구)": {
                "rich_text": [{"text": {"content": item.get("지원 자격(요구)", "")}}]
            },
            "우대사항": {
                "rich_text": [{"text": {"content": item.get("우대사항", "")}}]
            },
            "근무지": {
                "multi_select": [{"name": t} for t in item.get("근무지", [])]
            },
            "고용형태": {
                "select": {"name": item.get("고용형태", "")}
            },
            "경력": {
                "select": {"name": item.get("경력", "")}
            },
            "기업규모(종업원수)": {
                "number": item.get("기업규모(종업원수)", 0)
            },
            "stack": {
                "multi_select": [{"name": t} for t in item.get("stack", [])]
            },
            "기업규모(종업원수)": {
                "number": item.get("기업규모(종업원수)", 0)
            },
            "URL": {
                "url": item.get("URL", "")
            },
            "복리후생": {
                "multi_select": [{"name": t} for t in item.get("복리후생", [])]
            }
        }
        
        # Notion 페이지 생성
        notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        count+=1
        print(f'<Database> 1개 행이 notion에 삽입되었습니다--{count}/{batch_size}')
        
    return count

# Example JSON data
sample_data = [
    {
        "기업명": "샘플데이터",
        "유형": ["보험사", "금융"],
        "직함": ["데이터 분석가"],
        "도메인(분야)": ["보험", "금융"],
        "지원 자격(요구)": "SQL, Python 사용 가능",
        "우대사항": "AI 모델링 경험",
        "근무지": ["서울특별시 강남구"],
        "고용형태": "정규직",
        "경력": "3년 이상",
        "기업규모": 500,
        "stack": ["Python", "SQL", "AWS"],
        "기업규모(종업원수)": 500,
        "URL": "https://example.com/job",
        "복리후생": ["4대 보험", "연차", "재택근무 가능"]
    }
]
