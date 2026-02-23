'use client';

import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { CheckCircle2, Loader2 } from 'lucide-react';
import api, { APIError } from '@/lib/api-client';
import type { ContractResponse } from '@/lib/api-types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface CompletionConfirmSectionProps {
  contract: ContractResponse;
  userRole: string;
  onAction: () => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getConfirmationState(contract: ContractResponse, userRole: string) {
  const isInstructor = userRole === 'instructor';
  const myConfirmed = isInstructor
    ? !!contract.instructor_confirmed_at
    : !!contract.studio_confirmed_at;
  const partnerConfirmed = isInstructor
    ? !!contract.studio_confirmed_at
    : !!contract.instructor_confirmed_at;

  return { myConfirmed, partnerConfirmed };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CompletionConfirmSection({
  contract,
  userRole,
  onAction,
}: CompletionConfirmSectionProps) {
  const { myConfirmed, partnerConfirmed } = getConfirmationState(
    contract,
    userRole,
  );

  const isInstructor = userRole === 'instructor';
  const myLabel = isInstructor ? '강사 (나)' : '스튜디오 (나)';
  const partnerLabel = isInstructor ? '스튜디오' : '강사';

  // ---- Mutation ------------------------------------------------------------
  const confirmMutation = useMutation({
    mutationFn: () => api.contracts.confirmCompletion(contract.id),
    onSuccess: () => {
      toast.success('완료 확인이 처리되었습니다.');
      onAction();
    },
    onError: (error: Error) => {
      if (
        error instanceof APIError &&
        error.message.toLowerCase().includes('already confirmed')
      ) {
        toast.warning('이미 완료 확인이 되었습니다.');
        onAction();
      } else {
        toast.error(
          error instanceof APIError
            ? error.message
            : '완료 확인 중 오류가 발생했습니다.',
        );
      }
    },
  });

  // ---- Render ---------------------------------------------------------------
  return (
    <div className="space-y-4">
      {/* Confirmation status badges - 2 column */}
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col items-center gap-1.5 rounded-lg border p-3">
          <span className="text-xs text-muted-foreground">{myLabel}</span>
          <Badge
            variant={myConfirmed ? 'default' : 'outline'}
            className={
              myConfirmed
                ? 'bg-green-600 text-white hover:bg-green-600'
                : 'border-orange-300 text-orange-600'
            }
          >
            {myConfirmed ? '확인 완료' : '확인 대기'}
          </Badge>
        </div>
        <div className="flex flex-col items-center gap-1.5 rounded-lg border p-3">
          <span className="text-xs text-muted-foreground">{partnerLabel}</span>
          <Badge
            variant={partnerConfirmed ? 'default' : 'outline'}
            className={
              partnerConfirmed
                ? 'bg-green-600 text-white hover:bg-green-600'
                : 'border-orange-300 text-orange-600'
            }
          >
            {partnerConfirmed ? '확인 완료' : '확인 대기'}
          </Badge>
        </div>
      </div>

      {/* Status message */}
      <p className="text-center text-sm text-muted-foreground">
        {myConfirmed && partnerConfirmed
          ? '양측 완료 확인됨'
          : myConfirmed
            ? '상대방의 완료 확인을 기다리는 중'
            : partnerConfirmed
              ? '상대방이 완료를 확인했습니다. 확인을 완료해주세요'
              : '양측 모두 완료 확인이 필요합니다'}
      </p>

      {/* Confirm button */}
      {!myConfirmed && (
        <Button
          className="min-h-[44px] w-full"
          disabled={confirmMutation.isPending}
          onClick={() => confirmMutation.mutate()}
          aria-label="수업 완료 확인"
        >
          {confirmMutation.isPending ? (
            <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
          ) : (
            <CheckCircle2 className="mr-2 size-4" aria-hidden="true" />
          )}
          {partnerConfirmed ? '완료 확인하고 계약 마무리' : '수업 완료 확인'}
        </Button>
      )}
    </div>
  );
}
