'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { formatCurrency, isTossPaymentsMockMode } from '@/lib/utils';
import { MockPaymentWidget } from './mock-payment-widget';
import { CreditCard, Loader2 } from 'lucide-react';

interface TossPaymentWidgetProps {
  clientKey: string;
  orderId: string;
  orderName: string;
  amount: number;
  customerKey?: string;
  onSuccess: (paymentKey: string, orderId: string, amount: number) => void;
  onCancel: () => void;
  isProcessing?: boolean;
}

export function TossPaymentWidget({
  clientKey,
  orderId,
  orderName,
  amount,
  customerKey,
  onSuccess,
  onCancel,
  isProcessing = false,
}: TossPaymentWidgetProps) {
  const [sdkLoaded, setSdkLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const paymentWidgetRef = useRef<any>(null);
  const paymentMethodsRef = useRef<HTMLDivElement>(null);

  // Check if we should use mock mode
  const isMock = isTossPaymentsMockMode() || !clientKey || clientKey.length < 20 || clientKey.includes('xxxx');

  useEffect(() => {
    if (isMock) return;

    // Load TossPayments SDK
    const script = document.createElement('script');
    script.src = 'https://js.tosspayments.com/v2/standard';
    script.async = true;
    script.onload = () => setSdkLoaded(true);
    script.onerror = () => setError('결제 SDK를 불러올 수 없습니다');
    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, [isMock]);

  useEffect(() => {
    if (!sdkLoaded || isMock || !paymentMethodsRef.current) return;

    async function initWidget() {
      try {
        const tossPayments = (window as any).TossPayments(clientKey);
        const widgets = tossPayments.widgets({ customerKey: customerKey || 'guest' });
        paymentWidgetRef.current = widgets;

        await widgets.setAmount({ currency: 'KRW', value: amount });
        await widgets.renderPaymentMethods({
          selector: '#payment-methods',
          variantKey: 'DEFAULT',
        });
      } catch (err) {
        setError('결제 위젯을 초기화할 수 없습니다');
        console.error('TossPayments init error:', err);
      }
    }

    initWidget();
  }, [sdkLoaded, isMock, clientKey, customerKey, amount]);

  // Mock mode
  if (isMock) {
    return (
      <MockPaymentWidget
        orderId={orderId}
        orderName={orderName}
        amount={amount}
        onSuccess={onSuccess}
        onCancel={onCancel}
        isProcessing={isProcessing}
      />
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="border-red-200">
        <CardContent className="py-6 text-center">
          <p className="text-sm text-red-500">{error}</p>
          <Button variant="outline" className="mt-3" onClick={onCancel}>
            돌아가기
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Real Toss widget
  const handlePayment = async () => {
    if (!paymentWidgetRef.current) return;

    try {
      await paymentWidgetRef.current.requestPayment({
        orderId,
        orderName,
        successUrl: `${window.location.origin}/payment/success`,
        failUrl: `${window.location.origin}/payment/fail`,
      });
    } catch (err: any) {
      if (err.code === 'USER_CANCEL') {
        onCancel();
      } else {
        setError(err.message || '결제 요청에 실패했습니다');
      }
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <CreditCard className="h-4 w-4" />
          결제
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-center">
          <p className="text-sm text-gray-500">{orderName}</p>
          <p className="text-2xl font-bold">{formatCurrency(amount)}</p>
        </div>

        {!sdkLoaded ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            <span className="ml-2 text-sm text-gray-500">결제 위젯 로딩 중...</span>
          </div>
        ) : (
          <div id="payment-methods" ref={paymentMethodsRef} />
        )}

        <div className="flex gap-2">
          <Button
            className="flex-1"
            onClick={handlePayment}
            disabled={!sdkLoaded || isProcessing}
          >
            {isProcessing ? '처리 중...' : `${formatCurrency(amount)} 결제하기`}
          </Button>
          <Button variant="outline" onClick={onCancel}>
            취소
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
