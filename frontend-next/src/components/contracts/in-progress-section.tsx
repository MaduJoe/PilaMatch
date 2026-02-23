'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  XCircle,
} from 'lucide-react';
import api, { APIError } from '@/lib/api-client';
import type { ContractResponse } from '@/lib/api-types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface InProgressSectionProps {
  contract: ContractResponse;
  userRole: string;
  userId: string;
  onAction: () => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getDDayInfo(dateStr: string): { text: string; variant: 'default' | 'destructive' | 'secondary' } {
  const target = new Date(dateStr);
  const today = new Date();
  target.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  const diff = Math.ceil(
    (target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24),
  );

  if (diff === 0) return { text: '오늘 수업입니다!', variant: 'destructive' };
  if (diff < 0)
    return { text: '수업일이 지났습니다', variant: 'secondary' };
  return { text: `수업까지 ${diff}일 남음`, variant: 'default' };
}

function calcDurationMinutes(startTime: string, endTime: string): number {
  const [sh, sm] = startTime.split(':').map(Number);
  const [eh, em] = endTime.split(':').map(Number);
  return (eh * 60 + em) - (sh * 60 + sm);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function InProgressSection({
  contract,
  userRole,
  userId,
  onAction,
}: InProgressSectionProps) {
  const [cancelOpen, setCancelOpen] = useState(false);
  const [noShowOpen, setNoShowOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');

  const dday = getDDayInfo(contract.date);
  const duration = calcDurationMinutes(contract.start_time, contract.end_time);
  const durationLabel =
    duration >= 60
      ? `${Math.floor(duration / 60)}시간${duration % 60 > 0 ? ` ${duration % 60}분` : ''}`
      : `${duration}분`;

  // The person to report as no-show is the other party
  const reportedUserId =
    userRole === 'instructor' ? contract.studio_id : contract.instructor_id;

  // ---- Mutations ------------------------------------------------------------

  const completeMutation = useMutation({
    mutationFn: () => api.contracts.confirmCompletion(contract.id),
    onSuccess: () => {
      toast.success('수업 완료가 확인되었습니다.');
      onAction();
    },
    onError: (error: Error) => {
      toast.error(
        error instanceof APIError
          ? error.message
          : '완료 처리 중 오류가 발생했습니다.',
      );
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () =>
      api.contracts.cancel(contract.id, { reason: cancelReason }),
    onSuccess: () => {
      toast.success('계약이 취소되었습니다.');
      setCancelOpen(false);
      setCancelReason('');
      onAction();
    },
    onError: (error: Error) => {
      toast.error(
        error instanceof APIError
          ? error.message
          : '취소 처리 중 오류가 발생했습니다.',
      );
    },
  });

  const noShowMutation = useMutation({
    mutationFn: () =>
      api.contracts.reportNoShow(contract.id, reportedUserId),
    onSuccess: () => {
      toast.success('노쇼 신고가 접수되었습니다.');
      setNoShowOpen(false);
      onAction();
    },
    onError: (error: Error) => {
      toast.error(
        error instanceof APIError
          ? error.message
          : '노쇼 신고 중 오류가 발생했습니다.',
      );
    },
  });

  // ---- Render ---------------------------------------------------------------
  return (
    <div className="space-y-4">
      {/* D-day + duration info */}
      <div className="flex items-center justify-between">
        <Badge variant={dday.variant}>{dday.text}</Badge>
        <span className="text-sm text-muted-foreground">
          수업 시간: {durationLabel}
        </span>
      </div>

      {/* Action buttons */}
      <div className="flex flex-col gap-2 sm:flex-row">
        <Button
          className="min-h-[44px] flex-1"
          disabled={completeMutation.isPending}
          onClick={() => completeMutation.mutate()}
          aria-label="수업 완료"
        >
          {completeMutation.isPending ? (
            <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
          ) : (
            <CheckCircle2 className="mr-2 size-4" aria-hidden="true" />
          )}
          수업 완료
        </Button>

        <Button
          variant="outline"
          className="min-h-[44px] flex-1"
          onClick={() => setCancelOpen(true)}
          aria-label="취소"
        >
          <XCircle className="mr-2 size-4" aria-hidden="true" />
          취소
        </Button>

        <Button
          variant="destructive"
          className="min-h-[44px] flex-1"
          onClick={() => setNoShowOpen(true)}
          aria-label="불참 신고"
        >
          <AlertTriangle className="mr-2 size-4" aria-hidden="true" />
          불참 신고
        </Button>
      </div>

      {/* ---------- Cancel Dialog ------------------------------------------- */}
      <Dialog open={cancelOpen} onOpenChange={setCancelOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>계약 취소</DialogTitle>
            <DialogDescription>
              계약을 취소하면 되돌릴 수 없습니다. 24시간 이내 취소 시 패널티가
              적용될 수 있습니다.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            <label
              htmlFor="cancel-reason"
              className="text-sm font-medium"
            >
              취소 사유
            </label>
            <Input
              id="cancel-reason"
              placeholder="취소 사유를 입력해주세요"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              className="min-h-[44px]"
            />
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              className="min-h-[44px]"
              onClick={() => setCancelOpen(false)}
            >
              돌아가기
            </Button>
            <Button
              variant="destructive"
              className="min-h-[44px]"
              disabled={!cancelReason.trim() || cancelMutation.isPending}
              onClick={() => cancelMutation.mutate()}
              aria-label="취소 확정"
            >
              {cancelMutation.isPending ? (
                <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
              ) : null}
              취소 확정
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---------- No-Show Dialog ------------------------------------------ */}
      <Dialog open={noShowOpen} onOpenChange={setNoShowOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>불참 신고</DialogTitle>
            <DialogDescription>
              {userRole === 'instructor'
                ? '스튜디오가 약속된 수업을 진행하지 않았나요? 노쇼 신고 시 상대방에게 30,000원 패널티가 부과되며, 3회 누적 시 계정이 정지됩니다.'
                : '강사가 약속된 수업에 참석하지 않았나요? 노쇼 신고 시 상대방에게 30,000원 패널티가 부과되며, 3회 누적 시 계정이 정지됩니다.'}
            </DialogDescription>
          </DialogHeader>

          <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3">
            <p className="text-sm text-destructive">
              허위 신고 시 본인에게 패널티가 적용될 수 있습니다.
              신중하게 판단해주세요.
            </p>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              className="min-h-[44px]"
              onClick={() => setNoShowOpen(false)}
            >
              돌아가기
            </Button>
            <Button
              variant="destructive"
              className="min-h-[44px]"
              disabled={noShowMutation.isPending}
              onClick={() => noShowMutation.mutate()}
              aria-label="노쇼 신고"
            >
              {noShowMutation.isPending ? (
                <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
              ) : null}
              노쇼 신고
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
