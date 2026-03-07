# MetricFlow ESG Dashboard

> ⚠️ **안내사항 (Cold Start)**
> 본 프로젝트의 백엔드 서버는 무료 클라우드 인스턴스에 배포되어 운영 중입니다. 일정 시간 요청이 없으면 서버가 휴면 상태로 전환되므로, **최초 접속 시 (Cold start) 백엔드 응답까지 약 1분 정도의 대기 시간이 발생**할 수 있습니다. 

🔗 **Live Demo:** [https://metricflow-esg.vercel.app/](https://metricflow-esg.vercel.app/)

## 🇰🇷 프로젝트 소개 (Project Overview)
이 프로젝트는 S&P 500 기업의 ESG 데이터를 분석하고 시각화하는 대시보드입니다. 대용량 데이터의 안정적인 처리와 사용자 경험 최적화에 중점을 두고 개발되었습니다.

### 📊 데이터 출처 (Data Source)
- **기업 데이터:** [Kaggle - ESG Sustainability Reports of S&P 500 Companies](https://www.kaggle.com/datasets/jaidityachopra/esg-sustainability-reports-of-s-and-p-500-companies)
- **시계열 데이터:** 무료 클라우드 서버의 한계로 인해 배포된 환경에는 약 5만 건의 데이터만 운영 중이나, 로컬 환경에서는 **3,000,000건(3M)** 모델을 자체 적재하여 대용량 트래픽 튜닝 및 스트레스 테스트를 완료했습니다.

### 🌟 주요 성과 (Key Achievements)

1. **대용량 데이터 파이프라인 구축 및 DB 최적화**
   5만 건 이상의 S&P 500 ESG Raw 데이터(`preprocessed_content.csv`)를 Pandas로 정제하여 PostgreSQL(Neon)에 벌크 인서트(Bulk Insert)하고, Sector와 Company 컬럼에 복합 인덱스(Composite Index)를 설계하여 풀 테이블 스캔(Full Table Scan)을 방지함.

2. **백엔드 집계 쿼리 튜닝 (API 응답 속도 단축)**
   FastAPI 백엔드에서 모든 데이터를 메모리에 올려 계산하는 대신, SQLAlchemy의 `func.avg`와 `GROUP BY`를 활용한 데이터베이스 레벨의 집계 쿼리로 튜닝하여 메모리 초과(OOM)를 방지하고 대시보드 로딩 지연을 해결함.

### 📈 대용량 트래픽 스트레스 테스트 및 튜닝 지표 (Stress Test Benchmark)
실제 B2B 환경(대규모 데이터)을 가정하여 로컬 환경(SQLite)에서 동일한 집계 쿼리(GROUP BY, ORDER BY)의 성능 한계를 테스트했습니다.

| 데이터 규모 | 콜드 스타트 (초기 로드) | 2회차 요청 (Materialized View 캐시) | 3회차 요청 (핫 히트) | 비고 |
| :--- | :--- | :--- | :--- | :--- |
| **5만 건** (기존) | 1,213 ms | 56.28 ms | 17.69 ms | 현재 라이브 서비스 수준 |
| **300만 건** | 2,136.82 ms | **12.29 ms** | **7.35 ms** | 10ms 이하의 쾌적한 속도 달성 |

💡 **Materialized View 도입 전략**
 
대규모 데이터를 매번 `JOIN`, `GROUP BY`로 집계하면 사용자가 늘어날수록 급격한 지연(Latency)이 발생합니다. 이를 극복하기 위해 비용이 드는 외부 인프라(Upstash Redis 등)를 추가하는 대신, 자체 데이터베이스 성능을 극대화하는 Materialized View를 아키텍처에 도입했습니다.

1. **PostgreSQL (운영 및 권장 환경):**
  DB에서 공식 지원하는 `MATERIALIZED VIEW` 문법을 활용합니다. 무거운 집계 결과를 디스크에 물리적인 테이블 형태로 저장하여, 쿼리 시 원본 테이블을 뒤지지 않고 이미 완성된 '단일 뷰 테이블'만 읽어오므로 수억 건의 데이터에서도 매우 빠른 조회 속도를 보장합니다.
2. **SQLite (로컬 벤치마크 환경):**
  **결과:** 300만 건의 대규모 트래픽 쿼리를 기존 수십 초 수준에서 단 7ms(0.007초)로 99.7% 단축하여 B2B 엔터프라이즈 환경에서도 지연 없는 초고속 대시보드를 성공적으로 구축했습니다.
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
- **Time-Series Data:** Due to the limitations of free cloud servers, the deployed environment operates with around 50,000 rows of data. However, in the local environment, a custom **3,000,000 (3M) row** model was populated to successfully complete large-scale traffic tuning and stress testing.

### 🌟 Key Achievements

1. **Large-Scale Data Pipeline & DB Optimization**
   Refined over 50,000 rows of S&P 500 ESG raw data (`preprocessed_content.csv`) using Pandas, bulk-inserted it into PostgreSQL (Neon), and designed a composite index on Sector and Company columns to prevent full table scans.
   
2. **Backend Aggregation Query Tuning (API Latency Reduction)**
   Rather than loading all data into memory for calculation in the FastAPI backend, tuned aggregation queries at the database level using SQLAlchemy's `func.avg` and `GROUP BY`. This prevented Out-Of-Memory (OOM) errors and resolved dashboard loading delays.

### 📈 Large-scale Traffic Stress Test & Tuning Metrics
Tested performance limits of aggregation queries (GROUP BY, ORDER BY) in a local environment (SQLite) to simulate actual B2B environments.

| Data Scope | Cold Start (Initial Load) | 2nd Request (Materialized View / Cache Table) | 3rd Request (Hot Hit) | Note |
| :--- | :--- | :--- | :--- | :--- |
| **50k Rows** (Current) | 1,213 ms | 56.28 ms | 17.69 ms | Current Live Service Level |
| **3M Rows** | 2,136.82 ms | **12.29 ms** | **7.35 ms** | Sub-10ms lightning-fast response achieved |

💡 **Materialized View Strategy**
 
Repeatedly running `JOIN` and `GROUP BY` aggregations on massive datasets causes severe latency as users increase. To overcome this without adding expensive external infrastructure (like Upstash Redis), we introduced **Materialized Views** into the architecture to maximize native database performance.

1. **PostgreSQL (Production & Recommended):**
    Utilizes the officially supported `MATERIALIZED VIEW` syntax. Heavy aggregation results are physically stored on disk as a table. Queries no longer scan the original tables, reading only the pre-computed 'single view table', guaranteeing extremely fast retrieval speeds even for hundreds of millions of rows.
2. **SQLite (Local Benchmark Environment):**
  **Result:** Large-scale 3M traffic queries were slashed by 99.7% from tens of seconds down to just 7ms (0.007 sec), successfully building a zero-latency ultra-fast dashboard suitable for enterprise B2B environments.
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
