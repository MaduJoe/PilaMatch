# 프로젝트 컨텍스트

## 페르소나
너는 한국 SMS/인증 서비스 개발에 정통한 시니어 백엔드 개발자야.
CoolSMS(solapi) API를 실무에서 다뤄봤고,
휴대폰 본인인증, OTP 발송, 인증번호 검증 플로우를 깊이 이해하고 있어.
보안 취약점(브루트포스, 인증번호 노출)에 민감하고,
Redis를 활용한 TTL 기반 인증 상태 관리를 항상 고려해.

## 기술 스택
- Backend: Node.js / NestJS  # 실제 스택으로 교체
- SMS: CoolSMS (solapi) SDK
- Cache: Redis (인증번호 임시 저장)
- DB: PostgreSQL

## 인증 관련 컨벤션
- 인증번호는 6자리 숫자
- TTL: 3분 (180초)
- 최대 재시도 횟수: 5회 초과 시 잠금
- 전화번호는 E.164 포맷으로 정규화 (+82XXXXXXXXXX)
- 인증번호는 절대 로그에 남기지 않음
```

---

## 2. Plan Mode 진입 및 요청 방법

**Plan Mode 진입:** `Shift + Tab` 두 번
```
CoolSMS를 이용한 SMS 인증 서비스를 구현하려 해.
코드 작성 전에 프로젝트 구조를 파악하고 구체적인 구현 플랜을 잡아줘.

요구사항:
- 인증번호 발송 API (POST /auth/sms/send)
- 인증번호 검증 API (POST /auth/sms/verify)
- Redis TTL 기반 인증 상태 관리 (3분 만료)
- 브루트포스 방어 (5회 실패 시 잠금)
- 동일 번호 재발송 쿨타임 (1분)

플랜에 반드시 포함할 것:
1. 디렉토리/파일 구조
2. Redis 키 설계 (auth:sms:{phone}, auth:sms:lock:{phone})
3. 환경변수 목록 (COOLSMS_API_KEY, COOLSMS_API_SECRET 등)
4. 각 API 요청/응답 스펙
5. 예외처리 시나리오 (발송 실패, 만료, 잠금 등)
6. 테스트 전략 (실제 발송 없이 mock 처리)

공식 문서 참고: https://docs.coolsms.co.kr
```

---

## 3. 단계별 워크플로우

**Phase 1 - 코드베이스 탐색 (Plan Mode)**
```
현재 프로젝트의 인증/미들웨어 구조를 먼저 파악하고
CoolSMS 연동을 어느 레이어에 붙이는 게 적합한지 제안해줘.
기존 auth 모듈이 있다면 충돌 없이 확장하는 방향으로.
```

**Phase 2 - 보안 검토 요청 (Plan Mode)**
```
위 플랜에서 보안 취약점을 시니어 보안 엔지니어 관점으로 리뷰해줘.
특히 인증번호 노출, 레이트 리미팅, Redis 키 충돌 가능성을 중점적으로 봐줘.
```

**Phase 3 - 플랜 확정 후 실행**

`Shift + Tab`으로 일반 모드 전환 후:
```
승인된 플랜대로 구현해줘.
- CoolSMS API 키는 반드시 환경변수로 분리
- 인증번호는 로그 출력 금지
- 각 함수마다 JSDoc 주석 포함
```

---

## 4. Redis 키 설계 예시 (플랜에 포함 요청할 것)

플랜 단계에서 Claude에게 아래 구조로 검토하도록 명시하면 좋아요:
```
auth:sms:code:{phone}    → 인증번호 (TTL 180초)
auth:sms:verified:{phone} → 인증 완료 여부 (TTL 600초)
auth:sms:attempt:{phone} → 실패 횟수 (TTL 600초)
auth:sms:cooldown:{phone} → 재발송 쿨타임 (TTL 60초)