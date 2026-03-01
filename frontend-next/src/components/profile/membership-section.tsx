'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api-client';
import { APIError } from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
// PMF pivot: Premium disabled -- constants commented out in constants.ts
// import { PREMIUM_BENEFITS, PREMIUM_PRICE } from '@/lib/constants';
// Local fallback for compilation; this component should not be rendered during pivot.
const PREMIUM_PRICE = 9900;
const PREMIUM_BENEFITS = {
  instructor: [
    { icon: 'rocket', title: '무제한 일일 지원', desc: '하루 5회 -> 무제한' },
  ],
  studio: [
    { icon: 'eye', title: '무제한 강사 프로필 열람', desc: '하루 5명 -> 무제한' },
  ],
} as const;
import { formatCurrency } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { PaymentMethodSelector } from '@/components/payment/payment-method-selector';
import { BankTransferInfo } from '@/components/payment/bank-transfer-info';
import { Crown, Star } from 'lucide-react';

export function MembershipSection() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [showBankTransfer, setShowBankTransfer] = useState(false);
  const [orderData, setOrderData] = useState<{
    order_id: string;
    amount: number;
    client_key: string;
    subscription_id: string;
  } | null>(null);
  const [bankTransferData, setBankTransferData] = useState<{
    order_id: string;
    amount: number;
    bank_name: string;
    account_number: string;
    account_holder: string;
    depositor_name: string;
    expires_at: string;
  } | null>(null);

  const { data: subscription, isLoading } = useQuery({
    queryKey: ['subscription', 'status'],
    queryFn: () => api.subscriptions.getStatus(),
  });

  const initUpgrade = useMutation({
    mutationFn: () => api.subscriptions.initializeUpgrade(),
    onSuccess: (data) => {
      setOrderData({
        order_id: data.order_id,
        amount: data.amount,
        client_key: data.client_key,
        subscription_id: data.subscription_id,
      });
    },
    onError: (error: Error) => {
      toast.error(
        error instanceof APIError ? error.message : '결제 준비 실패',
      );
    },
  });

  const cancelSub = useMutation({
    mutationFn: () => api.subscriptions.cancel('User requested'),
    onSuccess: () => {
      toast.success('구독이 취소되었습니다');
      queryClient.invalidateQueries({ queryKey: ['subscription'] });
      queryClient.invalidateQueries({ queryKey: ['trustScore'] });
    },
    onError: (error: Error) => {
      toast.error(
        error instanceof APIError ? error.message : '구독 취소 실패',
      );
    },
  });

  const confirmPayment = useMutation({
    mutationFn: (data: { payment_key: string; order_id: string }) =>
      api.subscriptions.confirmPayment(data),
    onSuccess: () => {
      toast.success('프리미엄 회원이 되신 것을 축하합니다!');
      setShowUpgrade(false);
      setOrderData(null);
      queryClient.invalidateQueries({ queryKey: ['subscription'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      queryClient.invalidateQueries({ queryKey: ['trustScore'] });
    },
    onError: (error: Error) => {
      toast.error(
        error instanceof APIError ? error.message : '결제 확인 실패',
      );
    },
  });

  const initBankTransfer = useMutation({
    mutationFn: (depositorName: string) =>
      api.subscriptions.initBankTransfer({ depositor_name: depositorName }),
    onSuccess: (data) => {
      setBankTransferData(data);
    },
    onError: (error: Error) => {
      toast.error(
        error instanceof APIError ? error.message : '무통장입금 초기화 실패',
      );
    },
  });

  if (isLoading || !user) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </CardContent>
      </Card>
    );
  }

  const isPremium = subscription?.membership_tier === 'premium';
  const role = user.role as 'instructor' | 'studio';
  const benefits = PREMIUM_BENEFITS[role] || PREMIUM_BENEFITS.instructor;

  return (
    <>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            멤버십 상태
            {isPremium ? (
              <Badge className="bg-yellow-100 text-yellow-800">
                <Crown className="mr-1 h-3 w-3" aria-hidden="true" />
                프리미엄
              </Badge>
            ) : (
              <Badge variant="secondary">무료</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {isPremium ? (
            <>
              <div className="space-y-2">
                <p className="text-sm font-medium text-green-700 dark:text-green-400">
                  현재 누리는 혜택:
                </p>
                {benefits.map((b, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <div>
                      <span className="font-medium">{b.title}</span>
                      <span className="text-muted-foreground"> - {b.desc}</span>
                    </div>
                  </div>
                ))}
              </div>
              {subscription?.subscription?.next_billing_date && (
                <p className="text-xs text-muted-foreground">
                  다음 결제일:{' '}
                  {new Date(
                    subscription.subscription.next_billing_date,
                  ).toLocaleDateString('ko-KR')}
                </p>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => cancelSub.mutate()}
                disabled={cancelSub.isPending}
                className="min-h-[44px]"
              >
                {cancelSub.isPending ? '취소 중...' : '구독 취소'}
              </Button>
            </>
          ) : (
            <>
              <div className="space-y-2">
                <p className="text-sm font-medium">
                  프리미엄 혜택 (월 {formatCurrency(PREMIUM_PRICE)}):
                </p>
                {benefits.map((b, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <div>
                      <span className="font-medium">{b.title}</span>
                      <span className="text-muted-foreground"> - {b.desc}</span>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                className="min-h-[44px] w-full"
                onClick={() => setShowUpgrade(true)}
              >
                <Star className="mr-2 h-4 w-4" aria-hidden="true" />
                프리미엄 업그레이드
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* Upgrade Dialog */}
      <Dialog open={showUpgrade} onOpenChange={setShowUpgrade}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>프리미엄 멤버십 결제</DialogTitle>
            <DialogDescription>
              월 {formatCurrency(PREMIUM_PRICE)}으로 더 빠른 계약 성공을
              경험하세요!
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            {benefits.map((b, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <span>
                  {b.title} - {b.desc}
                </span>
              </div>
            ))}
          </div>

          <PaymentMethodSelector
            isLoading={initUpgrade.isPending}
            onSelect={(method) => {
              if (method === 'card') {
                initUpgrade.mutate();
              } else {
                setShowUpgrade(false);
                setShowBankTransfer(true);
              }
            }}
          />

          {orderData && (
            <div className="space-y-3">
              <div className="rounded-lg border bg-muted/50 p-4 text-center">
                <p className="text-sm text-muted-foreground">결제 금액</p>
                <p className="text-2xl font-bold">
                  {formatCurrency(orderData.amount)}
                </p>
                <p className="text-xs text-muted-foreground">
                  주문번호: {orderData.order_id}
                </p>
              </div>
              <div className="space-y-2">
                <Button
                  className="min-h-[44px] w-full"
                  onClick={() =>
                    confirmPayment.mutate({
                      payment_key: `mock_${Date.now()}`,
                      order_id: orderData.order_id,
                    })
                  }
                  disabled={confirmPayment.isPending}
                >
                  {confirmPayment.isPending
                    ? '결제 확인 중...'
                    : '결제 완료'}
                </Button>
                <Button
                  variant="outline"
                  className="min-h-[44px] w-full"
                  onClick={() => {
                    setOrderData(null);
                    setShowUpgrade(false);
                  }}
                >
                  취소
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Bank Transfer Dialog */}
      <Dialog open={showBankTransfer} onOpenChange={setShowBankTransfer}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>무통장입금</DialogTitle>
            <DialogDescription>
              아래 계좌로 입금해주시면 관리자 확인 후 프리미엄이 활성화됩니다.
            </DialogDescription>
          </DialogHeader>

          {!bankTransferData ? (
            <div className="space-y-3">
              <div className="space-y-2">
                <label className="text-sm font-medium">입금자명</label>
                <Input
                  placeholder="홍길동"
                  id="depositor-name"
                  aria-label="입금자명"
                  className="min-h-[44px]"
                />
              </div>
              <Button
                className="min-h-[44px] w-full"
                onClick={() => {
                  const input = document.getElementById('depositor-name') as HTMLInputElement;
                  if (input?.value) {
                    initBankTransfer.mutate(input.value);
                  }
                }}
                disabled={initBankTransfer.isPending}
              >
                {initBankTransfer.isPending ? '처리 중...' : '입금 안내 받기'}
              </Button>
            </div>
          ) : (
            <BankTransferInfo
              bankName={bankTransferData.bank_name}
              accountNumber={bankTransferData.account_number}
              accountHolder={bankTransferData.account_holder}
              amount={bankTransferData.amount}
              depositorName={bankTransferData.depositor_name}
              expiresAt={bankTransferData.expires_at}
              orderId={bankTransferData.order_id}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
