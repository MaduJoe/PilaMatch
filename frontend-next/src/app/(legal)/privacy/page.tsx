import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '개인정보처리방침 - StudioBridge',
};

export default function PrivacyPage() {
  return (
    <article className="prose prose-sm max-w-none dark:prose-invert">
      <h1>개인정보처리방침</h1>
      <p className="text-muted-foreground">시행일: 2026년 2월 26일</p>

      <p>
        StudioBridge(이하 &quot;회사&quot;)는 개인정보보호법 등 관련 법령에 따라
        이용자의 개인정보를 보호하고 이와 관련한 고충을 신속하고 원활하게
        처리하기 위해 다음과 같이 개인정보처리방침을 수립·공개합니다.
      </p>

      <h2>제1조 (수집하는 개인정보 항목)</h2>
      <p>회사는 서비스 제공을 위해 다음의 개인정보를 수집합니다.</p>
      <h3>필수 수집 항목</h3>
      <ul>
        <li><strong>회원가입</strong>: 이메일 주소, 비밀번호, 역할(강사/스튜디오)</li>
        <li><strong>본인인증</strong>: 휴대전화번호</li>
        <li><strong>사업자인증</strong>: 사업자등록번호, 업체명</li>
        <li><strong>결제</strong>: 결제수단 정보(카드번호, 계좌번호 등은 결제대행사가 직접 처리)</li>
      </ul>
      <h3>선택 수집 항목</h3>
      <ul>
        <li>프로필 사진, 자기소개, 자격증, 경력, 활동 지역</li>
      </ul>

      <h2>제2조 (개인정보의 수집 및 이용 목적)</h2>
      <ul>
        <li>회원 가입 및 관리: 본인 확인, 가입 의사 확인, 서비스 부정 이용 방지</li>
        <li>서비스 제공: 강사-스튜디오 매칭, 계약 체결 및 관리, 리뷰 시스템</li>
        <li>결제 및 정산: 에스크로 결제, 보증금 관리, 프리미엄 구독 관리</li>
        <li>고객 지원: 문의 응대, 분쟁 해결, 공지사항 전달</li>
        <li>서비스 개선: 이용 통계 분석, 서비스 품질 향상</li>
      </ul>

      <h2>제3조 (개인정보의 보유 및 이용 기간)</h2>
      <p>
        회사는 법령에 따른 보유 기간 또는 이용자로부터 동의받은 기간 동안
        개인정보를 보유·이용합니다.
      </p>
      <ul>
        <li>회원 정보: 회원 탈퇴 시까지 (탈퇴 후 30일간 복구 목적 보관)</li>
        <li>계약 및 결제 기록: 전자상거래법에 따라 <strong>5년</strong></li>
        <li>로그인 기록: 통신비밀보호법에 따라 <strong>3개월</strong></li>
        <li>소비자 불만·분쟁 기록: 전자상거래법에 따라 <strong>3년</strong></li>
      </ul>

      <h2>제4조 (개인정보의 제3자 제공)</h2>
      <p>
        회사는 이용자의 동의 없이 개인정보를 제3자에게 제공하지 않습니다.
        다만, 다음의 경우에는 예외로 합니다.
      </p>
      <table>
        <thead>
          <tr>
            <th>제공받는 자</th>
            <th>제공 목적</th>
            <th>제공 항목</th>
            <th>보유 기간</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>토스페이먼츠(TossPayments)</td>
            <td>결제 처리, 에스크로, 정기결제</td>
            <td>결제 관련 정보</td>
            <td>결제 완료 후 5년</td>
          </tr>
          <tr>
            <td>CoolSMS</td>
            <td>본인인증 SMS 발송</td>
            <td>휴대전화번호</td>
            <td>인증 완료 후 즉시 파기</td>
          </tr>
        </tbody>
      </table>

      <h2>제5조 (개인정보의 파기 절차 및 방법)</h2>
      <ol>
        <li>
          <strong>파기 절차</strong>: 이용 목적이 달성된 개인정보는 별도의
          DB로 옮겨져 내부 방침 및 법령에 따라 일정 기간 보관 후 파기됩니다.
        </li>
        <li>
          <strong>파기 방법</strong>: 전자적 파일은 복구 불가능한 방법으로
          삭제하며, 종이 문서는 분쇄기로 분쇄합니다.
        </li>
      </ol>

      <h2>제6조 (이용자의 권리 및 행사 방법)</h2>
      <p>이용자는 다음의 권리를 행사할 수 있습니다.</p>
      <ul>
        <li>개인정보 열람, 정정, 삭제, 처리 정지 요구</li>
        <li>회원 탈퇴를 통한 개인정보 삭제 (서비스 내 설정에서 가능)</li>
        <li>이메일 또는 고객 지원을 통한 권리 행사</li>
      </ul>

      <h2>제7조 (개인정보 보호책임자)</h2>
      <ul>
        <li>책임자: StudioBridge 개인정보 보호팀</li>
        <li>이메일: privacy@studiobridge.kr</li>
      </ul>

      <h2>제8조 (개인정보처리방침의 변경)</h2>
      <p>
        이 개인정보처리방침은 법령 및 방침에 따라 변경될 수 있으며, 변경 시
        서비스 내 공지사항을 통해 안내드립니다.
      </p>
    </article>
  );
}
