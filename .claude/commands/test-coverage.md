커버리지 분석을 수행해:

1. 실행:
   ```bash
   cd backend && uv run pytest --cov=app --cov-report=term-missing -q 2>&1 | tail -40
   ```

2. 커버리지 80% 미만인 파일 식별

3. 가장 중요한 미커버 파일 TOP 3에 대해:
   - 누락된 테스트 케이스 제안
   - 우선순위 표시 (P0/P1/P2)

4. 전체 커버리지 요약 테이블 출력
