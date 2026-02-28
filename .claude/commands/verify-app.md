앱이 정상 동작하는지 전체 검증해:

1. **서비스 상태 확인**:
   ```bash
   docker-compose ps
   curl -s http://localhost:8000/api/v1/docs | head -5
   curl -s http://localhost:8501 | head -5
   ```

2. **핵심 API 헬스체크**:
   ```bash
   # 인증
   curl -s -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"Test1234!","role":"instructor"}'

   # 공고 목록
   curl -s http://localhost:8000/api/v1/jobs | head -20
   ```

3. **DB 상태 확인**:
   ```bash
   docker-compose exec db psql -U postgres -d pilamatch -c "SELECT COUNT(*) FROM users;"
   ```

4. **결과 리포트**:
   - 각 서비스 상태 (pass/fail)
   - 발견된 문제 severity별 정리 (Critical/Warning/Info)
   - 수정 제안
