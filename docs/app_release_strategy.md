# PilaMatch 앱스토어 출시 전략

**작성일**: 2026-02-28
**버전**: 1.0
**대상**: Apple App Store (iOS) + Google Play Store (Android)
**참조**: PRD v2, CLAUDE.md, store-description-ko.md

---

## 목차

1. [현재 상태 진단](#1-현재-상태-진단)
2. [전략 선택지 비교](#2-전략-선택지-비교)
3. [Capacitor 통합 상세 계획](#3-capacitor-통합-상세-계획)
   - Phase 1: Mac 빌드 환경 구축
   - Phase 2: Capacitor 통합
   - Phase 3: 코드 수정 필요 사항
   - Phase 4: 앱스토어/플레이스토어 출시 준비물
   - Phase 5: 결제 관련 중대 이슈 (Apple 30%)
   - Phase 6: 빌드 & 배포 파이프라인
   - Phase 7: 앱 심사 대비 체크리스트
   - Phase 8: 출시 타임라인
4. [즉시 실행 가능한 작업 (WSL2에서)](#4-즉시-실행-가능한-작업-wsl2에서)
5. [리스크 & 대응 방안](#5-리스크--대응-방안)

---

## 1. 현재 상태 진단

### 기술 스택 현황

| 구성 요소 | 현재 상태 | 앱스토어 대응 상태 | 필요 작업 |
|-----------|----------|-------------------|----------|
| **프레임워크** | Next.js 16.1.6 + React 19.2.3 | WebView 래핑 필요 | Capacitor 통합 |
| **UI 라이브러리** | shadcn/ui + Tailwind CSS v4 | 모바일 반응형 부분 대응 | iOS HIG 가이드라인 적합성 검토 |
| **빌드 출력** | `output: "standalone"` (Docker 서버 렌더링) | Static export 필요 | `output: "export"` 전환 |
| **인증 방식** | BFF 패턴 (Next.js API Routes + httpOnly cookie) | 네이티브 앱에서 작동 불가 | Direct API + Secure Storage 전환 |
| **API 프록시** | Next.js `rewrites` (`/api/v1/:path*` -> FastAPI) | 네이티브 앱에서 작동 불가 | Direct API URL 분기 |
| **결제** | Toss Payments SDK (`@tosspayments/payment-sdk`) | 앱 내 결제 이슈 (Apple IAP 정책) | 결제 유형별 분리 전략 |
| **PWA** | 기본 manifest.json (아이콘 2개, 서비스워커 없음) | iOS App Store 등록 불가 | Capacitor 네이티브 래핑 |
| **Push 알림** | 미구현 | 앱스토어 기본 기대 기능 | FCM + APNs 연동 |
| **패키지 매니저** | pnpm | Capacitor 호환 | 호환 문제 없음 |
| **개발 환경** | WSL2 (Linux) | iOS 빌드 불가 | Mac 환경 필요 |
| **개인정보처리방침** | `docs/privacy-policy-ko.md` (작성 완료) | URL 배포 필요 | 웹 호스팅 |
| **이용약관** | `docs/terms-of-service-ko.md` (작성 완료) | URL 배포 필요 | 웹 호스팅 |
| **앱 설명** | `docs/store-description-ko.md` (작성 완료) | 즉시 사용 가능 | 스크린샷 추가 |

### BFF 인증 패턴 상세 (전환 대상)

현재 인증 플로우는 Next.js 서버 사이드에 의존하고 있어 네이티브 앱에서 작동하지 않는다.

```
[현재 - 웹 BFF 패턴]
Browser → POST /api/auth/login (Next.js Route Handler)
       → Next.js가 FastAPI /api/v1/auth/login 호출
       → 받은 JWT를 httpOnly cookie로 설정
       → 이후 요청 시 middleware가 cookie에서 토큰 추출 → Authorization header 주입

[변경 필요 - 네이티브 Direct 패턴]
Native App → POST https://api.pilamatch.com/api/v1/auth/login (FastAPI 직접)
          → JWT를 Capacitor Secure Storage에 저장
          → 이후 요청 시 Storage에서 토큰 꺼내 Authorization header에 직접 설정
```

### 결제 현황 (전환 분석 대상)

| 결제 유형 | 현재 구현 | 금액 | Apple 정책 분류 | 전환 필요 여부 |
|-----------|----------|------|----------------|--------------|
| **에스크로 (수업료)** | Toss Payments | 계약별 상이 | 실물 서비스 중개 | Toss 유지 가능 |
| **보증금** | Toss Payments | 50,000원 | 서비스 보증금 | Toss 유지 가능 |
| **프리미엄 구독** | Toss Payments (월 자동결제) | 9,900원/월 | 디지털 콘텐츠/기능 언락 | **IAP 전환 필수** |

---

## 2. 전략 선택지 비교

### Option A: Capacitor (추천)

| 항목 | 내용 |
|------|------|
| **개요** | Ionic Capacitor로 기존 Next.js 앱을 네이티브 WebView로 래핑 |
| **코드 재사용률** | 약 90% (UI/비즈니스 로직 전체 재사용) |
| **예상 기간** | 2-3주 (빌드 환경 구축 포함 4-5주) |
| **러닝 커브** | 낮음 (웹 개발자 기준) |
| **네이티브 접근** | 플러그인으로 카메라, 푸시, 생체인증 등 사용 가능 |
| **성능** | WebView 기반이나 일반적인 비즈니스 앱에 충분 |
| **빌드 요구사항** | iOS: Mac + Xcode, Android: Android Studio |
| **유지보수** | 웹 코드 변경 시 앱도 자동 반영 (sync 후 재빌드) |
| **앱스토어 심사** | WebView만으로는 거절 위험 있음 → 네이티브 기능 추가 필수 |

**추천 근거**: PilaMatch는 콘텐츠/폼 중심의 비즈니스 앱으로, 복잡한 애니메이션이나 3D 렌더링이 필요하지 않다. 기존 Next.js + shadcn/ui 코드를 90% 이상 재사용할 수 있어 개발 비용 대비 효율이 가장 높다.

### Option B: React Native (Expo)

| 항목 | 내용 |
|------|------|
| **개요** | Expo + React Native로 UI를 완전히 재작성 |
| **코드 재사용률** | 약 30-40% (비즈니스 로직, API 클라이언트, 타입 재사용) |
| **예상 기간** | 6-8주 |
| **러닝 커브** | 중간-높음 (React Native 컴포넌트, 네비게이션, 스타일링 학습) |
| **네이티브 접근** | 직접적인 네이티브 API 접근 가능 |
| **성능** | WebView보다 우수 (네이티브 렌더링) |
| **빌드 요구사항** | Expo EAS Build로 클라우드 빌드 가능 (Mac 불필요) |
| **유지보수** | 웹/앱 코드 이중 관리 필요 |
| **앱스토어 심사** | 네이티브 앱으로 인정 → 심사 통과 용이 |

**비추천 근거**: UI 전체 재작성이 필요하여 MVP 단계의 1인 개발자에게 부담이 크다. shadcn/ui 컴포넌트를 전부 React Native 컴포넌트로 교체해야 하며, 이후 웹과 앱을 이중으로 유지보수해야 한다.

### Option C: PWA 강화

| 항목 | 내용 |
|------|------|
| **개요** | 서비스워커, 오프라인 캐싱, 설치 프롬프트 등 PWA 기능 완성 |
| **코드 재사용률** | 100% (추가 코드 작업만) |
| **예상 기간** | 1주 |
| **러닝 커브** | 낮음 |
| **네이티브 접근** | 제한적 (푸시는 Web Push API로 가능, 카메라 등 브라우저 API만) |
| **성능** | 브라우저 엔진 의존 |
| **빌드 요구사항** | 기존 환경 그대로 |
| **유지보수** | 웹 코드 하나만 관리 |
| **앱스토어 심사** | Google Play: TWA로 등록 가능 / **Apple App Store: 등록 불가** |

**비추천 근거**: iOS App Store에 등록할 수 없어 한국 시장의 약 40%를 포기해야 한다. 또한 iOS Safari에서 Web Push, 백그라운드 동기화 등 핵심 기능이 제한적이다.

### 선택지 요약 비교

```
                ┌─────────────────────────────────────────────────────┐
                │              전략 비교 매트릭스                      │
                ├──────────┬────────────┬─────────────┬───────────────┤
                │          │ Capacitor  │ React Native│ PWA 강화      │
                │          │  (추천)     │  (Expo)     │               │
                ├──────────┼────────────┼─────────────┼───────────────┤
                │ 개발 기간 │  2-3주     │  6-8주      │  1주          │
                │ 코드 재사용│  ~90%     │  ~35%       │  100%         │
                │ iOS 출시  │  가능      │  가능       │  불가          │
                │ Android  │  가능      │  가능       │  TWA로 가능    │
                │ 네이티브  │  플러그인   │  직접 접근   │  제한적        │
                │ 성능     │  충분      │  우수       │  브라우저 의존  │
                │ 유지보수  │  단일 코드  │  이중 관리   │  단일 코드     │
                │ Mac 필요  │  iOS만     │  EAS 대체   │  불필요        │
                └──────────┴────────────┴─────────────┴───────────────┘
```

---

## 3. Capacitor 통합 상세 계획

### Phase 1: Mac 빌드 환경 구축

#### Mac 사양 요구사항

| 항목 | 최소 사양 | 권장 사양 |
|------|----------|----------|
| **칩셋** | Apple M1 | Apple M2 이상 |
| **RAM** | 8GB | 16GB |
| **저장소** | 256GB SSD (Xcode만 약 35GB) | 512GB SSD |
| **macOS** | Ventura 13.0+ | Sonoma 15.0+ |
| **Xcode** | 15.0+ | 16.0+ (최신 iOS SDK) |
| **용도** | iOS 빌드 전용 | iOS 빌드 + Android 빌드 + 시뮬레이터 테스트 |

#### Mac이 없는 경우 대안

| 대안 | 월 비용 | 장점 | 단점 | 추천도 |
|------|---------|------|------|--------|
| **Mac mini 구매 (M2)** | 0원 (일시불 ~80만원) | 완전한 제어, 장기적 비용 효율 | 초기 투자 비용 | 강력 추천 |
| **MacInCloud** | $30-50/월 | 즉시 사용 가능, 원격 접속 | 레이턴시, 파일 전송 불편 | 단기 대안 |
| **GitHub Actions macOS runner** | 무료 (Public) / 분당 과금 (Private) | CI/CD 통합, 자동화 | 디버깅 어려움, 시뮬레이터 불가 | 빌드 전용 |
| **Codemagic** | 무료 500분/월, $95/월 (Pro) | Capacitor/Ionic 최적화, 코드 서명 관리 | 비용, 커스터마이징 한계 | 추천 |
| **Bitrise** | 무료 300크레딧/월 | 모바일 CI/CD 특화 | 비용 | 대안 |

> **권장**: 장기 운영을 고려하면 Mac mini M2 구매가 가장 경제적이다. 초기에는 Codemagic 무료 플랜으로 시작하고, 출시 후 Mac mini를 구매하는 단계적 접근도 가능하다.

#### Mac 초기 셋업 스크립트

```bash
#!/bin/bash
# PilaMatch Mac 빌드 환경 초기 셋업
# 실행: chmod +x setup-mac.sh && ./setup-mac.sh

set -e

echo "=== PilaMatch Mac Build Environment Setup ==="

# 1. Xcode Command Line Tools
echo "[1/8] Xcode Command Line Tools 설치..."
xcode-select --install 2>/dev/null || echo "이미 설치됨"

# 2. Homebrew
echo "[2/8] Homebrew 설치..."
if ! command -v brew &>/dev/null; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 3. Node.js (LTS) via nvm
echo "[3/8] Node.js 설치..."
if ! command -v nvm &>/dev/null; then
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi
nvm install --lts
nvm use --lts

# 4. pnpm
echo "[4/8] pnpm 설치..."
npm install -g pnpm

# 5. CocoaPods (iOS 빌드 의존성)
echo "[5/8] CocoaPods 설치..."
brew install cocoapods

# 6. JDK 17 (Android 빌드용)
echo "[6/8] JDK 17 설치..."
brew install openjdk@17
sudo ln -sfn "$(brew --prefix openjdk@17)/libexec/openjdk.jdk" \
  /Library/Java/JavaVirtualMachines/openjdk-17.jdk

# 7. Android Studio
echo "[7/8] Android Studio 설치..."
brew install --cask android-studio
echo "Android Studio를 열어 SDK Manager에서 다음을 설치하세요:"
echo "  - Android SDK Platform 34 (API 34)"
echo "  - Android SDK Build-Tools 34.0.0"
echo "  - Android SDK Command-line Tools"
echo "  - Android Emulator"

# 8. 환경 변수 설정
echo "[8/8] 환경 변수 설정..."
cat >> ~/.zshrc << 'EOF'

# Android SDK
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin

# Java
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
EOF

source ~/.zshrc

echo ""
echo "=== 셋업 완료 ==="
echo "추가 필요 작업:"
echo "  1. App Store에서 Xcode 설치 (약 35GB)"
echo "  2. Xcode 열기 → Preferences → Platforms → iOS Simulator 다운로드"
echo "  3. Android Studio 열기 → SDK Manager → Platform 34 설치"
echo "  4. Apple Developer 계정 로그인 (Xcode → Settings → Accounts)"
```

---

### Phase 2: Capacitor 통합

#### 2.1 Capacitor 패키지 설치

```bash
cd /home/jkcho/PilaMatch/frontend-next

# Capacitor 코어 & CLI
pnpm add @capacitor/core
pnpm add -D @capacitor/cli

# 플랫폼
pnpm add @capacitor/ios @capacitor/android

# 필수 플러그인
pnpm add @capacitor/push-notifications   # 푸시 알림
pnpm add @capacitor/camera               # 프로필 사진 (추후)
pnpm add @capacitor/haptics              # 햅틱 피드백
pnpm add @capacitor/status-bar           # 상태바 제어
pnpm add @capacitor/splash-screen        # 스플래시 화면
pnpm add @capacitor/keyboard             # 키보드 제어
pnpm add @capacitor/app                  # 앱 상태/딥링크
pnpm add @capacitor/browser              # In-App Browser (Toss 결제용)
pnpm add @capacitor/preferences          # 키-값 저장소 (토큰)
pnpm add @capacitor/network              # 네트워크 상태 감지

# 보안 저장소 (JWT 토큰용, 커뮤니티 플러그인)
pnpm add capacitor-secure-storage-plugin

# Capacitor 초기화
npx cap init "PilaMatch" "com.pilamatch.app" --web-dir out
```

#### 2.2 next.config.ts 변경

현재 `output: "standalone"`은 Node.js 서버 렌더링용이다. Capacitor는 정적 HTML/JS/CSS 파일이 필요하므로 `output: "export"`로 전환해야 한다.

```typescript
// frontend-next/next.config.ts

import type { NextConfig } from "next";

const isCapacitor = process.env.BUILD_TARGET === 'capacitor';

const nextConfig: NextConfig = {
  // Capacitor 빌드: 정적 export / 웹 빌드: standalone (Docker)
  output: isCapacitor ? "export" : "standalone",
  reactStrictMode: true,

  // Capacitor 빌드 시 이미지 최적화 비활성화 (next/image는 서버 필요)
  ...(isCapacitor && {
    images: {
      unoptimized: true,
    },
  }),

  // 웹 빌드 시에만 API 프록시 적용
  ...(!isCapacitor && {
    async rewrites() {
      const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
      return [
        {
          source: "/api/v1/:path*",
          destination: `${backendUrl}/api/v1/:path*`,
        },
      ];
    },
  }),
};

export default nextConfig;
```

> **중요**: `output: "export"`로 전환하면 Next.js API Routes (`/api/auth/*`)와 middleware, `rewrites`가 작동하지 않는다. 이것이 Phase 3에서 인증 방식을 변경해야 하는 핵심 이유다.

#### 2.3 capacitor.config.ts

```typescript
// frontend-next/capacitor.config.ts

import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.pilamatch.app',
  appName: 'PilaMatch',
  webDir: 'out',

  server: {
    // 개발 시에만 사용 (프로덕션 빌드에서는 제거)
    // url: 'http://192.168.x.x:3000',
    // cleartext: true,

    androidScheme: 'https',
    iosScheme: 'https',
  },

  plugins: {
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 2000,
      backgroundColor: '#7c3aed', // PilaMatch theme color
      androidSplashResourceName: 'splash',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
      splashFullScreen: true,
      splashImmersive: true,
    },

    StatusBar: {
      style: 'LIGHT',
      backgroundColor: '#7c3aed',
    },

    Keyboard: {
      resize: 'body',
      resizeOnFullScreen: true,
    },

    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert'],
    },

    CapacitorHttp: {
      enabled: true,
    },
  },

  ios: {
    contentInset: 'always',
    allowsLinkPreview: false,
    scrollEnabled: true,
    // iOS 상단 Safe Area 처리
    preferredContentMode: 'mobile',
  },

  android: {
    allowMixedContent: false,
    captureInput: true,
    webContentsDebuggingEnabled: false, // 프로덕션에서는 false
  },
};

export default config;
```

#### 2.4 플랫폼 추가 및 동기화

```bash
# 정적 빌드 생성
BUILD_TARGET=capacitor pnpm build

# iOS/Android 프로젝트 생성
npx cap add ios
npx cap add android

# 웹 자산 동기화
npx cap sync
```

---

### Phase 3: 코드 수정 필요 사항

#### 3.1 인증 방식 전환: BFF -> Direct API

현재 BFF 패턴의 핵심 파일들은 다음과 같다.

| 파일 | 역할 | 전환 필요 |
|------|------|----------|
| `src/app/api/auth/login/route.ts` | 로그인 BFF (FastAPI 호출 -> httpOnly cookie 설정) | 네이티브에서 불필요 |
| `src/app/api/auth/signup/route.ts` | 회원가입 BFF | 네이티브에서 불필요 |
| `src/app/api/auth/logout/route.ts` | 로그아웃 BFF (cookie 삭제) | 네이티브에서 불필요 |
| `src/app/api/auth/me/route.ts` | 현재 사용자 조회 BFF | 네이티브에서 불필요 |
| `src/middleware.ts` | cookie에서 토큰 추출 -> Authorization header 주입 | 네이티브에서 작동 안 함 |
| `src/lib/api-client.ts` | `credentials: 'include'`로 cookie 전송 | 토큰 직접 주입으로 변경 |

**전환 구현 코드**:

```typescript
// frontend-next/src/lib/platform.ts
// 플랫폼 감지 유틸리티

import { Capacitor } from '@capacitor/core';

export function isNativePlatform(): boolean {
  return Capacitor.isNativePlatform();
}

export function getPlatform(): 'ios' | 'android' | 'web' {
  return Capacitor.getPlatform() as 'ios' | 'android' | 'web';
}
```

```typescript
// frontend-next/src/lib/token-storage.ts
// 플랫폼별 토큰 저장소

import { isNativePlatform } from './platform';

// 네이티브: Capacitor Secure Storage
// 웹: BFF cookie (기존 방식 유지)

let SecureStoragePlugin: any = null;

async function getSecureStorage() {
  if (!SecureStoragePlugin) {
    const module = await import('capacitor-secure-storage-plugin');
    SecureStoragePlugin = module.SecureStoragePlugin;
  }
  return SecureStoragePlugin;
}

export async function saveToken(token: string): Promise<void> {
  if (!isNativePlatform()) return; // 웹에서는 BFF cookie 사용

  const storage = await getSecureStorage();
  await storage.set({ key: 'access_token', value: token });
}

export async function getToken(): Promise<string | null> {
  if (!isNativePlatform()) return null; // 웹에서는 cookie 자동 전송

  try {
    const storage = await getSecureStorage();
    const result = await storage.get({ key: 'access_token' });
    return result.value;
  } catch {
    return null;
  }
}

export async function removeToken(): Promise<void> {
  if (!isNativePlatform()) return;

  const storage = await getSecureStorage();
  await storage.remove({ key: 'access_token' });
}
```

```typescript
// frontend-next/src/lib/api-client.ts 수정
// 플랫폼별 API 호출 분기

import { isNativePlatform } from './platform';
import { getToken } from './token-storage';

// 네이티브: FastAPI 직접 호출
// 웹: Next.js 프록시 경유 (기존 유지)
function getBaseUrl(): string {
  if (isNativePlatform()) {
    // 프로덕션 API 서버 주소
    return process.env.NEXT_PUBLIC_NATIVE_API_URL || 'https://api.pilamatch.com/api/v1';
  }
  return '/api/v1'; // 웹: Next.js rewrites 경유
}

const BASE_URL = getBaseUrl();

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${BASE_URL}${path}`;

  const defaultHeaders: Record<string, string> = {};
  if (options.body && typeof options.body === 'string') {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  // 네이티브: Secure Storage에서 토큰을 꺼내 헤더에 직접 설정
  if (isNativePlatform()) {
    const token = await getToken();
    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  const config: RequestInit = {
    ...options,
    // 네이티브에서는 credentials 불필요
    ...(isNativePlatform() ? {} : { credentials: 'include' as RequestCredentials }),
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  // ... (기존 retry 로직 유지)
}
```

#### 3.2 API Base URL 분기 로직

```typescript
// frontend-next/src/lib/config.ts

import { Capacitor } from '@capacitor/core';

interface AppConfig {
  apiBaseUrl: string;
  tossClientKey: string;
  tossSuccessUrl: string;
  tossFailUrl: string;
  isNative: boolean;
}

export function getAppConfig(): AppConfig {
  const isNative = Capacitor.isNativePlatform();

  if (isNative) {
    return {
      apiBaseUrl: 'https://api.pilamatch.com/api/v1',
      tossClientKey: process.env.NEXT_PUBLIC_TOSS_CLIENT_KEY || '',
      // 네이티브: Deep Link으로 결제 결과 수신
      tossSuccessUrl: 'pilamatch://payment/success',
      tossFailUrl: 'pilamatch://payment/fail',
      isNative: true,
    };
  }

  return {
    apiBaseUrl: '/api/v1',
    tossClientKey: process.env.NEXT_PUBLIC_TOSS_CLIENT_KEY || '',
    // 웹: 페이지 URL로 리다이렉트
    tossSuccessUrl: `${window.location.origin}/payment/success`,
    tossFailUrl: `${window.location.origin}/payment/fail`,
    isNative: false,
  };
}
```

#### 3.3 Toss Payments 결제 플로우 변경

현재 `toss-payment-widget.tsx`에서 결제 완료 후 `successUrl`로 브라우저 리다이렉트하는 방식을 사용한다. 네이티브 앱에서는 In-App Browser를 열고 Deep Link로 결과를 수신해야 한다.

```typescript
// frontend-next/src/components/payment/native-payment-handler.ts

import { Browser } from '@capacitor/browser';
import { App } from '@capacitor/app';
import { isNativePlatform } from '@/lib/platform';

export async function handleNativePayment(paymentUrl: string): Promise<{
  paymentKey: string;
  orderId: string;
  amount: number;
} | null> {
  if (!isNativePlatform()) return null;

  return new Promise((resolve) => {
    // Deep Link 리스너 등록
    const listener = App.addListener('appUrlOpen', ({ url }) => {
      const parsedUrl = new URL(url);

      if (parsedUrl.hostname === 'payment') {
        const path = parsedUrl.pathname;

        if (path === '/success') {
          const paymentKey = parsedUrl.searchParams.get('paymentKey') || '';
          const orderId = parsedUrl.searchParams.get('orderId') || '';
          const amount = Number(parsedUrl.searchParams.get('amount')) || 0;

          resolve({ paymentKey, orderId, amount });
        } else {
          resolve(null); // 결제 실패/취소
        }

        listener.remove();
        Browser.close();
      }
    });

    // In-App Browser로 결제 페이지 열기
    Browser.open({
      url: paymentUrl,
      presentationStyle: 'popover',
    });
  });
}
```

#### 3.4 Push Notifications (신규 기능)

```typescript
// frontend-next/src/lib/push-notifications.ts

import { PushNotifications } from '@capacitor/push-notifications';
import { isNativePlatform } from './platform';
import { getToken } from './token-storage';

export async function initializePushNotifications(): Promise<void> {
  if (!isNativePlatform()) return;

  // 권한 요청
  const permission = await PushNotifications.requestPermissions();
  if (permission.receive !== 'granted') return;

  // 등록
  await PushNotifications.register();

  // FCM 토큰 수신 -> 서버에 등록
  PushNotifications.addListener('registration', async (token) => {
    const accessToken = await getToken();
    if (!accessToken) return;

    await fetch('https://api.pilamatch.com/api/v1/devices/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        token: token.value,
        platform: 'fcm', // iOS도 FCM 사용 가능
      }),
    });
  });

  // 알림 수신 (포그라운드)
  PushNotifications.addListener('pushNotificationReceived', (notification) => {
    console.log('Push received:', notification);
    // 앱 내 알림 UI 표시
  });

  // 알림 탭 (사용자가 알림 클릭)
  PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
    const data = action.notification.data;
    // data.type에 따라 해당 페이지로 네비게이션
    if (data.type === 'new_offer') {
      window.location.href = `/steps/offers`;
    } else if (data.type === 'contract_update') {
      window.location.href = `/steps/contracts`;
    }
  });
}
```

#### 3.5 전체 변경 파일 목록

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `next.config.ts` | **수정** | `output` 분기 (standalone/export) |
| `capacitor.config.ts` | **신규** | Capacitor 설정 |
| `src/lib/platform.ts` | **신규** | 플랫폼 감지 유틸리티 |
| `src/lib/token-storage.ts` | **신규** | 토큰 저장소 (Secure Storage) |
| `src/lib/config.ts` | **신규** | 플랫폼별 설정 |
| `src/lib/api-client.ts` | **수정** | Base URL 분기, 토큰 직접 주입 |
| `src/lib/push-notifications.ts` | **신규** | Push 알림 초기화 |
| `src/components/payment/toss-payment-widget.tsx` | **수정** | 네이티브 Deep Link 결제 |
| `src/components/payment/native-payment-handler.ts` | **신규** | 네이티브 결제 핸들러 |
| `src/hooks/use-auth.ts` | **수정** | 네이티브 로그인/로그아웃 분기 |
| `src/providers/auth-provider.tsx` | **수정** | 토큰 저장/복원 로직 |
| `src/middleware.ts` | **조건부 제거** | 네이티브 빌드 시 미사용 |
| `src/app/api/auth/*/route.ts` | **조건부 제거** | 네이티브 빌드 시 미사용 |
| `package.json` | **수정** | 빌드 스크립트 추가 |

---

### Phase 4: 앱스토어/플레이스토어 출시 준비물

#### 4.1 Apple App Store 준비물

| 항목 | 상세 | 현재 상태 | 비용 |
|------|------|----------|------|
| **Apple Developer 계정** | 개인 또는 조직 계정 등록 | 미등록 | $99/년 |
| **App Store Connect** | 앱 정보 등록, 빌드 업로드, 심사 관리 | - | 무료 (개발자 계정 포함) |
| **인증서 (Certificate)** | iOS Distribution Certificate | 미생성 | 무료 |
| **Provisioning Profile** | App Store Distribution Profile | 미생성 | 무료 |
| **앱 아이콘** | 1024x1024 PNG (알파 채널 없음) | SVG 아이콘만 존재 | 디자인 필요 |
| **스크린샷** | 최소 3종 해상도 | 미준비 | 앱 완성 후 촬영 |
| **개인정보처리방침 URL** | 공개 접근 가능한 URL | `docs/privacy-policy-ko.md` 작성 완료 | 웹 호스팅 필요 |
| **지원 URL** | 고객 지원 페이지/이메일 | support@pilamatch.com | 운영 준비 필요 |
| **앱 설명** | 최대 4,000자 | `docs/store-description-ko.md` 작성 완료 | 가공 필요 |
| **키워드** | 최대 100자 (쉼표 구분) | 작성 완료 | - |
| **연령 등급** | 콘텐츠 질문지 답변 | 미설정 | 무료 |
| **App Privacy** | 수집 데이터 카테고리 명시 | 미설정 | 무료 |

**스크린샷 필요 해상도**:

| 디바이스 | 해상도 | 필수 여부 |
|---------|--------|----------|
| iPhone 16 Pro Max (6.9") | 1320 x 2868 | 필수 |
| iPhone 16 Pro (6.3") | 1206 x 2622 | 선택 (6.9" 자동 조정 가능) |
| iPhone SE 3세대 (4.7") | 750 x 1334 | 선택 (앱이 지원하는 경우) |
| iPad Pro 13" | 2064 x 2752 | iPad 미지원 시 불필요 |

**필요 스크린샷 장면** (최소 3장, 권장 5-8장):

1. 로그인/회원가입 화면
2. 프로필 (강사 or 스튜디오)
3. 매칭 결과 / 공고 목록
4. 계약 상세 / 에스크로 결제
5. Trust Score 대시보드
6. 프리미엄 멤버십 페이지
7. 채팅 화면
8. 본인인증 (SMS OTP)

#### 4.2 Google Play Store 준비물

| 항목 | 상세 | 현재 상태 | 비용 |
|------|------|----------|------|
| **Google Play Console** | 개발자 계정 등록 | 미등록 | $25 (일회성) |
| **서명 키** | Upload Key + Google Play App Signing | 미생성 | 무료 |
| **앱 아이콘** | 512x512 PNG (32-bit, 알파 포함 가능) | SVG 아이콘만 존재 | 디자인 필요 |
| **특성 그래픽** | 1024x500 PNG/JPEG | 미준비 | 디자인 필요 |
| **스크린샷** | 최소 2장, 최대 8장 (폰/태블릿별) | 미준비 | 앱 완성 후 촬영 |
| **짧은 설명** | 최대 80자 | 작성 필요 | - |
| **전체 설명** | 최대 4,000자 | `docs/store-description-ko.md` 활용 가능 | 가공 필요 |
| **개인정보처리방침 URL** | Apple과 동일 | 작성 완료 | 웹 호스팅 필요 |
| **데이터 안전 섹션** | 수집/공유하는 데이터 유형 명시 | 미설정 | 무료 |
| **콘텐츠 등급** | IARC 질문지 | 미설정 | 무료 |
| **대상 연령층** | 모든 연령 / 성인 등 | 설정 필요 | 무료 |
| **광고 포함 여부** | 없음 | - | - |

**데이터 안전 섹션 작성 내용** (PilaMatch 기준):

| 데이터 유형 | 수집 여부 | 공유 여부 | 용도 |
|------------|----------|----------|------|
| 이름 | 수집 | 비공유 | 계정 관리, 프로필 |
| 이메일 | 수집 | 비공유 | 계정 관리, 로그인 |
| 전화번호 | 수집 | 비공유 | 본인인증 (SMS) |
| 위치 (대략적) | 수집 | 비공유 | 매칭 (지역 기반) |
| 결제 정보 | 수집 | Toss Payments에 공유 | 결제 처리 |
| 사업자등록번호 | 수집 | 국세청에 공유 (진위 확인) | 사업자 인증 |
| 사용자 활동 | 수집 | 비공유 | 서비스 개선, Trust Score |

---

### Phase 5: 결제 관련 중대 이슈 (Apple 30%)

#### 5.1 Apple In-App Purchase 정책 분석

Apple은 앱 내에서 "디지털 콘텐츠 또는 서비스 기능 해제(unlock)"에 해당하는 결제를 반드시 IAP(In-App Purchase)를 통해 처리하도록 요구하며, 매출의 30% (Small Business Program 적용 시 15%)를 수수료로 부과한다.

**PilaMatch 결제 유형별 분석**:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Apple IAP 정책 적용 분석                               │
├─────────────────┬────────────────────────┬──────────────┬───────────────┤
│ 결제 유형        │ 분류                   │ IAP 필수?    │ 근거          │
├─────────────────┼────────────────────────┼──────────────┼───────────────┤
│ 에스크로 (수업료) │ 실물 서비스 중개 수수료  │ 아니오       │ App Store     │
│                 │ (필라테스/요가 수업)     │ Toss 유지    │ Review 3.1.3 │
│                 │                        │              │ "실물 서비스" │
├─────────────────┼────────────────────────┼──────────────┼───────────────┤
│ 보증금 (5만원)   │ 서비스 이용 보증금       │ 아니오       │ App Store     │
│                 │ (환불 가능 예치금)       │ Toss 유지    │ Review 3.1.5 │
│                 │                        │              │ "환불가능 예치"│
├─────────────────┼────────────────────────┼──────────────┼───────────────┤
│ 프리미엄 구독    │ 디지털 기능 언락         │ 예           │ App Store     │
│ (9,900원/월)    │ (수수료 할인, 무제한     │ IAP 전환     │ Review 3.1.1 │
│                 │  지원, 매칭 부스트 등)   │ 필수         │ "디지털 콘텐츠"│
└─────────────────┴────────────────────────┴──────────────┴───────────────┘
```

#### 5.2 프리미엄 구독 IAP 전환 전략

**세 가지 접근법 비교**:

| 접근법 | 설명 | 장점 | 단점 | 추천 |
|--------|------|------|------|------|
| **A. IAP 사용 (추천)** | Apple/Google IAP로 프리미엄 구독 처리 | 심사 통과 확실, 표준 결제 UX | Apple 30% 수수료 | 강력 추천 |
| **B. Reader Rule** | 앱에서 외부 결제 링크 제공 (2022년 한국 공정위 결정) | Toss 유지 가능 | 구현 복잡, Apple 추가 심사, UX 분절 | 장기 검토 |
| **C. 웹 전용 구독** | 앱에서 구독 UI 제거, 웹에서만 결제 | 수수료 회피 | 전환율 급감, 사용자 혼란 | 비추천 |

**접근법 A (IAP) 상세 - 추천**:

```
[가격 전략]

현재 Toss 결제:
  월 9,900원 -> 수수료 약 3% (PG) = 순매출 약 9,603원

Apple IAP 전환 시:
  Apple 수수료 30% (또는 Small Business Program 적용 시 15%)

  옵션 1) 가격 유지 (마진 감소)
    월 9,900원 -> Apple 30% = 순매출 6,930원 (29% 감소)
    월 9,900원 -> Apple 15% = 순매출 8,415원 (12% 감소)

  옵션 2) 가격 인상 (마진 유지)
    월 12,900원 -> Apple 30% = 순매출 9,030원 (기존과 유사)
    월 11,900원 -> Apple 15% = 순매출 10,115원

  옵션 3) 플랫폼별 차등 가격
    iOS: 12,900원 (Apple Tier)
    Android: 10,900원 (Google 15%)
    Web: 9,900원 (Toss PG 3%)

권장: 옵션 1 + Small Business Program 신청
  - Small Business Program: 연 매출 $1M 미만 시 수수료 15% 적용
  - MVP 단계에서는 거의 확실히 자격 충족
  - 월 9,900원 유지, 순매출 8,415원으로 운영
```

**IAP 구현 시 필요 작업**:

| 작업 | 내용 |
|------|------|
| App Store Connect에 IAP 상품 등록 | `com.pilamatch.premium.monthly` Auto-Renewable Subscription |
| Google Play Console에 구독 상품 등록 | 동일 상품 ID |
| Capacitor IAP 플러그인 추가 | `@capawesome-team/capacitor-purchases` 또는 RevenueCat SDK |
| 서버 영수증 검증 | Apple: App Store Server API, Google: Google Play Developer API |
| 기존 `SubscriptionService` 확장 | IAP 영수증 기반 구독 상태 관리 추가 |
| 웹/네이티브 구독 UI 분기 | 네이티브에서는 IAP 구독 UI, 웹에서는 Toss 유지 |

```typescript
// frontend-next/src/lib/iap.ts
// In-App Purchase 처리 (Capacitor)

import { isNativePlatform, getPlatform } from './platform';

interface IAPProduct {
  productId: string;
  title: string;
  price: string;
  priceAmountMicros: number;
  currency: string;
}

interface IAPPurchaseResult {
  transactionId: string;
  receipt: string; // 서버 검증용
  platform: 'apple' | 'google';
}

// RevenueCat 사용 시 (추천 - Apple/Google 통합 관리)
export async function initializeIAP(): Promise<void> {
  if (!isNativePlatform()) return;

  // RevenueCat SDK 초기화
  // const { Purchases } = await import('@revenuecat/purchases-capacitor');
  // await Purchases.configure({ apiKey: 'YOUR_REVENUECAT_API_KEY' });
}

export async function getSubscriptionProducts(): Promise<IAPProduct[]> {
  if (!isNativePlatform()) return [];

  // 구독 상품 목록 조회
  // const offerings = await Purchases.getOfferings();
  // return offerings.current?.availablePackages || [];
  return [];
}

export async function purchaseSubscription(productId: string): Promise<IAPPurchaseResult | null> {
  if (!isNativePlatform()) return null;

  // IAP 구매 실행
  // const result = await Purchases.purchasePackage({ aPackage: ... });
  // return { transactionId: result.transaction.transactionIdentifier, ... };
  return null;
}

export async function restorePurchases(): Promise<void> {
  if (!isNativePlatform()) return;

  // 이전 구매 복원 (앱 재설치 시)
  // await Purchases.restorePurchases();
}
```

---

### Phase 6: 빌드 & 배포 파이프라인

#### 6.1 전체 빌드 플로우

```
                      PilaMatch 빌드 & 배포 파이프라인
                      ================================

   [개발 환경]           [빌드 환경]              [배포 대상]
   ============         =============           ================

   WSL2 (Linux)
   ┌──────────┐
   │ Next.js  │──(1)──> git push
   │ 소스코드   │
   │ + FastAPI │
   └──────────┘
        │
        │              Mac (또는 CI)
        │              ┌──────────────────────┐
        │              │                      │
        └──(2)──pull──>│  pnpm install        │
                       │  BUILD_TARGET=cap    │
                       │  pnpm build          │──(3a)──> ┌─────────────┐
                       │  npx cap sync        │          │ App Store   │
                       │                      │          │ Connect     │
                       │  ┌─────────────┐     │          │ (TestFlight)│
                       │  │ Xcode       │─────│──────────│──> App Store│
                       │  │ Archive     │     │          └─────────────┘
                       │  └─────────────┘     │
                       │                      │
                       │  ┌─────────────┐     │──(3b)──> ┌─────────────┐
                       │  │ Android     │     │          │ Google Play │
                       │  │ Studio      │─────│──────────│ Console     │
                       │  │ AAB Bundle  │     │          │ (내부 테스트) │
                       │  └─────────────┘     │          │──> Play Store│
                       │                      │          └─────────────┘
                       └──────────────────────┘

   [웹 배포 - 기존 유지]
   WSL2 ──> docker-compose build ──> Docker Registry ──> 서버 배포
```

#### 6.2 빌드 명령어

**package.json 스크립트 추가**:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "build:cap": "BUILD_TARGET=capacitor next build",
    "start": "next start",
    "cap:sync": "npx cap sync",
    "cap:ios": "npx cap open ios",
    "cap:android": "npx cap open android",
    "cap:build": "pnpm build:cap && pnpm cap:sync",
    "cap:run:ios": "pnpm cap:build && npx cap run ios",
    "cap:run:android": "pnpm cap:build && npx cap run android"
  }
}
```

**전체 빌드 & 배포 프로세스**:

```bash
# === iOS 빌드 & 배포 ===

# 1. 웹 자산 빌드 (Mac에서)
cd /path/to/PilaMatch/frontend-next
pnpm install
pnpm cap:build

# 2. Xcode에서 iOS 프로젝트 열기
npx cap open ios

# 3. Xcode에서 다음 수행:
#    a. Signing & Capabilities → Team 선택 (Apple Developer 계정)
#    b. Product → Archive
#    c. Organizer → Distribute App → App Store Connect
#    d. TestFlight에서 내부 테스트 진행
#    e. App Store Connect → 심사 제출


# === Android 빌드 & 배포 ===

# 1. 웹 자산 빌드 (동일)
pnpm cap:build

# 2. Android Studio에서 프로젝트 열기
npx cap open android

# 3. Android Studio에서 다음 수행:
#    a. Build → Generate Signed Bundle / APK
#    b. Android App Bundle (AAB) 선택
#    c. 키스토어 생성 또는 기존 키스토어 선택
#    d. Release 빌드 생성
#    e. Google Play Console → 내부 테스트 트랙에 업로드
#    f. 프로덕션 트랙으로 승격
```

#### 6.3 CI/CD 자동화 (GitHub Actions)

```yaml
# .github/workflows/mobile-build.yml

name: Mobile Build

on:
  push:
    tags:
      - 'v*'  # v1.0.0 태그 시 빌드

jobs:
  build-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'pnpm'
          cache-dependency-path: frontend-next/pnpm-lock.yaml

      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Install dependencies
        working-directory: frontend-next
        run: pnpm install

      - name: Build web assets
        working-directory: frontend-next
        run: pnpm cap:build
        env:
          BUILD_TARGET: capacitor
          NEXT_PUBLIC_NATIVE_API_URL: https://api.pilamatch.com/api/v1

      - name: Build Android
        working-directory: frontend-next/android
        run: ./gradlew assembleRelease

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: android-release
          path: frontend-next/android/app/build/outputs/apk/release/

  build-ios:
    runs-on: macos-14  # Apple Silicon runner
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'pnpm'
          cache-dependency-path: frontend-next/pnpm-lock.yaml

      - name: Install dependencies
        working-directory: frontend-next
        run: pnpm install

      - name: Build web assets
        working-directory: frontend-next
        run: pnpm cap:build
        env:
          BUILD_TARGET: capacitor
          NEXT_PUBLIC_NATIVE_API_URL: https://api.pilamatch.com/api/v1

      - name: Install CocoaPods
        working-directory: frontend-next/ios/App
        run: pod install

      - name: Build iOS
        working-directory: frontend-next/ios/App
        run: |
          xcodebuild -workspace App.xcworkspace \
            -scheme App \
            -sdk iphoneos \
            -configuration Release \
            -archivePath build/App.xcarchive \
            archive \
            CODE_SIGNING_ALLOWED=NO
```

---

### Phase 7: 앱 심사 대비 체크리스트

#### 7.1 Apple 심사 거절 사유 Top 5 및 대응 방안

| 거절 사유 | App Store Review 조항 | PilaMatch 리스크 | 대응 방안 |
|----------|----------------------|----------------|----------|
| **Minimum Functionality** | 4.2 | **높음** - WebView만으로는 "웹사이트를 래핑한 것"으로 판단 가능 | 네이티브 기능 최소 3-4개 추가 (Push, 생체인증, 카메라, Haptics) |
| **IAP 미사용** | 3.1.1 | **높음** - 프리미엄 구독이 Toss 결제를 사용 중 | IAP로 전환 필수 (Phase 5 참조) |
| **Privacy 부정확** | 5.1.1 | **중간** - 수집 데이터 목록 부정확 시 | 개인정보처리방침 + App Privacy Labels 정확히 작성 |
| **디자인 가이드라인** | 4.0 | **중간** - iOS HIG 미준수 (웹 스타일 UI) | iOS 네이티브 네비게이션, 상태바, Safe Area 대응 |
| **불완전한 정보** | 2.1 | **낮음** - 데모 계정 미제공 | 심사용 테스트 계정 + 상세 노트 제공 |

#### 7.2 심사 통과를 위한 필수 네이티브 기능

WebView 앱이 "Minimum Functionality (4.2)" 거절을 피하려면 순수 웹에서는 불가능한 네이티브 기능을 반드시 포함해야 한다.

| 기능 | Capacitor 플러그인 | 구현 난이도 | 우선순위 | 설명 |
|------|-------------------|-----------|---------|------|
| **Push Notifications** | `@capacitor/push-notifications` | 중 | P0 | 새 오퍼, 계약 상태 변경, 메시지 알림 |
| **Biometric Auth** | `capacitor-native-biometric` | 낮 | P0 | Face ID / 지문으로 앱 잠금 해제 |
| **Camera** | `@capacitor/camera` | 낮 | P1 | 프로필 사진 촬영 (추후 자격증 사진 업로드) |
| **Haptics** | `@capacitor/haptics` | 낮 | P1 | 버튼 탭, 상태 전환 시 햅틱 피드백 |
| **App Badge** | 자동 (Push 설정) | 없음 | P1 | 읽지 않은 알림 수 표시 |
| **Calendar** | `@capacitor/calendar` (커뮤니티) | 중 | P2 | 수업 일정을 기기 캘린더에 추가 |
| **Location** | `@capacitor/geolocation` | 낮 | P2 | 현재 위치 기반 주변 스튜디오/공고 검색 |
| **Share** | `@capacitor/share` | 낮 | P2 | 공고/프로필 공유 기능 |

#### 7.3 Apple 심사 제출 시 Review Notes 템플릿

```
[테스트 계정]
- 강사 계정: test-instructor@pilamatch.com / Test1234!
- 스튜디오 계정: test-studio@pilamatch.com / Test1234!
- 프리미엄 회원 계정: test-premium@pilamatch.com / Test1234!

[결제 설명]
- 에스크로 결제 (수업료): 실물 서비스(필라테스/요가 수업) 중개 수수료입니다.
  App Store Review Guidelines 3.1.3(e)에 따라 외부 결제(Toss Payments)를
  사용합니다.
- 보증금: 서비스 이용 보증을 위한 환불 가능한 예치금입니다.
- 프리미엄 구독: In-App Purchase (Auto-Renewable Subscription)으로 처리됩니다.

[앱 동작 순서]
1. 회원가입 → SMS 본인인증 → 프로필 작성
2. (스튜디오) 사업자인증 → 보증금 입금 → 공고 작성
3. (강사) 보증금 입금 → 공고 검색 → 지원
4. 매칭 → 오퍼 → 계약 체결 → 에스크로 결제 → 수업 진행 → 완료/정산
5. (선택) 프리미엄 구독으로 추가 혜택

[네이티브 기능 사용]
- Push Notifications: 새 오퍼, 메시지, 계약 상태 변경 알림
- Face ID / Touch ID: 앱 잠금 해제 및 결제 확인
- Camera: 프로필 사진 촬영
- Haptic Feedback: UI 인터랙션 피드백

[개인정보]
- 개인정보처리방침: https://pilamatch.com/privacy
- 이용약관: https://pilamatch.com/terms
```

#### 7.4 Google Play 심사 체크리스트

Google Play는 Apple보다 심사가 관대하나, 다음 사항은 반드시 준수해야 한다.

| 항목 | 확인 사항 | 상태 |
|------|----------|------|
| 데이터 안전 섹션 | 수집 데이터 목록 정확히 기재 | 작성 필요 |
| 콘텐츠 등급 | IARC 질문지 완료 | 설정 필요 |
| 대상 연령 | "성인" 또는 "모든 연령" 설정 | 설정 필요 |
| 결제 정책 | 디지털 상품 IAP 사용 (Google 15%/30%) | 전환 필요 |
| 위치 권한 | 백그라운드 위치 미사용 명시 | 해당 없음 |
| 카메라 권한 | 용도 명시 (프로필 사진) | 설정 필요 |
| 앱 크래시 | ANR/크래시 없이 정상 동작 | 테스트 필요 |
| 20개 내부 테스터 | 내부 테스트 트랙 14일 이상 운영 | 신규 필수 조건 |

---

### Phase 8: 출시 타임라인

```
주차별 상세 타임라인 (총 6주)
==========================

Week 1-2: Capacitor 통합 & 코드 수정
├── Day 1-2:  Capacitor 설치, capacitor.config.ts, next.config.ts 수정
├── Day 3-5:  인증 방식 전환 (BFF -> Direct API + Secure Storage)
├── Day 6-7:  API Base URL 분기, api-client.ts 수정
├── Day 8-9:  Toss Payments 네이티브 결제 플로우 (In-App Browser + Deep Link)
└── Day 10:   프리미엄 구독 IAP 연동 (RevenueCat 또는 직접 구현)

Week 3: 네이티브 기능 추가
├── Day 11-12: Push Notifications (FCM + APNs, 서버 API 추가)
├── Day 13:    Biometric Auth (Face ID / 지문 잠금)
├── Day 14:    Camera (프로필 사진)
└── Day 15:    Haptics, Splash Screen, Status Bar 세팅

Week 4: 테스팅 & QA
├── Day 16-17: iOS 시뮬레이터 테스트 (모든 화면 검증)
├── Day 18-19: Android 에뮬레이터 테스트
├── Day 20:    실기기 테스트 (iPhone + Android 최소 1대씩)
└── Day 21:    결제 플로우 E2E 테스트 (Sandbox/테스트 환경)

Week 5: 스토어 등록 & 제출
├── Day 22:    앱 아이콘 + 스크린샷 제작
├── Day 23:    Apple Developer 계정 등록 + App Store Connect 앱 생성
├── Day 24:    Google Play Console 등록 + 내부 테스트 트랙 배포
├── Day 25:    iOS Archive → TestFlight 업로드 → 내부 테스트
├── Day 26:    Android AAB → 내부 테스트 트랙 → 14일 테스트 시작
└── Day 27:    iOS 심사 제출 (Review Notes 포함)

Week 6: 심사 대응
├── Day 28-30: Apple 심사 대기 (평균 24-48시간, 최대 7일)
├── Day 31-32: 심사 피드백 대응 (거절 시 수정 후 재제출)
├── Day 33-34: Google Play 프로덕션 트랙 승격
└── Day 35:    양 스토어 공개 + 웹 공지
```

**마일스톤 체크포인트**:

| 마일스톤 | 예상 날짜 | 완료 기준 |
|---------|----------|----------|
| Capacitor 빌드 성공 | Week 1 Day 3 | `npx cap sync` 에러 없음 |
| 네이티브 로그인 동작 | Week 2 Day 7 | iOS 시뮬레이터에서 로그인 -> 대시보드 진입 |
| 결제 플로우 완성 | Week 2 Day 10 | Sandbox IAP 결제 성공 |
| 네이티브 기능 동작 | Week 3 Day 15 | Push 수신, 생체인증 작동 |
| QA 완료 | Week 4 Day 21 | 크리티컬 버그 0개 |
| 심사 제출 | Week 5 Day 27 | App Store Connect에 빌드 업로드 |
| 출시 | Week 6 Day 35 | 양 스토어 공개 |

---

## 4. 즉시 실행 가능한 작업 (WSL2에서)

### Mac 없이 지금 할 수 있는 작업

| 작업 | 설명 | 예상 소요 시간 | 우선순위 |
|------|------|--------------|---------|
| **Capacitor 설치 및 설정** | pnpm add, capacitor.config.ts 작성 | 1시간 | P0 |
| **next.config.ts 분기** | `output` 조건부 설정 | 30분 | P0 |
| **인증 코드 분기** | platform.ts, token-storage.ts 작성, api-client.ts 수정 | 4시간 | P0 |
| **Android 프로젝트 생성** | `npx cap add android` (WSL2에서 가능) | 30분 | P0 |
| **Android 빌드 테스트** | WSL2에 Android SDK 설치 후 빌드 | 2시간 | P1 |
| **앱 아이콘 디자인** | 1024x1024 + 512x512 PNG 제작 | 2시간 | P1 |
| **스토어 설명 가공** | store-description-ko.md 기반 앱스토어 형식 작성 | 1시간 | P1 |
| **IAP 서버 검증 API** | FastAPI에 영수증 검증 엔드포인트 추가 | 4시간 | P1 |
| **Push 알림 서버 API** | FCM 토큰 등록, 알림 발송 API 추가 | 4시간 | P1 |
| **Deep Link 설정** | `pilamatch://` URL scheme 핸들러 코드 | 1시간 | P2 |
| **Apple Developer 계정 등록** | developer.apple.com에서 $99 결제 | 30분 | P2 |
| **Google Play Console 등록** | play.google.com/console에서 $25 결제 | 30분 | P2 |
| **개인정보처리방침 웹 호스팅** | pilamatch.com/privacy URL 배포 | 1시간 | P2 |

### Mac이 필요한 작업

| 작업 | 설명 | Mac 필요 이유 |
|------|------|-------------|
| iOS 프로젝트 생성 | `npx cap add ios` | CocoaPods 필요 |
| iOS 시뮬레이터 테스트 | Xcode Simulator | macOS 전용 |
| iOS 빌드 | Xcode Archive | macOS 전용 |
| iOS 코드 서명 | Certificate + Provisioning Profile | Keychain 필요 |
| TestFlight 업로드 | Xcode Organizer | macOS 전용 |
| App Store 제출 | App Store Connect 빌드 배포 | Xcode 필요 |

> **결론**: 전체 작업의 약 60%를 WSL2에서 선행할 수 있다. Mac은 최종 iOS 빌드와 제출 단계에서만 필수적이다. Android는 WSL2에서 빌드부터 Play Console 업로드까지 모두 가능하다.

---

## 5. 리스크 & 대응 방안

### 5.1 Apple 심사 거절 리스크

| 리스크 | 발생 확률 | 영향도 | 대응 방안 |
|--------|----------|--------|----------|
| 4.2 Minimum Functionality (WebView 판정) | **높음** (40%) | 출시 지연 1-2주 | Push, 생체인증, 카메라, Haptics 반드시 포함. 첫 제출 시 Review Notes에 네이티브 기능 목록 명시 |
| 3.1.1 IAP 미사용 | **매우 높음** (90% if 미전환) | 출시 불가 | 프리미엄 구독 반드시 IAP 전환. 에스크로/보증금은 실물 서비스 근거 문서 첨부 |
| 5.1.1 Privacy 부정확 | **중간** (25%) | 출시 지연 3-5일 | 개인정보처리방침과 App Privacy Labels 사전 교차 검증 |
| 디자인 가이드라인 미준수 | **낮음** (15%) | 출시 지연 3-5일 | iOS 네이티브 뒤로가기 제스처, Safe Area, Dynamic Type 대응 |
| 에스크로 외부 결제 거절 | **낮음** (10%) | 수익 모델 변경 필요 | "실물 서비스 중개" 근거 사전 준비 (App Store Review Board 항소 가능) |

**첫 심사 거절 시 행동 계획**:

```
1. Resolution Center에서 거절 사유 정확히 확인
2. 거절 사유별 수정 (보통 1-3일 소요)
3. 수정 후 Reply + 재제출 (Review Notes에 변경 사항 명시)
4. 2회 연속 거절 시 App Review Board에 항소 검토
5. 3회 거절 시 전략 재검토 (React Native 전환 등)
```

### 5.2 Capacitor WebView 성능 이슈

| 리스크 | 발생 확률 | 영향도 | 대응 방안 |
|--------|----------|--------|----------|
| 화면 전환 시 흰 화면(Flash) | **중간** (30%) | UX 저하 | SplashScreen 플러그인으로 마스킹, CSS transition 추가 |
| 스크롤 성능 저하 (구형 기기) | **낮음** (15%) | 일부 사용자 불만 | 가상 스크롤 적용, 큰 리스트 페이지네이션, `-webkit-overflow-scrolling: touch` |
| 키보드 표시 시 레이아웃 깨짐 | **높음** (50%) | 입력 폼 사용 불편 | Keyboard 플러그인 `resize: 'body'` 설정, viewport meta 조정 |
| 메모리 부족 (iOS WKWebView) | **낮음** (10%) | 앱 크래시 | 이미지 최적화, 컴포넌트 lazy loading |
| 제스처 충돌 (iOS 뒤로가기) | **중간** (30%) | 네비게이션 혼란 | `capacitor.config.ts`에서 `allowsBackForwardNavigationGestures: true` |

**성능 최적화 체크리스트**:

```bash
# 빌드 사이즈 분석 (큰 번들은 로딩 지연)
pnpm add -D @next/bundle-analyzer

# 이미지 최적화 (unoptimized: true일 때 직접 최적화)
pnpm add sharp  # 빌드 시 이미지 리사이징

# CSS 정리 (사용하지 않는 Tailwind 클래스 제거)
# tailwind.config.ts에 purge 설정 확인
```

### 5.3 Toss Payments 모바일 호환성

| 리스크 | 발생 확률 | 영향도 | 대응 방안 |
|--------|----------|--------|----------|
| WebView 내 결제 SDK 미동작 | **중간** (30%) | 결제 불가 | In-App Browser (`@capacitor/browser`)로 외부 창에서 결제, Deep Link으로 결과 수신 |
| 결제 후 앱 복귀 실패 | **중간** (25%) | 결제 확인 불가 | Universal Links (iOS) / App Links (Android) 설정으로 확실한 복귀 보장 |
| Toss SDK가 네이티브 앱에서 차단 | **낮음** (10%) | 결제 수단 변경 | Toss Payments 기술 지원 문의, 필요시 Redirect 방식으로 전환 |
| 보증금/에스크로 결제 UX 분절 | **중간** (20%) | 사용자 이탈 | 결제 중 로딩 UI, 완료 시 앱 내 확인 화면 제공 |

**Toss Payments 네이티브 대응 전략**:

```
[우선 시도] In-App Browser 방식
  1. 서버에서 결제 URL 생성 (Toss checkout URL)
  2. Capacitor Browser.open()으로 외부 브라우저 오픈
  3. successUrl을 pilamatch:// Deep Link로 설정
  4. 결제 완료 시 앱으로 자동 복귀

[대안] Server-to-Server 방식
  1. 앱에서 카드 정보 직접 입력 (PCI-DSS 필요 → 비현실적)
  → Toss Payments Redirect 방식 사용 권장

[최종 대안] 수동 확인 방식
  1. 결제 후 앱에서 "결제 완료 확인" 버튼 제공
  2. 서버에서 Toss API로 결제 상태 확인
```

### 5.4 프리미엄 구독 IAP 전환 복잡성

| 리스크 | 발생 확률 | 영향도 | 대응 방안 |
|--------|----------|--------|----------|
| IAP + Toss 이중 결제 시스템 관리 | **확실** (100%) | 운영 복잡도 증가 | RevenueCat으로 IAP 관리 통합, 서버에서 결제 소스 통합 관리 |
| 기존 Toss 구독자 마이그레이션 | **확실** (100%) | 사용자 혼란 | 웹 기존 구독자는 Toss 유지, 앱 신규 구독만 IAP |
| Apple/Google 영수증 검증 서버 구현 | **확실** (100%) | 개발 공수 추가 | RevenueCat Server-to-Server webhook 활용 |
| 구독 상태 불일치 (서버 vs Apple/Google) | **중간** (30%) | 결제 분쟁 | Server Notifications (Apple) / RTDN (Google) 실시간 수신 |
| 환불 처리 | **중간** (20%) | CS 부담 | Apple/Google 환불은 스토어에서 자동 처리, 서버에서 상태 반영만 |

**IAP 서버 아키텍처**:

```
┌──────────────────────────────────────────────────────────────┐
│                    구독 관리 아키텍처                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  [웹 사용자]                [앱 사용자]                        │
│      │                         │                              │
│      v                         v                              │
│  Toss Payments             Apple IAP / Google Play Billing   │
│      │                         │                              │
│      v                         v                              │
│  ┌─────────────────────────────────────────────────┐         │
│  │           FastAPI - SubscriptionService          │         │
│  │  ┌─────────────┐  ┌───────────────────────────┐ │         │
│  │  │ Toss 결제    │  │ IAP 영수증 검증            │ │         │
│  │  │ (기존 유지)   │  │ (Apple/Google Server API) │ │         │
│  │  └──────┬──────┘  └────────────┬──────────────┘ │         │
│  │         │                      │                 │         │
│  │         v                      v                 │         │
│  │  ┌─────────────────────────────────────────┐    │         │
│  │  │     Subscription 테이블 (통합 관리)       │    │         │
│  │  │  payment_source: 'toss' | 'apple' | 'google' │         │
│  │  │  status: active | cancelled | expired    │    │         │
│  │  └─────────────────────────────────────────┘    │         │
│  └─────────────────────────────────────────────────┘         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 5.5 리스크 우선순위 종합

```
[즉시 대응 필요 - P0]
  1. 프리미엄 구독 IAP 전환 설계 (Apple 심사 필수)
  2. 네이티브 기능 추가 계획 (Minimum Functionality 대응)
  3. 인증 방식 전환 코드 작성 (BFF -> Direct API)

[출시 전 해결 - P1]
  4. Toss Payments 네이티브 결제 플로우 검증
  5. 키보드/레이아웃 모바일 최적화
  6. 개인정보처리방침 웹 URL 배포

[출시 후 개선 가능 - P2]
  7. WebView 성능 최적화
  8. 기존 Toss 구독자 IAP 마이그레이션
  9. 추가 네이티브 기능 (캘린더, 위치, 공유)
```

---

## 부록: 핵심 참조 파일

| 파일 경로 | 용도 |
|-----------|------|
| `/home/jkcho/PilaMatch/frontend-next/next.config.ts` | 현재 빌드 설정 (수정 대상) |
| `/home/jkcho/PilaMatch/frontend-next/package.json` | 의존성 관리 (Capacitor 추가 대상) |
| `/home/jkcho/PilaMatch/frontend-next/public/manifest.json` | PWA 매니페스트 (Capacitor가 대체) |
| `/home/jkcho/PilaMatch/frontend-next/src/lib/api-client.ts` | API 클라이언트 (플랫폼 분기 대상) |
| `/home/jkcho/PilaMatch/frontend-next/src/middleware.ts` | BFF 인증 미들웨어 (네이티브에서 미사용) |
| `/home/jkcho/PilaMatch/frontend-next/src/app/api/auth/login/route.ts` | BFF 로그인 (네이티브에서 미사용) |
| `/home/jkcho/PilaMatch/frontend-next/src/components/payment/toss-payment-widget.tsx` | 결제 위젯 (네이티브 분기 필요) |
| `/home/jkcho/PilaMatch/backend/app/services/subscription.py` | 구독 서비스 (IAP 검증 확장) |
| `/home/jkcho/PilaMatch/docs/store-description-ko.md` | 앱스토어 설명 (작성 완료) |
| `/home/jkcho/PilaMatch/docs/privacy-policy-ko.md` | 개인정보처리방침 (작성 완료) |
| `/home/jkcho/PilaMatch/docs/terms-of-service-ko.md` | 이용약관 (작성 완료) |

---

*최종 수정: 2026-02-28*
