# MetricFlow ESG Dashboard

🔗 **Live Demo:** [https://metricflow-esg.vercel.app/](https://metricflow-esg.vercel.app/)

## 🇰🇷 프로젝트 소개 (Project Overview)
이 프로젝트는 S&P 500 기업의 ESG 데이터를 분석하고 시각화하는 대시보드입니다. 대용량 데이터의 안정적인 처리와 사용자 경험 최적화에 중점을 두고 개발되었습니다.

### 📊 데이터 출처 (Data Source)
- **기업 데이터:** [Kaggle - ESG Sustainability Reports of S&P 500 Companies](https://www.kaggle.com/datasets/jaidityachopra/esg-sustainability-reports-of-s-and-p-500-companies)
- **시계열 데이터:** 51,900건의 ESG 지표 데이터는 테스트 및 성능 최적화 검증을 위해 목업(Mockup)으로 합성되었습니다.

### 🌟 주요 성과 (Key Achievements)

1. **대용량 데이터 파이프라인 구축 및 DB 최적화**
   5만 건 이상의 S&P 500 ESG Raw 데이터(`preprocessed_content.csv`)를 Pandas로 정제하여 PostgreSQL(Neon)에 벌크 인서트(Bulk Insert)하고, Sector와 Company 컬럼에 복합 인덱스(Composite Index)를 설계하여 풀 테이블 스캔(Full Table Scan)을 방지함.

2. **백엔드 집계 쿼리 튜닝 (API 응답 속도 단축)**
   FastAPI 백엔드에서 모든 데이터를 메모리에 올려 계산하는 대신, SQLAlchemy의 `func.avg`와 `GROUP BY`를 활용한 데이터베이스 레벨의 집계 쿼리로 튜닝하여 메모리 초과(OOM)를 방지하고 대시보드 로딩 지연을 해결함.

3. **사용자 경험(UX) 및 프론트엔드 렌더링 최적화**
   Next.js와 React-Query를 결합하여 데이터 패칭(Fetching) 상태를 관리하고, 불필요한 리렌더링을 억제하여 B2B 환경에 적합한 끊김 없는 대용량 데이터 시각화(Recharts) 대시보드와 모던한 Tailwind CSS 다크모드 UI를 구현함.

### 🛠 기술 스택 (Tech Stack)
- **Frontend:** Next.js (App Router), React, Tailwind CSS v4, React Query, Recharts, Axios
- **Backend:** FastAPI, Uvicorn, SQLAlchemy, Pydantic, Python 3.12
- **Database:** PostgreSQL (Neon Serverless Postgres)
- **Deployment:** Render (Backend), Vercel (Frontend)

### 🚀 실행 방법 (How to Run)

#### Backend 설정
```bash
# 1. 백엔드 폴더로 이동
cd backend

# 2. 가상 환경 설정 및 패키지 설치
uv sync  # 또는 pip install -r requirements.txt

# 3. 환경 변수 설정
# .env 파일을 만들고 DATABASE_URL 설정을 추가하세요.
# DATABASE_URL="postgresql://user:password@host/dbname"

# 4. 데이터베이스 마이그레이션 및 데이터 주입 (최초 1회)
uv run python ingest_data.py

# 5. 서버 실행
uv run python main.py
```

#### Frontend 설정
```bash
# 1. 프론트엔드 폴더로 이동
cd frontend

# 2. 패키지 설치
npm install

# 3. 환경 변수 설정
# .env.local 파일을 만들고 다음을 추가하세요.
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# 4. 개발 서버 실행
npm run dev
```

---

## 🇺🇸 Project Overview
This project is a dashboard that analyzes and visualizes ESG data for S&P 500 companies. It focuses on stable processing of large-scale data and optimizing the user experience.

### 📊 Data Source
- **Enterprise Data:** [Kaggle - ESG Sustainability Reports of S&P 500 Companies](https://www.kaggle.com/datasets/jaidityachopra/esg-sustainability-reports-of-s-and-p-500-companies)
- **Time-Series Data:** 51,900 rows of ESG metrics were synthetically mocked for testing and performance optimization verification.

### 🌟 Key Achievements

1. **Large-Scale Data Pipeline & DB Optimization**
   Refined over 50,000 rows of S&P 500 ESG raw data (`preprocessed_content.csv`) using Pandas, bulk-inserted it into PostgreSQL (Neon), and designed a composite index on Sector and Company columns to prevent full table scans.
   
2. **Backend Aggregation Query Tuning (API Latency Reduction)**
   Rather than loading all data into memory for calculation in the FastAPI backend, tuned aggregation queries at the database level using SQLAlchemy's `func.avg` and `GROUP BY`. This prevented Out-Of-Memory (OOM) errors and resolved dashboard loading delays.

3. **User Experience (UX) & Frontend Rendering Optimization**
   Combined Next.js and React-Query to manage data fetching states and suppress unnecessary re-renders, delivering a seamless large-scale data visualization dashboard (Recharts) suitable for a B2B environment with a modern Tailwind CSS dark-mode UI.

### 🛠 Tech Stack
- **Frontend:** Next.js (App Router), React, Tailwind CSS v4, React Query, Recharts, Axios
- **Backend:** FastAPI, Uvicorn, SQLAlchemy, Pydantic, Python 3.12
- **Database:** PostgreSQL (Neon Serverless Postgres)
- **Deployment:** Render (Backend), Vercel (Frontend)

### 🚀 How to Run

#### Backend Setup
```bash
cd backend
uv sync  # or pip install -r requirements.txt
# Set DATABASE_URL in your .env file
uv run python ingest_data.py
uv run python main.py
```

#### Frontend Setup
```bash
cd frontend
npm install
# Set NEXT_PUBLIC_API_URL in .env.local
npm run dev
```
