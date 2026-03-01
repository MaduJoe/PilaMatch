'use client';

import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { Loader2, FileText, CheckCircle2, AlertTriangle, Clock } from 'lucide-react';
import { toast } from 'sonner';
import api, { APIError } from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import type { PaymentConfirmationResponse } from '@/lib/api-types';
import { formatCurrency, formatDateTime } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// ---------------------------------------------------------------------------
// Status display helpers
// ---------------------------------------------------------------------------

function getPaymentStatusDisplay(status: string): {
  label: string;
  icon: React.ReactNode;
  variant: 'default' | 'secondary' | 'destructive' | 'outline';
} {
  switch (status) {
    case 'pending':
      return {
        label: '확인 대기',
        icon: <Clock className="size-3.5" aria-hidden="true" />,
        variant: 'secondary',
      };
    case 'confirmed':
      return {
        label: '수령 확인됨',
        icon: <CheckCircle2 className="size-3.5" aria-hidden="true" />,
        variant: 'default',
      };
    case 'disputed':
      return {
        label: '미지급 신고',
        icon: <AlertTriangle className="size-3.5" aria-hidden="true" />,
        variant: 'destructive',
      };
    default:
      return {
        label: status,
        icon: null,
        variant: 'outline',
      };
  }
}

// ---------------------------------------------------------------------------
// Payment Confirmation Card
// ---------------------------------------------------------------------------

