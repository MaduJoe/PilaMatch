'use client';

import { useState } from 'react';
import { loadTossPayments } from '@tosspayments/tosspayments-sdk';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Loader2, CreditCard } from 'lucide-react';
import api from '@/lib/api-client';
import { Button } from '@/components/ui/button';

interface TossCheckoutButtonProps {
  /** 사용자 표시 이름 (orderName에 사용) */
  userName?: string;
  /** 사용자 이메일 (결제창에 전달) */
  userEmail?: string;
  /** 버튼 비활성 여부 */
  disabled?: boolean;
}

export function TossCheckoutButton({
  userName,
  userEmail,
  disabled,
}: TossCheckoutButtonProps) {
  const [isOpening, setIsOpening] = useState(false);

  const upgradeMutation = useMutation({
    mutationFn: () => api.subscriptions.initializeUpgrade(),
  });

  const handleCheckout = async () => {
    setIsOpening(true);
    try {
      // 1. 백엔드에서 order_id, client_key, customer_key 발급
      const { order_id, amount, client_key, customer_key } =
        await upgradeMutation.mutateAsync();

      // 2. TossPayments SDK V2 로드
      const tossPayments = await loadTossPayments(client_key);

      // 3. 로그인 고객 결제 인스턴스 생성
      const payment = tossPayments.payment({ customerKey: customer_key! });

      // 4. 카드 + 간편결제 통합 결제창 호출
      await payment.requestPayment({
        method: 'CARD',
        amount: { currency: 'KRW', value: amount },
        orderId: order_id,
        orderName: 'PilaMatch 프리미엄 구독',
        successUrl: `${window.location.origin}/payment/success`,
        failUrl: `${window.location.origin}/payment/fail`,
        customerEmail: userEmail,
        customerName: userName,
        card: {
          useEscrow: false,
          flowMode: 'DEFAULT',
          useCardPoint: false,
        },
      });
    } catch (err: any) {
      // 사용자가 결제창을 닫은 경우 (PAY_PROCESS_CANCELED)
      if (err?.code === 'PAY_PROCESS_CANCELED') {
        return;
      }
      const msg =
        err?.response?.data?.detail?.message ||
        err?.message ||
        '결제 요청에 실패했습니다.';
      toast.error(msg);
    } finally {
      setIsOpening(false);
    }
  };

  const isPending = upgradeMutation.isPending || isOpening;

  return (
    <Button
      className="min-h-[48px] w-full text-base font-display font-semibold"
      onClick={handleCheckout}
      disabled={disabled || isPending}
    >
      {isPending ? (
        <>
          <Loader2 className="mr-2 size-4 animate-spin" />
          결제창 여는 중...
        </>
      ) : (
        <>
          <CreditCard className="mr-2 size-4" />
          프리미엄 구독하기
        </>
      )}
    </Button>
  );
}
