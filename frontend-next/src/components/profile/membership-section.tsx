'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api-client';
import { APIError } from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import { PREMIUM_BENEFITS, PREMIUM_PRICE } from '@/lib/constants';
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
import { Crown, Star } from 'lucide-react';

export function MembershipSection() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [orderData, setOrderData] = useState<{
    order_id: string;
    amount: number;
    client_key: string;
    subscription_id: string;
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
    },
    onError: (error: Error) => {
      toast.error(
        error instanceof APIError ? error.message : '결제 확인 실패',
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

          {!orderData ? (
            <Button
              className="min-h-[44px] w-full"
              onClick={() => initUpgrade.mutate()}
              disabled={initUpgrade.isPending}
            >
              {initUpgrade.isPending ? '결제를 준비하는 중...' : '결제 진행'}
            </Button>
          ) : (
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
              {/* Mock Payment for development */}
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
                    : '결제 완료 (Mock)'}
                </Button>
                <Button
                  variant="outline"
                  className="min-h-[44px] w-full"
                  onClick={() => {
                    setOrderData(null);
                    setShowUpgrade(false);
                  }}
                >
                  결제 취소
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
