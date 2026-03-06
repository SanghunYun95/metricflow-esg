# Clean Architecture Structure Guidelines

이 프로젝트는 유지보수성과 확장성을 위해 **Clean Architecture** 원칙을 따릅니다.
Next.js의 App Router 기능을 활용하면서도, 비즈니스 로직을 프레임워크로부터 분리하여 독립적으로 테스트하고 관리할 수 있도록 구성합니다.

## 1. 폴더 구조 (Folder Structure)

프로젝트의 핵심 로직은 `src` 디렉토리에 위치하며, Next.js 관련 설정은 `app` 디렉토리에 위치합니다.

```
dashboard/
├── app/                  # [Frameworks & Drivers] Next.js App Router (진입점)
│   ├── (auth)/           # 라우팅 그룹 (로그인, 회원가입 등)
│   ├── api/              # API Route Handlers (Controller 역할)
│   ├── layout.tsx        # 최상위 레이아웃
│   └── page.tsx          # 메인 페이지
│
├── src/                  # 핵심 비즈니스 로직 (프레임워크 독립적)
│   ├── domain/           # [Enterprise Business Rules] 가장 안쪽 레이어
│   │   ├── entities/     # 핵심 데이터 모델 (Types, Interfaces, Classes)
│   │   └── errors/       # 도메인 에러 정의 (예: UserNotFoundError)
│   │
│   ├── application/      # [Application Business Rules] 유스케이스 레이어
│   │   ├── use-cases/    # 비즈니스 로직의 단위 (e.g., CreateUser, GetPosts)
│   │   ├── ports/        # 외부 의존성(DB, API)을 위한 인터페이스 정의 (In/Out Ports)
│   │   └── dtos/         # 계층 간 데이터 전송 객체 (Input/Output DTO)
│   │
│   ├── infrastructure/   # [Interface Adapters] 구현체 레이어
│   │   ├── repositories/ # application/ports의 구현체 (Supabase, Prisma 등)
│   │   ├── services/     # 외부 서비스 구현체 (e.g., EmailService, PaymentService)
│   │   └── config/       # 환경 변수, DB 설정 파일
│   │
│   └── presentation/     # [Interface Adapters] UI 관련 레이어
│       ├── components/   # UI 컴포넌트
│       │   ├── ui/       # 재사용 가능한 기본 UI (예: 버튼, 입력창 - Shadcn UI)
│       │   └── domain/   # 도메인 특화 컴포넌트 (예: UserCard, PostList)
│       ├── hooks/        # 커스텀 훅 (ViewModel 역할)
│       └── utils/        # UI 포맷팅 및 헬퍼 함수
│
├── public/               # 정적 파일 (이미지, 폰트 등)
└── ...
```

---

## 2. 레이어별 역할 및 규칙 (Layer Responsibilities)

### 1) Domain Layer (Enterprise Business Rules)
시스템의 핵심 업무 규칙과 데이터를 정의합니다. 이 레이어는 **외부의 어떤 라이브러리나 프레임워크에도 의존하지 않아야 합니다**.
- **Entities**: 데이터 구조와 비즈니스 규칙을 포함하는 객체나 타입입니다.
- **Errors**: 도메인에서 발생할 수 있는 에러를 정의합니다.

### 2) Application Layer (Application Business Rules)
애플리케이션이 수행해야 하는 작업(Use Case)을 정의하고 흐름을 제어합니다.
- **Use Cases**: 사용자의 요청을 처리하는 구체적인 비즈니스 로직입니다. (예: `CreateUser`, `GetPostList`)
- **Ports**: 데이터를 저장하거나 외부 서비스와 통신하기 위한 **인터페이스**를 정의합니다. 실제 구현 방법(DB 종류 등)은 알지 못합니다.
- **DTOs (Data Transfer Objects)**: 레이어 간 데이터를 주고받을 때 사용하는 객체입니다.

### 3) Infrastructure Layer (Interface Adapters)
Application 레이어에서 정의한 인터페이스(Ports)를 **실제로 구현**하는 곳입니다.
- **Repositories**: DB(Supabase, Prisma 등)와 통신하여 데이터를 가져오거나 저장하는 코드가 위치합니다.
- **Services**: 이메일 발송, 결제 시스템 등 외부 API와의 통신을 구현합니다.
- **Config**: 환경 변수나 라이브러리 설정을 관리합니다.

### 4) Presentation Layer / App (Frameworks & Drivers)
사용자와 상호작용하고 화면을 그리는 역할을 합니다. Next.js의 기능을 적극적으로 활용합니다.
- **UI Components**: 화면에 보여지는 요소들입니다.
- **App Router (`app/`)**: URL 라우팅을 담당하며, **Server Components**나 **API Routes**가 Controller 역할을 수행하여 Use Case를 호출합니다.

---

## 3. 의존성 규칙 (Dependency Rule)

**"소스 코드의 의존성은 반드시 안쪽(Domain 방향)으로만 향해야 한다."**

1.  **Domain**은 누구에게도 의존하지 않습니다. (No dependencies)
2.  **Application**은 **Domain**에만 의존합니다.
3.  **Infrastructure**와 **Presentation**은 **Application**과 **Domain**에 의존합니다.

### 중요 원칙
- **Infrastructure(DB 등) 코드가 Application이나 Domain 코드에 직접 등장해서는 안 됩니다.**
    - 대신 Application 층에 정의된 `Interface(Port)`를 사용하고, 실행 시점에 Infrastructure의 `Implementation(구현체)`를 주입(Injection)받아 사용합니다.
- UI 컴포넌트에서 직접 DB 쿼리를 작성하지 않고, 되도록 **Use Case**를 거쳐 데이터를 가져오도록 합니다.

## 4. 개발 흐름 예시 (Workflow)

새로운 기능(예: "글 작성")을 추가할 때의 권장 순서:

1.  **Domain**: `Post` 엔티티와 필요한 타입 정의.
2.  **Application (Port)**: `PostRepository` 인터페이스 정의 (예: `save(post: Post): Promise<void>`).
3.  **Application (Use Case)**: `CreatePostUseCase` 작성. `PostRepository` 인터페이스를 사용하여 로직 구현.
4.  **Infrastructure**: `SupabasePostRepository` 구현. `PostRepository` 인터페이스를 implement하여 실제 Supabase DB에 저장하는 코드 작성.
5.  **Presentation/App**: Next.js Server Action이나 API Route에서 `CreatePostUseCase`를 호출하고, `SupabasePostRepository` 인스턴스를 주입. UI와 연결.