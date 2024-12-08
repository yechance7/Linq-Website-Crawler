import csv
from pathlib import Path
import requests


# ========================
# 1. 데이터 요청 함수
# ========================
def request_news(page_idx: int, date_from: str, page_size: int, search_phrase: str = '') -> dict:
    """
    특정 페이지의 뉴스 데이터를 요청하는 함수
    :param page_idx: 요청할 페이지 번호
    :param date_from: 시작 날짜 (형식: MM/DD/YYYY)
    :param page_size: 페이지당 뉴스 수
    :param search_phrase: 검색어 (기본값: '')
    :return: 뉴스 데이터를 포함하는 응답(JSON)
    """
    url = "https://asia.tools.euroland.com/tools/Pressreleases/Main/GetNews/"

    data = {
        "strDateFrom": f"{date_from}",     # 요청 시작 날짜
        "pageIndex": f"{page_idx}",        # 페이지 번호
        "searchPhrase": f"{search_phrase}",# 검색어 필터
        "pageJummp": f"{page_size}",       # 한 페이지당 요청 뉴스 수
        "strDateTo": "",                   # 종료 날짜 비활성화
        "typeFilter": "",                  
        "orderBy": "0",                    # 최신순 정렬
        "hasTypeFilter": "false",          
        "companyCode": "hk-570",           # 특정 회사 코드
        "onlyInsiderInfo": "false",        
        "lang": "en-GB",                   # 언어 설정
        "v": "redesign",                   
        "alwaysIncludeInsiders": "false",
    }

    try:
        resp = requests.post(url=url, data=data, timeout=10)
        resp.raise_for_status()  # 예외 처리: 상태 코드 확인
        print(f"요청 성공: [{url}] 상태 코드: [{resp.status_code}]")
        return resp.json()
    except requests.RequestException as e:
        print(f"요청 오류: {e}")
        return {}


# ==========================
# 2. 데이터 응답 검증 로직
# ==========================
def validate_response(resp: dict) -> bool:
    """
    응답 데이터 유효성 검사
    :param resp: 응답 데이터(JSON)
    :return: 유효하면 True, 그렇지 않으면 False
    """
    required_keys = {'News', 'Attachments', 'total'}  # 필수 키 목록 정의
    if not isinstance(resp, dict) or not required_keys.issubset(resp.keys()):
        print(f"잘못된 응답 형식: {resp}")  # 잘못된 응답 출력
        return False
    return True


# ========================
# 3. 데이터 수집 함수
# ========================
def request_news_from_date(date_from: str):
    """
    특정 날짜부터 모든 뉴스 데이터를 수집
    :param date_from: 시작 날짜 (형식: MM/DD/YYYY)
    :return: 수집된 뉴스 응답 리스트
    """
    page_size = 10  # 한 페이지당 문서 수
    resp_list = []
    i = 0

    # 첫 번째 요청: 전체 문서 수 확인
    first_resp = request_news(0, date_from, page_size)
    if not validate_response(first_resp):  # 응답 유효성 검사
        return resp_list

    total_doc_cnt = int(first_resp['total'])  # 전체 문서 수 확인
    request_cnt = 0

    while request_cnt < total_doc_cnt:  # 전체 문서 수만큼 루프
        resp = request_news(i, date_from, page_size)
        if not validate_response(resp):  # 유효하지 않으면 중단
            break
        resp_list.append(resp)
        request_cnt += len(resp['News'])  # 수집한 문서 수 누적
        i += 1
    return resp_list


# ========================
# 4. 데이터 파싱 함수
# ========================
def parse_response(resp: dict) -> list[dict]:
    """
    응답 데이터에서 뉴스 정보를 추출하는 함수
    :param resp: 응답 데이터(JSON)
    :return: 뉴스 데이터 리스트 (딕셔너리 형식)
    """
    results = []
    for annual_report in resp['News']:
        # 첨부 파일 유효성 검사 및 추출
        attachment = next(
            (item for item in resp['Attachments'] if item['prID'] == annual_report['ID']),
            None
        )
        if attachment:  # 첨부 파일이 있는 경우
            result = {
                'title': annual_report['title'],          # 뉴스 제목
                'date': annual_report['formatedDate'],   # 뉴스 날짜
                'link': f"https://staticpacific.blob.core.windows.net/press-releases-attachments/{attachment['atID']}/{attachment['filename']}"
            }
            # PDF 파일만 저장
            if attachment['filename'].lower().endswith('.pdf'):
                results.append(result)
            else:
                print(f"예상치 못한 파일 형식: [{result['link']}]")  # 잘못된 형식 경고
        else:
            print(f"첨부 파일 없음: 뉴스 ID [{annual_report['ID']}]")  # 첨부파일이 없으면 경고
    return results


# ========================
# 5. PDF 다운로드 함수
# ========================
def download_pdf(base_path: Path, url: str):
    """
    PDF 파일 다운로드
    :param base_path: 파일 저장 경로
    :param url: 다운로드할 파일의 URL
    """
    try:
        base_path.mkdir(parents=True, exist_ok=True)  # 경로가 없으면 생성
        filename = url.split('/')[-1]  # 파일 이름 추출
        with requests.get(url, stream=True, timeout=10) as r:
            r.raise_for_status()  # HTTP 오류 검사
            with open(base_path / filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):  # 청크별로 파일 저장
                    f.write(chunk)
        print(f"다운로드 완료: [{filename}]")  # 다운로드 성공 메시지
    except Exception as e:
        print(f"다운로드 실패 [{url}]: {e}")  # 오류 메시지 출력


# ========================
# 6. CSV 저장 함수
# ========================
def save_to_csv(datas: list[dict], save_path: Path):
    """
    수집된 데이터를 CSV 파일로 저장
    :param datas: 뉴스 데이터 리스트
    :param save_path: CSV 저장 경로
    """
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)  # 경로가 없으면 생성
        with open(save_path, 'w', newline='', encoding='utf-8') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(['Title', 'Date', 'File Path'])  # CSV 헤더 작성
            for data in datas:
                filename = data['link'].split('/')[-1]  # 파일 이름 추출
                file_path = str(save_path.parent / filename)  # 파일 경로 생성
                csv_writer.writerow([data['title'], data['date'], file_path])  # 데이터 기록
        print(f"CSV 저장 완료: [{save_path}]")  # 저장 성공 메시지
    except IOError as e:
        print(f"CSV 저장 오류: {e}")  # 파일 저장 오류 시 경고


# ========================
# 메인 실행 코드
# ========================
resp_list = request_news_from_date('01/01/2024')  # 시작 날짜 설정

doc_info_list = []
for resp in resp_list:
    doc_info_list.extend(parse_response(resp))  # 응답 파싱 후 리스트 확장

# PDF 파일 다운로드
for doc_info in doc_info_list:
    download_pdf(Path.cwd() / 'data1', doc_info['link'])  # 파일 다운로드

# CSV 파일 생성
save_to_csv(doc_info_list, Path.cwd() / 'data1' / 'result.csv')  # CSV 저장
