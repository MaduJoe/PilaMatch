'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Loader2, PenLine } from 'lucide-react';
import api, { APIError } from '@/lib/api-client';
import type { ContractResponse } from '@/lib/api-types';
import { CONTRACT_TERMS } from '@/lib/constants';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface SigningSectionProps {
  contract: ContractResponse;
  userRole: string;
  onAction: () => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getSignatureState(contract: ContractResponse, userRole: string) {
  const isInstructor = userRole === 'instructor';
  const mySigned = isInstructor
    ? !!contract.instructor_signed_at
    : !!contract.studio_signed_at;
  const partnerSigned = isInstructor
    ? !!contract.studio_signed_at
    : !!contract.instructor_signed_at;

  return { mySigned, partnerSigned };
}

function getStatusMessage(mySigned: boolean, partnerSigned: boolean): string {
  if (mySigned && partnerSigned) return '양측 서명 완료';
  if (mySigned && !partnerSigned) return '상대방 서명을 기다리는 중';
  if (!mySigned && partnerSigned)
    return '상대방이 서명했습니다. 서명을 완료해주세요';
  return '양측 모두 서명이 필요합니다';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SigningSection({
  contract,
  userRole,
  onAction,
}: SigningSectionProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [agreed, setAgreed] = useState(false);

  const { mySigned, partnerSigned } = getSignatureState(contract, userRole);
  const statusMessage = getStatusMessage(mySigned, partnerSigned);

  const isInstructor = userRole === 'instructor';
  const myLabel = isInstructor ? '강사 (나)' : '스튜디오 (나)';
  const partnerLabel = isInstructor ? '스튜디오' : '강사';

  // ---- Mutation ------------------------------------------------------------
  const signMutation = useMutation({
    mutationFn: () => api.contracts.setInProgress(contract.id),
    onSuccess: () => {
      toast.success('서명이 완료되었습니다.');
      setDialogOpen(false);
      setAgreed(false);
      onAction();
    },
    onError: (error: Error) => {
      if (
        error instanceof APIError &&
        error.message.toLowerCase().includes('already signed')
      ) {
        toast.warning('이미 서명이 완료되었습니다.');
        setDialogOpen(false);
        onAction();
      } else {
        toast.error(
          error instanceof APIError
            ? error.message
            : '서명 처리 중 오류가 발생했습니다.',
        );
      }
    },
  });

  // ---- Render ---------------------------------------------------------------
  return (
    <div className="space-y-4">
      {/* Signature status badges - 2 column */}
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col items-center gap-1.5 rounded-lg border p-3">
          <span className="text-xs text-muted-foreground">{myLabel}</span>
          <Badge
            variant={mySigned ? 'default' : 'outline'}
            className={
              mySigned
                ? 'bg-green-600 text-white hover:bg-green-600'
                : 'border-orange-300 text-orange-600'
            }
          >
            {mySigned ? '완료' : '대기'}
          </Badge>
        </div>
        <div className="flex flex-col items-center gap-1.5 rounded-lg border p-3">
          <span className="text-xs text-muted-foreground">{partnerLabel}</span>
          <Badge
            variant={partnerSigned ? 'default' : 'outline'}
            className={
              partnerSigned
                ? 'bg-green-600 text-white hover:bg-green-600'
                : 'border-orange-300 text-orange-600'
            }
          >
            {partnerSigned ? '완료' : '대기'}
          </Badge>
        </div>
      </div>

      {/* Status message */}
      <p className="text-center text-sm text-muted-foreground">
        {statusMessage}
      </p>

      {/* Sign button (only if I haven't signed yet) */}
      {!mySigned && (
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button
              className="min-h-[44px] w-full"
              aria-label="서명하기"
            >
              <PenLine className="mr-2 size-4" aria-hidden="true" />
              서명하기
            </Button>
          </DialogTrigger>

          <DialogContent>
            <DialogHeader>
              <DialogTitle>계약 서명</DialogTitle>
              <DialogDescription>
                아래 약속 사항을 확인한 후 서명해주세요.
              </DialogDescription>
            </DialogHeader>

            {/* Contract terms */}
            <div
              className="max-h-60 overflow-y-auto rounded-md border bg-muted/30 p-4 text-sm leading-relaxed whitespace-pre-line"
              role="document"
              aria-label="계약 조건"
            >
              {CONTRACT_TERMS.trim()}
            </div>

            {/* Agreement checkbox */}
            <label className="flex min-h-[44px] cursor-pointer items-center gap-3">
              <Checkbox
                checked={agreed}
                onCheckedChange={(checked) =>
                  setAgreed(checked === true)
                }
                aria-label="약속 사항 동의"
              />
              <span className="text-sm">위 약속 사항에 동의합니다</span>
            </label>

            <DialogFooter>
              <Button
                variant="outline"
                className="min-h-[44px]"
                onClick={() => setDialogOpen(false)}
              >
                취소
              </Button>
              <Button
                className="min-h-[44px]"
                disabled={!agreed || signMutation.isPending}
                onClick={() => signMutation.mutate()}
                aria-label={
                  partnerSigned ? '서명하고 계약 시작하기' : '서명하기'
                }
              >
                {signMutation.isPending ? (
                  <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
                ) : null}
                {partnerSigned ? '서명하고 계약 시작하기' : '서명하기'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
