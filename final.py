import csv
from pathlib import Path
import requests


def request_news(page_idx: int, date_from: str, page_size: int, search_phrase: str = '') -> dict:
    """
    뉴스 데이터를 요청하는 함수
    :param page_idx: 페이지 인덱스
    :param date_from: 시작 날짜 ('MM/DD/YYYY' 형식)
    :param page_size: 페이지 당 문서 개수
    :param search_phrase: 검색어 (기본값: 빈 문자열)
    :return: 요청 결과 JSON 데이터
    """
    url = "https://asia.tools.euroland.com/tools/Pressreleases/Main/GetNews/"

    data = {
        "strDateFrom": f"{date_from}",
        "pageIndex": f"{page_idx}",
        "searchPhrase": f"{search_phrase}",
        "pageJummp": f"{page_size}",
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

    # API 요청 및 응답 상태 코드 출력
    resp = requests.post(url=url, data=data)
    print(f'requested to [{url}] status code: [{resp.status_code}]')
    return resp.json()


def request_news_from_date(date_from: str):
    """
    시작 날짜부터 모든 뉴스 문서 요청
    :param date_from: 시작 날짜 ('MM/DD/YYYY' 형식)
    :return: 뉴스 응답 목록
    """
    page_size = 10  # 한 페이지에 요청할 문서 개수
    total_doc_cnt = int(request_news(0, date_from, page_size)['total'])  # 전체 문서 개수
    request_cnt = 0  # 요청된 문서 개수 추적

    i = 0
    resp_list = []
    while request_cnt < total_doc_cnt:
        resp = request_news(i, date_from, page_size)
        resp_list.append(resp)
        request_cnt += len(resp['News'])  # 요청된 문서 수 업데이트
        i += 1  # 다음 페이지로 이동
    return resp_list


def parse_response(resp: dict) -> list[dict]:
    """
    뉴스 응답 데이터에서 제목, 날짜, PDF 링크 추출
    :param resp: 응답 JSON 데이터
    :return: 추출된 뉴스 정보 리스트
    """
    results = []
    for annual_report in resp['News']:
        # 첨부파일 정보 찾기
        attachment = next(
            item for item in resp['Attachments'] if item['prID'] == annual_report['ID']
        )
        result = {
            'title': annual_report['title'],
            'date': annual_report['formatedDate'],
            'link': f"https://staticpacific.blob.core.windows.net/press-releases-attachments/{attachment['atID']}/{attachment['filename']}"
        }

        # PDF 파일만 결과에 추가
        if attachment['filename'].endswith('.PDF'):
            results.append(result)
        else:
            print(f"unexpected file format in [{result['link']}]")

    return results


def download_pdf(base_path: Path, url: str):
    """
    PDF 파일 다운로드
    :param base_path: 다운로드 경로
    :param url: PDF 파일 URL
    """
    base_path.mkdir(parents=True, exist_ok=True)  # 폴더 생성
    filename: str = url.split('/')[-1]

    with requests.get(url, stream=True) as r:
        r.raise_for_status()  # 오류 발생 시 예외 발생
        with open(base_path / filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)  # 파일 쓰기
    print(f'downloaded [{url}]')


def save_to_csv(datas: list[dict], save_path: Path):
    """
    추출된 뉴스 정보를 CSV 파일로 저장
    :param datas: 뉴스 정보 리스트
    :param save_path: CSV 저장 경로
    """
    save_path.parent.mkdir(parents=True, exist_ok=True)  # 폴더 생성
    with open(save_path, 'w', newline='', encoding='utf-8') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['Title', 'Date', 'File Path'])  # CSV 헤더 작성

        for data in datas:
            filename = data['link'].split('/')[-1]
            file_path = str(save_path.parent / filename)
            csv_writer.writerow([data['title'], data['date'], file_path])  # 데이터 쓰기


# 시작 날짜 기준으로 뉴스 요청
resp_list = request_news_from_date('01/01/2024')

# 뉴스 문서 정보 파싱
doc_info_list = []
for resp in resp_list:
    doc_info_list.extend(parse_response(resp))

# PDF 파일 다운로드
for doc_info in doc_info_list:
    download_pdf(Path.cwd() / 'data1', doc_info['link'])

# CSV 파일 저장
save_to_csv(doc_info_list, Path.cwd() / 'data1' / 'result.csv')