function PaymentConfirmationCard({
  confirmation,
  userRole,
  onConfirm,
  onDispute,
  isConfirming,
  isDisputing,
}: {
  confirmation: PaymentConfirmationResponse;
  userRole: string;
  onConfirm: (id: string) => void;
  onDispute: (id: string) => void;
  isConfirming: boolean;
  isDisputing: boolean;
}) {
  const statusDisplay = getPaymentStatusDisplay(confirmation.status);
  const isPending = confirmation.status === 'pending';
  const isInstructor = userRole === 'instructor';

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 p-5">
        {/* Header: amount + status */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col gap-1">
            <p className="text-lg font-bold">
              {formatCurrency(confirmation.amount)}
            </p>
            {confirmation.center_marked_paid_at && (
              <p className="text-xs text-muted-foreground">
                지급 표시: {formatDateTime(confirmation.center_marked_paid_at)}
              </p>
            )}
            {confirmation.instructor_confirmed_at && (
              <p className="text-xs text-muted-foreground">
                수령 확인: {formatDateTime(confirmation.instructor_confirmed_at)}
              </p>
            )}
          </div>
          <Badge
            variant={statusDisplay.variant}
            className="flex items-center gap-1"
            aria-label={`상태: ${statusDisplay.label}`}
          >
            {statusDisplay.icon}
            {statusDisplay.label}
          </Badge>
        </div>

        {/* Dispute reason if present */}
        {confirmation.dispute_reason && (
          <div className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-200">
            사유: {confirmation.dispute_reason}
          </div>
        )}

        {/* Action buttons: instructor can confirm or dispute pending payments */}
        {isPending && isInstructor && (
          <div className="flex gap-2 pt-1">
            <Button
              size="sm"
              className="min-h-[44px] flex-1"
              disabled={isConfirming}
              onClick={() => onConfirm(confirmation.id)}
              aria-label="수령 확인"
            >
              {isConfirming ? (
                <>
                  <Loader2 className="mr-1 size-4 animate-spin" aria-hidden="true" />
                  확인 중...
                </>
              ) : (
                '수령 확인'
              )}
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="min-h-[44px] flex-1"
              disabled={isDisputing}
              onClick={() => onDispute(confirmation.id)}
              aria-label="미지급 신고"
            >
              {isDisputing ? (
                <>
                  <Loader2 className="mr-1 size-4 animate-spin" aria-hidden="true" />
                  신고 중...
                </>
              ) : (
                '미지급 신고'
              )}
            </Button>
          </div>
        )}

        {/* Studio sees a pending status note */}
        {isPending && !isInstructor && (
          <p className="text-xs text-muted-foreground">
            강사의 수령 확인을 기다리고 있습니다.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ContractsPage() {
  const user = useAuthStore((s) => s.user);
  const isLoading = useAuthStore((s) => s.isLoading);
  const queryClient = useQueryClient();

  // ---- Query: payment confirmations -------------------------------------------
  const confirmationsQuery = useQuery({
    queryKey: ['my-payment-confirmations'],
    queryFn: () => api.paymentConfirmations.getMyConfirmations(),
    enabled: !!user,
  });

  // ---- Confirm mutation -------------------------------------------------------
  const confirmMutation = useMutation({
    mutationFn: (id: string) => api.paymentConfirmations.confirm(id),
    onSuccess: () => {
      toast.success('수령이 확인되었습니다.');
      void queryClient.invalidateQueries({ queryKey: ['my-payment-confirmations'] });
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(error.message);
      } else {
        toast.error('확인 처리 중 오류가 발생했습니다.');
      }
    },
  });

  // ---- Dispute mutation -------------------------------------------------------
  const disputeMutation = useMutation({
    mutationFn: (id: string) =>
      api.paymentConfirmations.dispute(id, '수업료를 받지 못했습니다'),
    onSuccess: () => {
      toast.success('미지급 신고가 접수되었습니다.');
      void queryClient.invalidateQueries({ queryKey: ['my-payment-confirmations'] });
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(error.message);
      } else {
        toast.error('신고 처리 중 오류가 발생했습니다.');
      }
    },
  });

  // ---- Loading state ----------------------------------------------------------
  if (isLoading || !user) {
    return (
      <div className="flex items-center justify-center py-20" role="status">
        <Loader2 className="mr-2 size-6 animate-spin" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">로딩 중...</span>
      </div>
    );
  }

  const isInstructor = user.role === 'instructor';

  // ---- Error state ------------------------------------------------------------
  if (confirmationsQuery.isError) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <h1 className="text-2xl font-bold">지급 확인</h1>
        <div
          className="mt-8 flex flex-col items-center justify-center gap-3 py-20"
          role="alert"
        >
          <p className="text-sm text-destructive">
            지급 확인 내역을 불러오는 데 실패했습니다.
          </p>
          <Button
            variant="outline"
            size="sm"
            className="min-h-[44px]"
            onClick={() => void confirmationsQuery.refetch()}
          >
            다시 시도
          </Button>
        </div>
      </div>
    );
  }

  // ---- Loading query ----------------------------------------------------------
  if (confirmationsQuery.isLoading) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <h1 className="text-2xl font-bold">지급 확인</h1>
        <div className="flex items-center justify-center py-20" role="status">
          <Loader2 className="mr-2 size-6 animate-spin" aria-hidden="true" />
          <span className="text-sm text-muted-foreground">
            내역을 불러오는 중...
          </span>
        </div>
      </div>
    );
  }

  const items = confirmationsQuery.data?.items ?? [];

  // ---- Render -----------------------------------------------------------------
  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="text-2xl font-bold">지급 확인</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {isInstructor
          ? '수업료 지급 내역을 확인하고, 수령 여부를 응답해 주세요.'
          : '수업료 지급 표시 내역을 확인하세요.'}
      </p>

      {items.length === 0 ? (
        <div className="mt-8 flex flex-col items-center justify-center gap-4 py-20">
          <FileText
            className="size-12 text-muted-foreground/40"
            aria-hidden="true"
          />
          <p className="text-sm text-muted-foreground">
            지급 확인 내역이 없습니다
          </p>
          <p className="text-xs text-muted-foreground">
            {isInstructor
              ? '스튜디오에서 수업료를 지급 표시하면 여기에 나타납니다.'
              : '매칭 완료 후 수업료 지급 표시를 하면 여기에 기록됩니다.'}
          </p>
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
          {items.map((confirmation) => (
            <PaymentConfirmationCard
              key={confirmation.id}
              confirmation={confirmation}
              userRole={user.role}
              onConfirm={(id) => confirmMutation.mutate(id)}
              onDispute={(id) => disputeMutation.mutate(id)}
              isConfirming={
                confirmMutation.isPending && confirmMutation.variables === confirmation.id
              }
              isDisputing={
                disputeMutation.isPending && disputeMutation.variables === confirmation.id
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
