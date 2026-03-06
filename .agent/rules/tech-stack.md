# Tech Stack & Rules

이 프로젝트는 **Next.js**와 **Supabase**를 기반으로 하며, 다음과 같은 기술 스택 규칙을 따릅니다.

## 1. Next.js (App Router)

### 버전 및 환경
- **Next.js 14+ (App Router)** 사용을 원칙으로 합니다.
- `src/` 디렉토리를 활용하여 비즈니스 로직과 라우팅을 분리합니다.

### 컴포넌트 원칙 (Server vs Client)
- **기본적으로 Server Component**로 작성합니다.
    - 데이터 페칭, 민감한 로직(API Key 사용 등)은 반드시 서버에서 처리합니다.
    - HTML을 렌더링하고 클라이언트로 전송되는 번들 사이즈를 최소화합니다.
- **상호작용이 필요한 경우에만 Client Component**로 전환합니다.
    - `useState`, `useEffect`, `onClick` 등의 이벤트 핸들러가 필요한 경우 파일 최상단에 `'use client'`를 선언합니다.
    - 가능한 한 Leaf Component(말단 컴포넌트)만 Client Component로 만들어서 서버 렌더링 이점을 유지합니다.

### 데이터 페칭 (Data Fetching)
- **Server Components**: `async/await`를 사용하여 직접 데이터를 페칭합니다. `fetch` API의 캐싱 기능을 활용하거나, Supabase Server Client를 사용합니다.
- **Client Components**: 필요한 경우 `Suspense`와 함께 사용하거나, React Query(TanStack Query) 등을 도입하여 상태를 관리할 수 있습니다. (현재 프로젝트 구조에 따라 결정)
- **API Routes**: `app/api/` 폴더 내에 정의하며, 외부 서비스와의 통신이나 프록시 역할이 필요할 때 사용합니다.

### Server Actions
- 폼 제출이나 데이터 변형(Mutation) 작업은 **Server Actions**를 적극 활용합니다.
- 별도의 API 라우트를 만들지 않고도 함수 형태로 서버 로직을 직접 호출할 수 있어 생산성이 높습니다.
- 보안을 위해 Server Action 내에서 반드시 입력값 검증(Validation)과 권한 확인(Authentication/Authorization)을 수행해야 합니다.

---

## 2. Supabase

### 클라이언트 구성 (Clients)
Supabase는 실행 환경에 따라 적절한 클라이언트를 사용해야 합니다.
- **Server Client**: Server Components, Server Actions, API Routes, Middleware에서 사용합니다. (쿠키 조작 가능)
- **Browser Client**: Client Components에서 사용합니다.

### 데이터베이스 접근 (Database Access)
- **Type Safety**: `database.types.ts` 파일을 생성하여 Supabase 테이블 스키마에 대한 타입을 자동으로 생성하고 관리합니다.
- **RLS (Row Level Security)**: 모든 테이블에 RLS를 활성화(Enable)하는 것을 기본 원칙으로 합니다. 서비스 로직에서 권한을 체크하기보다, DB 수준에서 정책(Policy)으로 데이터 접근을 제어합니다.

### 인증 (Authentication)
- Supabase Auth를 사용하며, Next.js Middleware를 통해 세션을 관리하고 보호된 라우트로의 접근을 제어합니다.
- 로그인/회원가입 상태 관리는 Supabase의 `onAuthStateChange` 이벤트를 활용하거나, Next.js Auth Helper를 사용합니다.

---

## 3. 스타일링 (Styling)

- **Tailwind CSS**를 기본으로 사용합니다.
- 컴포넌트 라이브러리는 **Shadcn UI** (Radix UI 기반)를 사용하여 일관된 디자인 시스템을 구축합니다.
- 복잡한 스타일링이 필요한 경우, Tailwind의 유틸리티 클래스 조합보다는 `class-variance-authority (cva)` 등을 활용하여 변형(Variant)을 관리합니다.

## 4. 언어 및 린팅 (Language & Linting)

- **TypeScript**를 엄격하게 사용합니다 (`noImplicitAny: true`).
- ESLint와 Prettier 설정을 준수하여 코드 스타일을 통일합니다.
- `import` 경로는 절대 경로(`@/`) 사용을 권장합니다.
