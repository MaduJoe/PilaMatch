'use client';

import { useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2, FileText } from 'lucide-react';
import api from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import { Button } from '@/components/ui/button';
import { ContractCard } from '@/components/contracts/contract-card';
import { CompletedContractsTable } from '@/components/contracts/completed-contracts-table';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ACTIVE_STATUSES = new Set(['confirmed', 'in_progress', 'pending_completion']);
const DONE_STATUSES = new Set(['completed', 'cancelled']);

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ContractsPage() {
  const user = useAuthStore((s) => s.user);
  const isLoading = useAuthStore((s) => s.isLoading);
  const queryClient = useQueryClient();

  // ---- Query ----------------------------------------------------------------
  const contractsQuery = useQuery({
    queryKey: ['my-contracts'],
    queryFn: () => api.contracts.getMyContracts(),
    enabled: !!user,
  });

  // ---- Derived data ---------------------------------------------------------
  const { active, done } = useMemo(() => {
    const all = contractsQuery.data?.items ?? [];
    return {
      active: all.filter((c) => ACTIVE_STATUSES.has(c.status)),
      done: all.filter((c) => DONE_STATUSES.has(c.status)),
    };
  }, [contractsQuery.data]);

  // ---- Handlers -------------------------------------------------------------
  function handleAction() {
    void queryClient.invalidateQueries({ queryKey: ['my-contracts'] });
  }

  // ---- Loading state --------------------------------------------------------
  if (isLoading || !user) {
    return (
      <div className="flex items-center justify-center py-20" role="status">
        <Loader2 className="mr-2 size-6 animate-spin" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">로딩 중...</span>
      </div>
    );
  }

  const isInstructor = user.role === 'instructor';

  // ---- Error state ----------------------------------------------------------
  if (contractsQuery.isError) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <h1 className="text-2xl font-bold">
          {isInstructor ? '4단계: 계약 진행' : '4단계: 계약 진행'}
        </h1>
        <div
          className="mt-8 flex flex-col items-center justify-center gap-3 py-20"
          role="alert"
        >
          <p className="text-sm text-destructive">
            계약 목록을 불러오는 데 실패했습니다.
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
      </div>
    );
  }

  // ---- Loading query --------------------------------------------------------
  if (contractsQuery.isLoading) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <h1 className="text-2xl font-bold">4단계: 계약 진행</h1>
        <div className="flex items-center justify-center py-20" role="status">
          <Loader2 className="mr-2 size-6 animate-spin" aria-hidden="true" />
          <span className="text-sm text-muted-foreground">
            계약을 불러오는 중...
          </span>
        </div>
      </div>
    );
  }

  // ---- Empty state ----------------------------------------------------------
  const isEmpty = active.length === 0 && done.length === 0;

  // ---- Render ---------------------------------------------------------------
  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="text-2xl font-bold">4단계: 계약 진행</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {isInstructor
          ? '계약 서명, 수업 진행, 완료 확인을 관리하세요.'
          : '계약 서명, 결제, 수업 완료를 관리하세요.'}
      </p>

      {isEmpty ? (
        <div className="mt-8 flex flex-col items-center justify-center gap-4 py-20">
          <FileText
            className="size-12 text-muted-foreground/40"
            aria-hidden="true"
          />
          <p className="text-sm text-muted-foreground">
            아직 계약이 없습니다
          </p>
          <p className="text-xs text-muted-foreground">
            오퍼를 수락하면 계약이 생성됩니다.
          </p>
        </div>
      ) : (
        <div className="mt-6 space-y-8">
          {/* Active contracts */}
          {active.length > 0 && (
            <section>
              <h2 className="mb-4 text-lg font-semibold">
                진행 중인 계약 ({active.length})
              </h2>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {active.map((contract) => (
                  <ContractCard
                    key={contract.id}
                    contract={contract}
                    onAction={handleAction}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Completed/cancelled contracts */}
          {done.length > 0 && (
            <section>
              <h2 className="mb-4 text-lg font-semibold">
                완료된 계약 ({done.length})
              </h2>
              <CompletedContractsTable
                contracts={done}
                userRole={user.role}
              />
            </section>
          )}
        </div>
      )}
    </div>
  );
}
