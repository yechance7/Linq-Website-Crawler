from bs4 import BeautifulSoup
import csv
from pathlib import Path
import requests


# ========================
# 1. 데이터 요청 및 응답 처리
# ========================

# 1-1. 뉴스 데이터 요청
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
        "strDateFrom": date_from,
        "pageIndex": page_idx,
        "searchPhrase": search_phrase,
        "pageJummp": page_size,
        "strDateTo": "",
        "typeFilter": "",
        "orderBy": "0",
        "hasTypeFilter": "false",
        "companyCode": "hk-570",
        "onlyInsiderInfo": "false",
        "lang": "en-GB",
        "v": "redesign",
        "alwaysIncludeInsiders": "false",
    }

    try:
        resp = requests.post(url=url, data=data, timeout=10)
        resp.raise_for_status()
        print(f"요청 성공: [{url}] 상태 코드: [{resp.status_code}]")
        return resp.json()
    except requests.RequestException as e:
        print(f"요청 오류: {e}")
        return {}


# 1-2. 응답 유효성 검사
def validate_response(resp: dict) -> bool:
    """
    응답 데이터 유효성 검사
    :param resp: 응답 데이터(JSON)
    :return: 유효하면 True, 그렇지 않으면 False
    """
    required_keys = {'News', 'Attachments', 'total'}
    if not isinstance(resp, dict) or not required_keys.issubset(resp.keys()):
        print(f"잘못된 응답 형식: {resp}")
        return False
    return True


# 1-3. 뉴스 데이터 수집
def request_news_from_date(date_from: str):
    """
    특정 날짜부터 모든 뉴스 데이터를 수집
    :param date_from: 시작 날짜 (형식: MM/DD/YYYY)
    :return: 수집된 뉴스 응답 리스트
    """
    page_size = 10
    resp_list = []
    i = 0

    first_resp = request_news(0, date_from, page_size)
    if not validate_response(first_resp):
        return resp_list

    total_doc_cnt = int(first_resp['total'])
    request_cnt = 0

    while request_cnt < total_doc_cnt:
        resp = request_news(i, date_from, page_size)
        if not validate_response(resp):
            break
        resp_list.append(resp)
        request_cnt += len(resp['News'])
        i += 1
    return resp_list


# ========================
# 2. 데이터 파싱 및 처리
# ========================

# 2-1. 응답 데이터 파싱
def parse_response(resp: dict) -> list[dict]:
    """
    응답 데이터에서 뉴스 정보를 추출하는 함수
    :param resp: 응답 데이터(JSON)
    :return: 뉴스 데이터 리스트 (딕셔너리 형식)
    """
    results = []
    for annual_report in resp['News']:
        attachment = next(
            (item for item in resp['Attachments'] if item['prID'] == annual_report['ID']),
            None
        )
        if attachment:
            file_link = f"https://staticpacific.blob.core.windows.net/press-releases-attachments/{attachment['atID']}/{attachment['filename']}"

            # PDF 파일인지 검사
            if attachment['filename'].lower().endswith('.pdf'):
                result = {
                    'title': annual_report['title'],
                    'date': annual_report['formatedDate'],
                    'link': file_link
                }
                results.append(result)

            # 예상치 못한 파일 형식 처리
            else:
                print(f"PDF가 아닌 파일 형식: [{file_link}]")
                display_pre_content(file_link)
        else:
            print(f"첨부 파일 없음: 뉴스 ID [{annual_report['ID']}]")
    return results


# 2-2. 예상치 못한 파일 형식 처리
def display_pre_content(file_link: str):
    """
    예상치 못한 파일 형식을 처리하고, <pre> 태그 내용을 출력
    :param file_link: 예상치 못한 파일의 URL
    """
    try:
        response = requests.get(file_link, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        pre_content = soup.find('pre')
        if pre_content:
            print(pre_content.get_text(strip=True))
        else:
            print("None")
    except requests.RequestException as e:
        print(f"파일 요청 오류: {e}")


# ========================
# 3. 데이터 저장 및 출력
# ========================

# 3-1. PDF 파일 다운로드
def download_pdf(base_path: Path, url: str):
    """
    PDF 파일 다운로드
    :param base_path: 파일 저장 경로
    :param url: 다운로드할 파일의 URL
    """
    try:
        base_path.mkdir(parents=True, exist_ok=True)
        filename = url.split('/')[-1]
        with requests.get(url, stream=True, timeout=10) as r:
            r.raise_for_status()
            with open(base_path / filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"다운로드 완료: [{filename}]")
    except Exception as e:
        print(f"다운로드 실패 [{url}]: {e}")


# 3-2. CSV 파일 저장
def save_to_csv(datas: list[dict], save_path: Path):
    """
    수집된 데이터를 CSV 파일로 저장
    :param datas: 뉴스 데이터 리스트
    :param save_path: CSV 저장 경로
    """
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'w', newline='', encoding='utf-8') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(['title', 'date', 'link'])
            for data in datas:
                filename = data['link'].split('/')[-1]
                file_path = str(save_path.parent / filename)
                csv_writer.writerow([data['title'], data['date'], file_path])
        print(f"CSV 저장 완료: [{save_path}]")
    except IOError as e:
        print(f"CSV 저장 오류: {e}")


# ========================
# 4. 메인 실행 코드
# ========================

if __name__ == "__main__":
    resp_list = request_news_from_date('01/01/2024')

    doc_info_list = []
    for resp in resp_list:
        doc_info_list.extend(parse_response(resp))

    for doc_info in doc_info_list:
        download_pdf(Path.cwd() / 'data', doc_info['link'])

    save_to_csv(doc_info_list, Path.cwd() / 'data' / 'data.csv')
