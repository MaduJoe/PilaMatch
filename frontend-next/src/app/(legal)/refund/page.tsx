import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '환불정책 - PilaMatch',
};

export default function RefundPage() {
  return (
    <article className="prose prose-sm max-w-none dark:prose-invert">
      <h1>환불정책</h1>
      <p className="text-muted-foreground">시행일: 2026년 2월 26일</p>

      <p>
        PilaMatch(이하 &quot;회사&quot;)는 이용자의 권익 보호를 위해 다음과
        같은 환불정책을 운영합니다.
      </p>

      <h2>제1조 (에스크로 결제 환불)</h2>
      <p>
        에스크로 결제는 계약 완료 전까지 결제 금액을 안전하게 보관하는
        시스템입니다.
      </p>
      <table>
        <thead>
          <tr>
            <th>구분</th>
            <th>환불 비율</th>
            <th>처리 기간</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>계약 시작 전 취소</td>
            <td>100% 전액 환불</td>
            <td>즉시 처리 (영업일 기준 1~3일 내 입금)</td>
          </tr>
          <tr>
            <td>계약 진행 중 취소</td>
            <td>양 당사자 협의에 따라 결정</td>
            <td>협의 완료 후 3영업일 이내</td>
          </tr>
          <tr>
            <td>계약 완료 후</td>
            <td>환불 불가 (정산 완료)</td>
            <td>-</td>
          </tr>
        </tbody>
      </table>

      <h2>제2조 (프리미엄 구독 환불)</h2>
      <p>프리미엄 멤버십(월 9,900원) 구독에 대한 환불 정책입니다.</p>
      <table>
        <thead>
          <tr>
            <th>구분</th>
            <th>환불 비율</th>
            <th>비고</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>결제 후 7일 이내 해지</td>
            <td>전액 환불 (9,900원)</td>
            <td>프리미엄 혜택 미사용 시</td>
          </tr>
          <tr>
            <td>결제 후 7일 초과 해지</td>
            <td>일할 계산 후 잔여분 환불</td>
            <td>사용일수 차감</td>
          </tr>
          <tr>
            <td>자동 갱신 후 취소</td>
            <td>갱신 결제 후 7일 이내 전액 환불</td>
            <td>7일 초과 시 일할 계산</td>
          </tr>
        </tbody>
      </table>
      <p>
        <strong>참고</strong>: 일할 계산 = 9,900원 &times; (잔여일수 / 30일)
      </p>

      <h2>제3조 (보증금 환불)</h2>
      <ul>
        <li>
          <strong>정상 환불</strong>: 서비스 탈퇴 시 미사용 보증금 전액
          환급 (영업일 기준 3~5일 소요)
        </li>
        <li>
          <strong>패널티 차감</strong>: 노쇼 패널티 발생 시 보증금에서 건당
          30,000원 차감
        </li>
        <li>
          <strong>보증금 소진</strong>: 보증금이 0원인 경우 추가 입금 필요
        </li>
      </ul>

      <h2>제4조 (분쟁 기반 환불)</h2>
      <p>
        거래 과정에서 분쟁이 발생한 경우 다음의 절차에 따라 환불이
        진행됩니다.
      </p>
      <ol>
        <li>
          <strong>분쟁 신고</strong>: 서비스 내 고객지원을 통해 분쟁을
          신고합니다.
        </li>
        <li>
          <strong>운영자 중재</strong>: 운영팀이 양 당사자의 주장을 검토하고
          증거를 확인합니다.
        </li>
        <li>
          <strong>중재 결정</strong>: 검토 결과에 따라 전액 환불, 부분 환불,
          또는 환불 거부를 결정합니다.
        </li>
        <li>
          <strong>처리 기간</strong>: 분쟁 접수 후 영업일 기준 7일 이내 결정,
          결정 후 3영업일 이내 환불 처리
        </li>
      </ol>

      <h2>제5조 (환불 불가 사유)</h2>
      <ul>
        <li>이용자의 고의적인 노쇼 또는 약관 위반으로 인한 패널티 차감분</li>
        <li>이미 완료된 계약에 대한 결제 금액</li>
        <li>정상적으로 제공된 서비스에 대한 환불 요청</li>
      </ul>

      <h2>제6조 (환불 신청 방법)</h2>
      <ul>
        <li>서비스 내 설정 &gt; 환불 신청</li>
        <li>이메일: support@pilamatch.kr</li>
      </ul>

      <p>
        환불 처리 후 결제 수단에 따라 입금까지 추가 시간이 소요될 수
        있습니다 (카드 취소: 3~7영업일, 계좌 이체: 1~3영업일).
      </p>
    </article>
  );
}
