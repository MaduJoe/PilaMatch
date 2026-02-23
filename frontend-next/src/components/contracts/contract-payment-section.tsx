'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { CreditCard, Loader2, Lock, XCircle } from 'lucide-react';
import api, { APIError } from '@/lib/api-client';
import type { ContractResponse, PaymentInitResponse } from '@/lib/api-types';
import { formatCurrency } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { MockPaymentWidget } from '@/components/payment/mock-payment-widget';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ContractPaymentSectionProps {
  contract: ContractResponse;
  onAction: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ContractPaymentSection({
  contract,
  onAction,
}: ContractPaymentSectionProps) {
  const [orderData, setOrderData] = useState<PaymentInitResponse | null>(null);
  const [confirming, setConfirming] = useState(false);

  // ---- Initialize payment ---------------------------------------------------
  const initMutation = useMutation({
    mutationFn: () => api.payments.initialize(contract.id),
    onSuccess: (data) => {
      setOrderData(data);
    },
    onError: (error: Error) => {
      toast.error(
        error instanceof APIError
          ? error.message
          : '결제 초기화에 실패했습니다.',
      );
    },
  });

  // ---- Confirm payment (after mock or Toss widget callback) -----------------
  async function handlePaymentSuccess(
    paymentKey: string,
    orderId: string,
    amount: number,
  ) {
    setConfirming(true);
    try {
      await api.payments.confirm({ payment_key: paymentKey, order_id: orderId, amount });
      toast.success('결제가 완료되었습니다.');
      setOrderData(null);
      onAction();
    } catch (error) {
      toast.error(
        error instanceof APIError
          ? (error as APIError).message
          : '결제 확인 중 오류가 발생했습니다.',
      );
    } finally {
      setConfirming(false);
    }
  }

  function handleCancel() {
    setOrderData(null);
  }

  // ---- Render: payment widget active ----------------------------------------
  if (orderData) {
    return (
      <div className="space-y-3">
        {/* Escrow trust badge */}
        <div className="flex items-center gap-2 rounded-md border border-blue-200 bg-blue-50 p-2.5 dark:border-blue-900 dark:bg-blue-950/30">
          <Lock className="size-4 shrink-0 text-blue-600" aria-hidden="true" />
          <span className="text-xs text-blue-700 dark:text-blue-300">
            에스크로로 안전하게 보관됩니다
          </span>
        </div>

        <MockPaymentWidget
          orderId={orderData.order_id}
          orderName={orderData.order_name}
          amount={orderData.amount}
          onSuccess={handlePaymentSuccess}
          onCancel={handleCancel}
          isProcessing={confirming}
        />

        {/* Settlement estimate */}
        {contract.settlement_amount != null && (
          <p className="text-center text-xs text-muted-foreground">
            예상 정산액: {formatCurrency(contract.settlement_amount)}
            {contract.platform_fee != null && (
              <span>
                {' '}(수수료 {formatCurrency(contract.platform_fee)})
              </span>
            )}
          </p>
        )}

        {/* Refund policy summary */}
        <p className="text-center text-xs text-muted-foreground">
          수업 시작 24시간 전까지 무료 취소 가능
        </p>

        <Button
          variant="ghost"
          size="sm"
          className="min-h-[44px] w-full"
          onClick={handleCancel}
          aria-label="결제 취소"
        >
          <XCircle className="mr-2 size-4" aria-hidden="true" />
          결제 취소
        </Button>
      </div>
    );
  }

  // ---- Render: initialize button --------------------------------------------
  return (
    <div className="space-y-2">
      <Button
        variant="default"
        className="min-h-[44px] w-full"
        disabled={initMutation.isPending}
        onClick={() => initMutation.mutate()}
        aria-label="계약금 결제하기"
      >
        {initMutation.isPending ? (
          <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
        ) : (
          <CreditCard className="mr-2 size-4" aria-hidden="true" />
        )}
        계약금 결제하기 ({formatCurrency(contract.total_amount)})
      </Button>

      {/* Escrow trust indicator */}
      <div className="flex items-center justify-center gap-1.5">
        <Lock className="size-3 text-muted-foreground" aria-hidden="true" />
        <span className="text-xs text-muted-foreground">
          에스크로로 안전하게 보관됩니다
        </span>
      </div>
    </div>
  );
}
