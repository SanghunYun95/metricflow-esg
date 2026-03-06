---
trigger: always_on
---

# CloudNote Service Context
## 1. Service Overview
**Name**: CloudNote
**Tagline**: 생각을 정리하는 새로운 방법 (The new way to organize thoughts)
**Value Proposition**:
CloudNote is a cloud-based AI note-taking service chosen by 100,000 users. It allows users to safely manage complex ideas in the cloud, featuring AI summarization, multi-device synchronization, and secure storage.
## 2. Core Features
- **AI-Powered Note Taking**:
  - AI summarization of notes (displayed in usage stats and feature lists).
  - AI search capabilities (Pro plan).
- **Cross-Platform Synchronization**:
  - Real-time sync across devices (Pro/Enterprise).
  - Offline access support.
- **Organization**:
  - Folder-based organization.
  - Category tagging (Work, Personal, Idea, Study).
  - Recent activity tracking.
- **Subscription Models**:
  - **Free**: 100 notes, Basic AI summary, 1GB storage.
  - **Pro (Recommended)**: Unlimited notes, Advanced AI, 10GB storage, Team sharing, Offline access.
  - **Enterprise**: All Pro features, Unlimited storage, Dedicated support, SSO.
## 3. User Flows
### Onboarding & Auth
- **Landing Page**: Showcases value prop, features, and pricing tiers.
- **Authentication**:
  - Email/Password login.
  - Social Login: Google, Kakao.
  - "Keep me logged in" functionality.
### Core Workflow
- **Dashboard**:
  - Overview of subscription status (Pro/Free).
  - Usage statistics (Note count, Storage, AI usage).
  - Recent activity feed (New notes, AI summaries, Folders, Sharing).
  - Quick navigation to Home, My Notes, Settings, Subscription.
- **Note Management**:
  - List view of notes with timestamps and summaries.
  - Rich text editor for creating/editing notes.
  - Categorization via dropdown (Work, Personal, etc.).
  - Modal for creating new notes.
### Subscription & Payment
- **Plan Selection**: Detailed comparison of Free, Pro, and Enterprise tiers.
- **Payment**:
  - Payment method selection: Credit Card, KakaoPay, NaverPay, TossPay.
  - Order summary and agreement checklists.
- **Confirmation**: Success screen with order details and next steps.
## 4. Design System & Aesthetics
**Theme**: Clean, professional SaaS aesthetic with support for Light and Dark modes.
**Typography**:
- Font Family: `Inter`, `Noto Sans KR`.
- Headings: Bold, clean sans-serif.
**Color Palette**:
- **Primary**: Blue (`#137fec`, `#2563eb`) - Trust, Clarity, Tech.
- **Background**: Light (`#f6f7f8`), Dark (`#101922`).
- **Surface**: White (`#ffffff`), Dark Surface (`#1c2632`).
- **Accents**: Kakao Yellow (`#FEE500`), Success Green (`#22c55e`), Error Red.
## 5. Page Breakdown
| Page | File | Description |
|------|------|-------------|
| **Landing** | `landing.html` | Hero section with cloud visuals, feature highlights, and pricing cards. |
| **Auth** | `auth.html` | Split layout: Brand/Marketing on left, Login/Signup form on right. Background animations. |
| **Dashboard** | `dashboard.html` | Sidebar navigation, Subscription status card, Usage progress bars, Activity feed. |
| **Note** | `note.html` | Sidebar note list, Main editor area, "New Note" modal with category selection. |
| **Payment** | `payment.html` | Plan comparison, Payment method grid, Order summary, Terms agreement. |
| **Success** | `payment-done.html` | Celebration state, Order receipt details, CTA to Dashboard. |