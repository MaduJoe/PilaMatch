# PilaMatch Admin Dashboard Guide

## 개요
PilaMatch Admin Dashboard는 개발자 전용 데이터베이스 관리 인터페이스입니다.
모든 테이블의 데이터를 조회, 수정, 삭제할 수 있는 강력한 도구입니다.

## 접속 방법

### URL
```
http://localhost:8502
```

### 로그인 정보
- **Admin Password**: `admin1234!`

> ⚠️ **주의**: 이 페이지는 개발자만 접근해야 합니다. 프로덕션 환경에서는 더 강력한 비밀번호를 사용하고 IP 제한을 설정하세요.

## 주요 기능

### 1. 📊 Tables (테이블 뷰어)
데이터베이스의 모든 테이블을 그룹별로 조회할 수 있습니다.

#### 테이블 그룹
- **👤 Users & Profiles**: 사용자 및 프로필 관련 테이블
  - `users`: 사용자 계정 정보
  - `instructor_profiles`: 강사 프로필
  - `studio_profiles`: 스튜디오 프로필

- **📋 Jobs & Applications**: 구인/구직 관련 테이블
  - `job_posts`: 구인 공고
  - `applications`: 지원 내역
  - `offers`: 제안 내역

- **📄 Contracts & Payments**: 계약 및 결제 관련 테이블
  - `contracts`: 계약 정보
  - `contract_event_logs`: 계약 상태 변경 로그
  - `payments`: 결제 내역
  - `payouts`: 정산 내역

- **⚠️ Disputes & Reports**: 분쟁 및 신고 관련 테이블
  - `disputes`: 분쟁 내역
  - `reports`: 신고 내역
  - `blocks`: 차단 내역

- **💬 Communication**: 소통 관련 테이블
  - `chat_threads`: 채팅 스레드
  - `chat_messages`: 채팅 메시지
  - `support_tickets`: 고객 지원 티켓

#### 기능
- **Query Builder**: WHERE 절, ORDER BY, LIMIT 설정
- **Data Export**: CSV, JSON 형식으로 내보내기
- **Data Editor**: 직접 데이터 수정 (현재는 읽기 전용)

### 2. 🖥️ SQL Executor (SQL 실행기)
직접 SQL 쿼리를 실행할 수 있습니다.

#### 지원 명령어
- SELECT, INSERT, UPDATE, DELETE
- CREATE, DROP, ALTER (주의!)
- 트랜잭션 지원

#### 자주 사용하는 쿼리 예시

```sql
-- 모든 사용자와 프로필 조회
SELECT u.*, ip.name as instructor_name, sp.business_name
FROM users u
LEFT JOIN instructor_profiles ip ON u.id = ip.user_id
LEFT JOIN studio_profiles sp ON u.id = sp.user_id;

-- 활성 계약 조회
SELECT * FROM contracts WHERE status = 'in_progress';

-- 보증금 잔액 확인
SELECT email, role, deposit_balance, deposit_required, is_early_bird
FROM users
WHERE deposit_balance > 0
ORDER BY deposit_balance DESC;

-- 검토 대기 중인 분쟁
SELECT * FROM disputes WHERE status IN ('open', 'objected');
```

### 3. 📈 Statistics (통계)
데이터베이스의 주요 통계를 한눈에 볼 수 있습니다.

#### 제공 통계
- **User Statistics**: 사용자 유형별 통계
- **Contract Statistics**: 계약 상태별 통계 및 총 거래액
- **Job Post Statistics**: 구인 공고 상태별 통계
- **Dispute Statistics**: 분쟁 유형 및 상태별 통계

#### Recent Activity
- Recent Users: 최근 가입한 사용자
- Recent Contracts: 최근 생성된 계약
- Recent Disputes: 최근 발생한 분쟁

### 4. ⚙️ Utilities (유틸리티)

#### 데이터 정리 기능
- **Delete All Test Accounts**: 테스트 계정 일괄 삭제
- **Clear Old Disputes**: 오래된 분쟁 데이터 삭제
- **Database Info**: PostgreSQL 버전 및 DB 크기 확인

## 테스트 계정 정리

### 테스트 계정 삭제 SQL
```sql
DELETE FROM users
WHERE email LIKE '%test.com%'
   OR email LIKE 'instructor_%'
   OR email LIKE 'studio_%'
   OR email LIKE '%debug%';
```

### 특정 테스트 세션 계정 삭제
```sql
-- 예: Test ID 20260214143135 삭제
DELETE FROM users
WHERE email LIKE '%20260214143135%';
```

## 데이터 수정 시 주의사항

### ⚠️ 위험한 작업
1. **CASCADE 삭제**: users 테이블 삭제 시 연관 데이터 모두 삭제됨
2. **계약 상태 변경**: 잘못된 상태 전환은 시스템 오류 유발
3. **보증금 수정**: 음수 값이나 잘못된 금액 입력 주의

### 안전한 작업 순서
1. 항상 SELECT로 먼저 조회
2. WHERE 조건 정확히 확인
3. 트랜잭션 사용 (BEGIN; ... COMMIT;)
4. 백업 후 작업

## 문제 해결

### Admin 페이지가 안 열릴 때
```bash
# 컨테이너 재시작
docker-compose restart admin

# 로그 확인
docker-compose logs admin --tail 50
```

### 데이터베이스 연결 오류
```bash
# DB 상태 확인
docker-compose ps db

# DB 재시작
docker-compose restart db
```

### 비밀번호 변경
`docker-compose.yml`에서 `ADMIN_PASSWORD` 환경변수 수정:
```yaml
environment:
  - ADMIN_PASSWORD=new_secure_password!
```

## 프로덕션 보안 설정

### 1. 강력한 비밀번호 사용
```bash
export ADMIN_PASSWORD=$(openssl rand -base64 32)
```

### 2. IP 화이트리스트 설정
nginx 설정 예시:
```nginx
location /admin {
    allow 123.456.789.0/24;
    deny all;
    proxy_pass http://localhost:8502;
}
```

### 3. HTTPS 적용
Let's Encrypt 등을 사용하여 SSL 인증서 적용

### 4. 로깅 및 감사
모든 관리자 작업을 로깅하고 정기적으로 검토

---

## Docker 명령어 참고

```bash
# Admin 컨테이너 시작
docker-compose up -d admin

# Admin 컨테이너 중지
docker-compose stop admin

# Admin 컨테이너 로그 보기
docker-compose logs -f admin

# 모든 컨테이너 상태 확인
docker-compose ps
```

---

*Last updated: 2026-02-14*