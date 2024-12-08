# Linq_Website_Crawler


## 📁 프로젝트 폴더 구조

```plaintext
Linq_Website_Crawler/
│
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 애플리케이션 시작점
│   │
│   ├── api/                     # 라우터와 엔드포인트 관리
│   │   ├── __init__.py
│   │   ├── user_router.py       # 사용자 관련 API 라우터
│   │   ├── voice_router.py      # 음성 메시지 관련 API 라우터
│   │   └── auth_router.py       # 카카오 로그인 관련 라우터
│   │
│   ├── auth/                    # 인증 및 OAuth 관련 로직
│   │   ├── __init__.py
│   │   ├── kakao_oauth.py       # 카카오 OAuth2.0 인증 처리
│   │   └── jwt_handler.py       # JWT 생성 및 검증 로직
│   │
│   ├── crud/                    # 데이터베이스 CRUD 로직
│   │   ├── __init__.py
│   │   ├── crud_user.py         # 사용자 테이블 관련 CRUD
│   │   └── crud_voice.py        # 음성 테이블 관련 CRUD
│   │
│   ├── models/                  # Pydantic 및 SQLAlchemy 모델 정의
│   │   ├── __init__.py
│   │   ├── user.py              # Users 테이블 모델
│   │   └── voice.py             # Voice 테이블 모델
│   │
│   ├── schemas/                 # 요청/응답 스키마
│   │   ├── __init__.py
│   │   ├── user.py              # 사용자 요청/응답 스키마
│   │   └── voice.py             # 음성 요청/응답 스키마
│   │
│   ├── db/                      # 데이터베이스 연결 및 초기화
│   │   ├── __init__.py
│   │   └── connection.py        # DB 연결 설정
│   │
│   ├── core/                    # 설정 및 유틸리티
│   │   ├── __init__.py
│   │   ├── config.py            # 환경 설정 (환경변수 관리)
│   │   └── security.py          # 보안 관련 설정 (JWT, OAuth 등)
│   │
│   └── tests/                   # 테스트 코드
│       ├── __init__.py
│       ├── test_user.py         # 사용자 테스트
│       └── test_voice.py        # 음성 메시지 테스트
│
├── requirements.txt             # Python 의존성 패키지 목록
├── README.md                    # 프로젝트 설명 문서
├── Dockerfile                   # Docker 설정 파일
├── docker-compose.yml           # Docker Compose 설정
└── .gitignore                   # Git 무시 파일

##가상환경 설정

```shell
pip install pipenv
pipenv --python 3.10
```

###가상환경 실행/종료

```shell
pipenv shell
exit
```

###가상환경에 pipenv 패키지 다운

```shell
pipenv install