import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PrivacyPage from '@/app/(legal)/privacy/page';
import TermsPage from '@/app/(legal)/terms/page';
import RefundPage from '@/app/(legal)/refund/page';
import LegalLayout from '@/app/(legal)/layout';

describe('Legal Pages', () => {
  describe('LegalLayout', () => {
    it('renders children with navigation', () => {
      render(
        <LegalLayout>
          <p>test content</p>
        </LegalLayout>,
      );
      expect(screen.getByText('test content')).toBeInTheDocument();
      expect(screen.getByText('StudioBridge')).toBeInTheDocument();
      expect(screen.getByText('홈으로 돌아가기')).toBeInTheDocument();
    });

    it('has back button link to home', () => {
      render(
        <LegalLayout>
          <p>child</p>
        </LegalLayout>,
      );
      const backText = screen.getByText('뒤로가기');
      const link = backText.closest('a');
      expect(link).toHaveAttribute('href', '/');
    });
  });

  describe('PrivacyPage', () => {
    it('renders privacy policy title', () => {
      render(<PrivacyPage />);
      expect(screen.getByText('개인정보처리방침')).toBeInTheDocument();
    });

    it('contains required PIPA sections', () => {
      render(<PrivacyPage />);
      expect(screen.getByText(/수집하는 개인정보 항목/)).toBeInTheDocument();
      expect(screen.getByText(/수집 및 이용 목적/)).toBeInTheDocument();
      expect(screen.getByText(/보유 및 이용 기간/)).toBeInTheDocument();
      expect(screen.getByText(/제3자 제공/)).toBeInTheDocument();
      expect(screen.getByText(/파기 절차 및 방법/)).toBeInTheDocument();
    });

    it('lists third-party providers', () => {
      render(<PrivacyPage />);
      expect(screen.getByText(/TossPayments/)).toBeInTheDocument();
      expect(screen.getByText(/CoolSMS/)).toBeInTheDocument();
    });

    it('lists collected data items', () => {
      render(<PrivacyPage />);
      expect(screen.getByText(/이메일 주소/)).toBeInTheDocument();
      expect(screen.getAllByText(/휴대전화번호/).length).toBeGreaterThan(0);
      expect(screen.getByText(/사업자등록번호/)).toBeInTheDocument();
    });
  });

  describe('TermsPage', () => {
    it('renders terms of service title', () => {
      render(<TermsPage />);
      expect(screen.getByText('이용약관')).toBeInTheDocument();
    });

    it('contains key sections', () => {
      render(<TermsPage />);
      expect(screen.getByText(/서비스의 정의/)).toBeInTheDocument();
      expect(screen.getByText(/회원의 의무/)).toBeInTheDocument();
      expect(screen.getAllByText(/금지행위/).length).toBeGreaterThan(0);
      expect(screen.getByText(/결제 및 환불/)).toBeInTheDocument();
      expect(screen.getByText(/제7조 \(노쇼 패널티\)/)).toBeInTheDocument();
      expect(screen.getByText(/제9조 \(계정 정지 및 해지\)/)).toBeInTheDocument();
    });

    it('mentions deposit and penalty amounts', () => {
      render(<TermsPage />);
      expect(screen.getByText(/50,000원/)).toBeInTheDocument();
      expect(screen.getAllByText(/30,000원/).length).toBeGreaterThan(0);
    });
  });

  describe('RefundPage', () => {
    it('renders refund policy title', () => {
      render(<RefundPage />);
      expect(screen.getByText('환불정책')).toBeInTheDocument();
    });

    it('contains escrow refund rules', () => {
      render(<RefundPage />);
      expect(screen.getByText(/100% 전액 환불/)).toBeInTheDocument();
      expect(screen.getByText(/양 당사자 협의/)).toBeInTheDocument();
    });

    it('contains subscription refund rules', () => {
      render(<RefundPage />);
      expect(screen.getAllByText(/9,900원/).length).toBeGreaterThan(0);
      expect(screen.getByText(/7일 이내 전액/)).toBeInTheDocument();
    });

    it('contains dispute resolution process', () => {
      render(<RefundPage />);
      expect(screen.getByText(/분쟁 신고/)).toBeInTheDocument();
      expect(screen.getByText(/운영자 중재/)).toBeInTheDocument();
    });
  });
});
