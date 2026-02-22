결제 및 신뢰 시스템 전체를 집중 테스트해:

1. **관련 테스트 실행**:
   ```bash
   cd backend && uv run pytest tests/test_escrow*.py tests/test_penalty*.py tests/test_deposit*.py tests/test_contract*.py -v 2>&1
   ```

2. **커버리지 확인**:
   ```bash
   cd backend && uv run pytest --cov=app/services/escrow --cov=app/services/penalty --cov=app/services/deposit --cov=app/services/contract --cov-report=term-missing -q 2>&1
   ```

3. **누락 시나리오 확인**:
   - 에스크로: 생성 → 홀드 → 릴리즈 → 정산 전체 플로우
   - 패널티: 노쇼 신고 → 차감 → 누적 → 3회 정지
   - 보증금: 입금 → 잔액 확인 → 차감 → 잔액 부족 시 에러
   - 계약 상태 전이: 모든 valid/invalid 전이 테스트

4. **누락된 테스트가 있으면 작성 후 실행**
