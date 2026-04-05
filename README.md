# MetricFlow ESG Dashboard
<img src="https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white" alt="Next.js"><img src="https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React"><img src="https://img.shields.io/badge/Tailwind%20CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind CSS"><img src="https://img.shields.io/badge/React%20Query-FF4154?style=flat-square&logo=reactquery&logoColor=white" alt="React Query"><img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"><img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"><img src="https://img.shields.io/badge/Go-00ADD8?style=flat-square&logo=go&logoColor=white" alt="Go"><img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"><img src="https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white" alt="Vercel"><img src="https://img.shields.io/badge/Render-46E3B7?style=flat-square&logo=render&logoColor=white" alt="Render">

> ⚠️ **안내사항 (Cold Start)**
> 본 프로젝트의 백엔드 서버는 무료 클라우드 인스턴스에 배포되어 운영 중입니다. 일정 시간 요청이 없으면 서버가 휴면 상태로 전환되므로, **최초 접속 시 (Cold start) 백엔드 응답까지 약 1분 정도의 대기 시간이 발생**할 수 있습니다. 

🔗 **Live Demo:** 
[https://metricflow-esg.vercel.app/](https://metricflow-esg.vercel.app/)

<video src="https://github.com/user-attachments/assets/ca395a60-4186-48ab-8748-28f1b7b4e760" autoplay loop muted playsinline width="100%">
</video>
---

## 📝 TODO

- [x] **Go 언어로 변환**: 현재 Python(FastAPI) 기반인 백엔드를 Go 언어로 포팅하여 성능 최적화 및 동시성 처리 강화 (Goroutine & Worker Pool 적용)
- [x] **대용량 스트레스 테스트**: 300만 건 데이터 대상 Go 백엔드 정밀 지표 측정 완료 (RPS 1,300+ 달성)

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

### 📈 300만 건 대용량 스트레스 테스트 지표 (Stress Test Analysis)
실제 B2B 엔터프라이즈 환경을 가정하여, 로컬 환경(SQLite)에서 데이터 집계 쿼리(GROUP BY, ORDER BY)의 성능 한계를 테스트한 지표입니다.

| 데이터 규모 | 콜드 스타트 (초기 로드) | 2회차 요청 (Materialized View 캐시) | 3회차 요청 (핫 히트) | 비고 |
| :--- | :--- | :--- | :--- | :--- |
| **5만 건** (기존) | 1,213 ms | 56.28 ms | 17.69 ms | 현재 라이브 서비스 수준 |
| **300만 건 (Python)** | 2,136.82 ms | **12.29 ms** | **7.35 ms** | 파이썬 성능 한계 측정 |
| **300만 건 (Go)** | 1,353.12 ms | **11.45 ms** | **5.12 ms** | 1,300+ RPS 이상으로 안정적 처리 |

💡 **Materialized View 도입 전략**
 
대규모 데이터를 매번 `JOIN`, `GROUP BY`로 집계하면 사용자가 늘어날수록 급격한 지연(Latency)이 발생합니다. 이를 극복하기 위해 비용이 드는 외부 인프라(Upstash Redis 등)를 추가하는 대신, 자체 데이터베이스 성능을 극대화하는 Materialized View를 아키텍처에 도입했습니다.

1. **PostgreSQL (운영 및 권장 환경):**
  DB에서 공식 지원하는 `MATERIALIZED VIEW` 문법을 활용합니다. 무거운 집계 결과를 디스크에 물리적인 테이블 형태로 저장하여, 쿼리 시 원본 테이블을 뒤지지 않고 이미 완성된 '단일 뷰 테이블'만 읽어오므로 수억 건의 데이터에서도 매우 빠른 조회 속도를 보장합니다.
2. **SQLite (로컬 벤치마크 환경):**
  **결과:** 300만 건의 대규모 트래픽 쿼리를 기존 수십 초 수준에서 단 **5.12 ms (0.005초)**로 99.7% 단축하여 B2B 엔터프라이즈 환경에서도 지연 없는 초고속 대시보드를 성공적으로 구축했습니다.
3. **Go 언어 도입을 통한 서버 자원 최적화 (Infrastructure Efficiency)**
   Python의 GIL 한계와 런타임 오버헤드를 극복하기 위해 핵심 Read API와 데이터 적재 파이프라인을 Go(Gin/GORM)로 포팅함. Goroutine을 활용한 비동기 캐시 갱신 및 Worker Pool 기반의 병렬 데이터 인제스천을 통해 동일 하드웨어 대비 처리량을 3.7배 향상시키고 메모리 사용량을 87% 절감함.

4. **사용자 경험(UX) 및 프론트엔드 렌더링 최적화**
   Next.js와 React-Query를 결합하여 데이터 패칭(Fetching) 상태를 관리하고, 불필요한 리렌더링을 억제하여 B2B 환경에 적합한 끊김 없는 대용량 데이터 시각화(Recharts) 대시보드와 모던한 Tailwind CSS 다크모드 UI를 구현함.

### 📊 Python vs Go 런타임 성능 비교 (Micro-Benchmark)
실제 로컬 환경(1,000건 샘플 데이터)에서 50명의 동시 사용자가 10초간 요청을 보냈을 때의 런타임 처리 효율 지표입니다.

| 지표 (Benchmark) | Python (FastAPI/Uvicorn) | **Go (Gin/Goroutine)** | **개선율** |
| :--- | :--- | :--- | :--- |
| **평균 응답 속도 (Latency)** | 48.2 ms | **12.4 ms** | **약 74% 단축** |
| **초당 처리량 (Max RPS)** | 1,024 RPS | **3,850 RPS** | **약 3.7배 향상** |
| **메모리 점유율 (Idle)** | ~120 MB | **~15 MB** | **87% 절감** |

> **Note:** Go의 가벼운 런타임과 동시성 모델 덕분에 300만 건의 대규모 데이터셋에서도 50명 동시 접속 시 평균 36ms의 응답 속도와 1,300 RPS 이상의 안정적인 성능을 보여줍니다.

### 🛠 기술 스택 (Tech Stack)
- **Frontend:** Next.js (App Router), React, Tailwind CSS v4, React Query, Recharts, Axios
- **Backend:** FastAPI, Python 3.12 / **Go 1.26 (Gin, GORM)**
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

# 5. 서버 실행 (Python)
uv run python main.py

# 6. 서버 실행 (Go - 권장)
cd ../backend-go
go run main.go
```

#### 🛠 3M 데이터 적재 (3M Data Ingestion - Optional)
이 과정은 스트레스 테스트를 위해 300만 건의 데이터를 생성하고 적재하고자 할 때만 필요합니다.

> ⚠️ **주의사항 (Important Notice)**
> 다음 도구들은 개발 및 테스트 환경용으로 설계되었습니다:
> - **`ingest_3m.go`**: 이 스크립트는 고속 인제스천을 위해 **기존 테이블(`companies`, `esg_metrics`)을 삭제(DROP)**하고 SQLite의 **PRAGMA 설정**을 변경합니다.
>   - **사전 요구사항:** 인제스천 스크립트가 실행 중인 서버와 **동일한 SQLite DB 파일**에 접근하는 경우, 반드시 API 서버를 **완전히 종료**해야 합니다. 기본 설정인 별도 DB(`sqlite:///./esg_3m.db`)를 사용하는 경우에는 종료할 필요가 없습니다.
>   - **보안:** 절대로 운영 환경이나 공유 데이터베이스에서 실행하지 마세요. 전용 로컬 SQLite 파일만 사용해야 합니다.
>   - **권장사항:** 실행 전에 데이터베이스 파일을 백업하고, IDE의 DB 브라우저 등 다른 프로세스가 파일을 점유하고 있지 않은지 확인하세요.
> 
> - **`ingest_3m.go`**: This script **DROPS EXISTING TABLES** (`companies` and `esg_metrics`) and modifies SQLite **PRAGMA settings** for high-speed ingestion. 
>   - **Prerequisite:** The API server must be **FULLY STOPPED** ONLY when the ingest script accesses the **same SQLite DB file** as the running server. If using the default separate DB (`sqlite:///./esg_3m.db`), stopping is not required.
>   - **Security:** NEVER run this against a production or shared database. Use a dedicated local SQLite file only.
>   - **Recommendation:** Back up your database file before execution and verify that no other process (like an IDE's DB browser) is holding the file.

```bash
# 300만 건 데이터 생성 및 적재 실행
cd backend-go/ingest
go run ingest_3m.go
```

#### Frontend 설정
```bash
# 1. 프론트엔드 폴더로 이동
cd frontend

# 2. 패키지 설치
npm install

# 3. 환경 변수 설정
# .env.local 파일을 만들고 다음을 추가하세요.
# Python 백엔드 사용 시: NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
# Go 백엔드 사용 시 (권장): NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1
NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1

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

### 📈 3M Records Large-Scale Stress Test (Stress Test Analysis)
Tested performance limits of aggregation queries (GROUP BY, ORDER BY) in a local environment (SQLite) to simulate actual B2B environments.

| Data Scope | Cold Start (Initial Load) | 2nd Request (Materialized View / Cache Table) | 3rd Request (Hot Hit) | Note |
| :--- | :--- | :--- | :--- | :--- |
| **50k Rows** (Current) | 1,213 ms | 56.28 ms | 17.69 ms | Current Live Service Level |
| **3M Rows (Python)** | 2,136.82 ms | **12.29 ms** | **7.35 ms** | Python performance limit |
| **3M Rows (Go)** | 1,353.12 ms | **11.45 ms** | **5.12 ms** | Stable processing at 1,300+ RPS |

> **Note:** Thanks to Go's lightweight runtime and concurrency model, even with a massive dataset of 3 million records, it maintains an average response time of 36ms and stable performance of over 1,300 RPS during 50 concurrent connections.

💡 **Materialized View Strategy**
 
Repeatedly running `JOIN` and `GROUP BY` aggregations on massive datasets causes severe latency as users increase. To overcome this without adding expensive external infrastructure (like Upstash Redis), we introduced **Materialized Views** into the architecture to maximize native database performance.

1. **PostgreSQL (Production & Recommended):**
    Utilizes the officially supported `MATERIALIZED VIEW` syntax. Heavy aggregation results are physically stored on disk as a table. Queries no longer scan the original tables, reading only the pre-computed 'single view table', guaranteeing extremely fast retrieval speeds even for hundreds of millions of rows.
2. **SQLite (Local Benchmark Environment):**
  **Result:** Large-scale 3M traffic queries were slashed by 99.7% from tens of seconds down to just **5.12ms (0.005 sec)** using Go's optimized runtime and pre-computed cache tables.
3. **Server Resource Optimization via Go (Infrastructure Efficiency)**
   Ported the core Read API and data ingestion pipeline to Go (Gin/GORM) to overcome Python's GIL limitations and runtime overhead. Achieved a 3.7x increase in throughput and a 87% reduction in memory usage through Goroutine-based asynchronous cache refreshing and worker pool-based parallel data ingestion.

### 📊 Python vs Go Runtime Performance (Micro-Benchmark)
Runtime efficiency measured in a local environment with 1,000 sample records and 50 concurrent users over 10 seconds.

| Metric (Benchmark) | Python (FastAPI/Uvicorn) | **Go (Gin/Goroutine)** | **Improvement** |
| :--- | :--- | :--- | :--- |
| **Avg Latency** | 48.2 ms | **12.4 ms** | **~74% Reduction** |
| **Throughput (Max RPS)** | 1,024 RPS | **3,850 RPS** | **~3.7x Increase** |
| **Memory usage (Idle)** | ~120 MB | **~15 MB** | **87% Lower** |

4. **User Experience (UX) & Frontend Rendering Optimization**
   Combined Next.js and React-Query to manage data fetching states and suppress unnecessary re-renders, delivering a seamless large-scale data visualization dashboard (Recharts) suitable for a B2B environment with a modern Tailwind CSS dark-mode UI.

### 🛠 Tech Stack
- **Frontend:** Next.js (App Router), React, Tailwind CSS v4, React Query, Recharts, Axios
- **Backend:** FastAPI, Python 3.12 / **Go 1.26 (Gin, GORM)**
- **Database:** PostgreSQL (Neon Serverless Postgres), SQLite (Local)
- **Deployment:** Render (Backend), Vercel (Frontend)

### 🚀 How to Run

#### Backend Setup
```bash
cd backend
uv sync  # or pip install -r requirements.txt
# Set DATABASE_URL in your .env file
uv run python ingest_data.py
# Run Server
uv run python main.py

# Run Server (Go - Recommended)
cd ../backend-go
go run main.go
```

#### Frontend Setup
```bash
cd frontend
npm install
# Set NEXT_PUBLIC_API_URL in .env.local
# Python: http://localhost:8000/api/v1
# Go (Recommended): http://localhost:8080/api/v1
NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1
npm run dev
```
