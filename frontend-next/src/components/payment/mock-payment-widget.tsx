'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatCurrency } from '@/lib/utils';
import { CreditCard } from 'lucide-react';

interface MockPaymentWidgetProps {
  orderId: string;
  orderName: string;
  amount: number;
  onSuccess: (paymentKey: string, orderId: string, amount: number) => void;
  onCancel: () => void;
  isProcessing?: boolean;
}

export function MockPaymentWidget({
  orderId,
  orderName,
  amount,
  onSuccess,
  onCancel,
  isProcessing = false,
}: MockPaymentWidgetProps) {
  const handleComplete = () => {
    const mockPaymentKey = `mock_pk_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    onSuccess(mockPaymentKey, orderId, amount);
  };

  return (
    <Card className="border-dashed border-yellow-300 bg-yellow-50">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <CreditCard className="h-4 w-4" />
          결제 (테스트 모드)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md bg-white p-3 text-center">
          <p className="text-sm text-gray-500">{orderName}</p>
          <p className="text-2xl font-bold">{formatCurrency(amount)}</p>
          <p className="text-xs text-gray-400">주문번호: {orderId}</p>
        </div>
        <p className="text-center text-xs text-yellow-600">
          테스트 환경에서는 실제 결제가 진행되지 않습니다
        </p>
        <div className="flex gap-2">
          <Button
            className="flex-1"
            onClick={handleComplete}
            disabled={isProcessing}
          >
            {isProcessing ? '처리 중...' : '결제 완료'}
          </Button>
          <Button
            variant="outline"
            className="flex-1"
            onClick={onCancel}
            disabled={isProcessing}
          >
            취소
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
