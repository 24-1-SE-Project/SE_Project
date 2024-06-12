# 개인 사진 일기

## 소개
2024년 1학기 소프트웨어 공학 및 설계 프로젝트 / 개인 사진 일기

## 설치 및 실행 방법
1. 리포지토리를 클론합니다:

2. 가상환경을 만들고 활성화합니다:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows에서는 `venv\Scripts\activate`
    ```

3. 필요한 패키지를 설치합니다:
    ```bash
    pip install Flask
    ```

4. 데이터베이스를 설정합니다:
    ```bash
    flask shell
    from app import get_db
    db = get_db()
    db.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    db.execute('''
    CREATE TABLE photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        keyword TEXT NOT NULL,
        filename TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    db.execute('''
    CREATE TABLE messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        recipient_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        FOREIGN KEY (sender_id) REFERENCES users (id),
        FOREIGN KEY (recipient_id) REFERENCES users (id)
    )
    ''')
    db.commit()
    exit()
    ```

5. 업로드 폴더를 생성합니다:
    ```bash
    mkdir -p static/uploads
    ```

6. 서버를 실행합니다:
    ```bash
    flask run
    ```

7. 웹 브라우저에서 `http://127.0.0.1:5000` 에 접속합니다.

## 기능
- 회원 가입, 로그인 및 로그아웃
- 사진 업로드, 수정 및 보기
- 키워드로 사진 검색
- 사용자 간 메시지 전송

## 기여 방법
프로젝트에 기여하려면, 포크를 하고 풀 리퀘스트를 보내주세요.