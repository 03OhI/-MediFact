import requests
import pandas as pd

def get_snu_api_data():
    # SNU 팩트체크 내부 API 주소 (보건/의료 카테고리 ID: 10)
    # 직접 주소를 찌르면 HTML 파싱할 필요 없이 데이터가 바로 들어옵니다.
    api_url = "https://factcheck.snu.ac.kr/v2/get_facts"
    params = {
        "category": "보건·의료",
        "page": 1,
        "per_page": 10
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Referer': 'https://factcheck.snu.ac.kr/v2/facts?category=%EB%B3%B4%EA%B1%B4%C2%B7%EC%9D%98%EB%A3%8C',
        'X-Requested-With': 'XMLHttpRequest'
    }

    print("서버에 직접 데이터를 요청 중입니다...")
    response = requests.get(api_url, params=params, headers=headers)
    
    if response.status_code != 200:
        print(f"에러 발생! 상태 코드: {response.status_code}")
        return None

    # JSON 데이터 파싱
    json_data = response.json()
    items = json_data.get('facts', [])
    
    if not items:
        print("데이터를 찾을 수 없습니다. API 구조가 변경되었을 수 있습니다.")
        return pd.DataFrame()

    processed_data = []
    for item in items:
        processed_data.append({
            "뉴스 제목": item.get('title'),
            "검증 결과": item.get('status_name'), # 참, 거짓 등
            "검증 기관": item.get('source_name'),
            "날짜": item.get('created_at')[:10]
        })
            
    return pd.DataFrame(processed_data)

# 실행
df = get_snu_api_data()

if not df.empty:
    print("\n" + "="*60)
    print("       [API로 가져온 실시간 팩트체크 리스트]       ")
    print("="*60)
    print(df)
    print("="*60)
else:
    print("여전히 데이터가 비어있습니다. 사이트 보안 정책이 강화된 것 같아요.")