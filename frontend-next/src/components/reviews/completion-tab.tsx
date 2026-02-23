'use client';

import { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, Clock, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import api, { APIError } from '@/lib/api-client';
import type { ContractResponse } from '@/lib/api-types';
import { useAuthStore } from '@/stores/auth-store';
import { formatCurrency, formatDate, formatTime } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

// ---------------------------------------------------------------------------
// Completion card sub-component
// ---------------------------------------------------------------------------

function CompletionCard({
  contract,
  userRole,
  onConfirm,
  isConfirming,
}: {
  contract: ContractResponse;
  userRole: string;
  onConfirm: (id: string) => void;
  isConfirming: boolean;
}) {
  const studioConfirmed = !!contract.studio_confirmed_at;
  const instructorConfirmed = !!contract.instructor_confirmed_at;
  const myConfirmDone =
    userRole === 'studio' ? studioConfirmed : instructorConfirmed;

  const partnerName =
    userRole === 'studio'
      ? contract.instructor_name ?? '강사'
      : contract.studio_name ?? '스튜디오';

  return (
    <Card>
      <CardContent className="flex flex-col gap-3">
        {/* Top row: partner + date */}
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="font-medium">{partnerName}</p>
            <p className="text-sm text-muted-foreground">
              {formatDate(contract.date)} {formatTime(contract.start_time)} -{' '}
              {formatTime(contract.end_time)}
            </p>
          </div>
          <Badge variant="secondary" className="shrink-0">
            {formatCurrency(contract.total_amount)}
          </Badge>
        </div>

        {/* Confirmation badges */}
        <div className="flex gap-2">
          <ConfirmBadge
            label="스튜디오"
            confirmed={studioConfirmed}
          />
          <ConfirmBadge
            label="강사"
            confirmed={instructorConfirmed}
          />
        </div>

        {/* Confirm button */}
        {!myConfirmDone && (
          <Button
            className="min-h-[44px] w-full"
            onClick={() => onConfirm(contract.id)}
            disabled={isConfirming}
            aria-label="수업 완료 확인"
          >
            {isConfirming ? (
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            ) : (
              '수업 완료 확인'
            )}
          </Button>
        )}

        {myConfirmDone && (
          <p className="text-sm text-muted-foreground text-center">
            완료 확인 완료 -- 상대방 확인을 기다리는 중
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Confirm badge
// ---------------------------------------------------------------------------

function ConfirmBadge({
  label,
  confirmed,
}: {
  label: string;
  confirmed: boolean;
}) {
  return (
    <Badge
      variant={confirmed ? 'default' : 'outline'}
      className="gap-1"
    >
      {confirmed ? (
        <CheckCircle2 className="size-3" aria-hidden="true" />
      ) : (
        <Clock className="size-3" aria-hidden="true" />
      )}
      {label}: {confirmed ? '완료' : '대기'}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function CompletionTab() {
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const userRole = user?.role ?? 'instructor';

  // ---- Query ---------------------------------------------------------------
  const contractsQuery = useQuery({
    queryKey: ['my-contracts'],
    queryFn: () => api.contracts.getMyContracts(),
  });

  // ---- Mutation ------------------------------------------------------------
  const confirmMutation = useMutation({
    mutationFn: (contractId: string) =>
      api.contracts.confirmCompletion(contractId),
    onSuccess: () => {
      toast.success('수업 완료를 확인했습니다.');
      void queryClient.invalidateQueries({ queryKey: ['my-contracts'] });
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(`완료 확인 실패: ${error.message}`);
      } else {
        toast.error('완료 확인 중 오류가 발생했습니다.');
      }
    },
  });

  // ---- Derived data --------------------------------------------------------
  const { pendingCompletion, completed, metrics } = useMemo(() => {
    const all = contractsQuery.data?.items ?? [];
    const pending = all.filter((c) => c.status === 'pending_completion');
    const done = all.filter((c) => c.status === 'completed');

    const totalAmount = done.reduce((sum, c) => sum + c.total_amount, 0);
    const avgAmount = done.length > 0 ? totalAmount / done.length : 0;

    return {
      pendingCompletion: pending,
      completed: done,
      metrics: {
        totalCompleted: done.length,
        totalAmount,
        avgAmount: Math.round(avgAmount),
      },
    };
  }, [contractsQuery.data]);

  // ---- Render: loading state -----------------------------------------------
  if (contractsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-20" role="status">
        <Loader2 className="mr-2 size-6 animate-spin" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">
          계약을 불러오는 중...
        </span>
      </div>
    );
  }

  // ---- Render: error state -------------------------------------------------
  if (contractsQuery.isError) {
    return (
      <div
        className="flex flex-col items-center justify-center gap-3 py-20"
        role="alert"
      >
        <p className="text-sm text-destructive">
          계약을 불러오는 데 실패했습니다.
        </p>
        <Button
          variant="outline"
          size="sm"
          className="min-h-[44px]"
          onClick={() => void contractsQuery.refetch()}
        >
          다시 시도
        </Button>
      </div>
    );
  }

  // ---- Render: empty state -------------------------------------------------
  if (pendingCompletion.length === 0 && completed.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-20">
        <p className="text-sm text-muted-foreground">
          아직 완료 대기 중이거나 완료된 수업이 없습니다.
        </p>
        <p className="text-xs text-muted-foreground">
          수업이 진행되면 이곳에서 완료를 확인할 수 있습니다.
        </p>
      </div>
    );
  }

  // ---- Render --------------------------------------------------------------
  return (
    <div className="flex flex-col gap-6">
      {/* Pending completion section */}
      {pendingCompletion.length > 0 && (
        <section>
          <h3 className="mb-3 text-base font-semibold">
            완료 대기 ({pendingCompletion.length}건)
          </h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {pendingCompletion.map((contract) => (
              <CompletionCard
                key={contract.id}
                contract={contract}
                userRole={userRole}
                onConfirm={(id) => confirmMutation.mutate(id)}
                isConfirming={confirmMutation.isPending}
              />
            ))}
          </div>
        </section>
      )}

      {/* Completed metrics */}
      {completed.length > 0 && (
        <section>
          <h3 className="mb-3 text-base font-semibold">완료 현황</h3>
          <div className="grid grid-cols-3 gap-3">
            <MetricCard
              label="총 완료"
              value={`${metrics.totalCompleted}건`}
            />
            <MetricCard
              label={userRole === 'studio' ? '총 지출' : '총 수익'}
              value={formatCurrency(metrics.totalAmount)}
            />
            <MetricCard
              label="평균 금액"
              value={formatCurrency(metrics.avgAmount)}
            />
          </div>
        </section>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Metric card
// ---------------------------------------------------------------------------

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-1 py-4 text-center">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-lg font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}
