'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import type { JobPostWithMatchingItem } from '@/lib/api-types';
import { APIError } from '@/lib/api-client';
import api from '@/lib/api-client';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const JOB_TYPE_LABELS: Record<string, string> = {
  substitute: '대타',
  regular: '정규',
  contract: '계약',
};

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface JobDetailDialogProps {
  item: JobPostWithMatchingItem | null;
  isApplied: boolean;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onApplied: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function JobDetailDialog({
  item,
  isApplied,
  open,
  onOpenChange,
  onApplied,
}: JobDetailDialogProps) {
  const queryClient = useQueryClient();
  const [applyError, setApplyError] = useState<string | null>(null);

  const applyMutation = useMutation({
    mutationFn: (jobId: string) => api.applications.apply(jobId),
    onSuccess: () => {
      toast.success('지원 완료! 스튜디오 응답을 기다려주세요.');
      void queryClient.invalidateQueries({ queryKey: ['my-applications'] });
      void queryClient.invalidateQueries({ queryKey: ['jobs-with-matching'] });
      onApplied();
      onOpenChange(false);
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        if (error.code === 'ALREADY_APPLIED') {
          toast.warning('이미 지원한 공고입니다.');
          setApplyError(null);
        } else if (error.code === 'INCOMPLETE_PROFILE') {
          toast.warning(`프로필 미완성: ${error.message}`);
          setApplyError('프로필을 먼저 완성해주세요.');
        } else if (error.code === 'APPLICATION_LIMIT') {
          toast.error(error.message);
          setApplyError('프리미엄으로 업그레이드하면 무제한 지원이 가능합니다.');
        } else {
          toast.error(`오류: ${error.message}`);
          setApplyError(error.message);
        }
      } else {
        toast.error('지원 중 오류가 발생했습니다.');
        setApplyError('알 수 없는 오류가 발생했습니다.');
      }
    },
  });

  // Guard: nothing to render when item is null
  if (!item) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>공고 상세 정보</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">공고 정보를 불러올 수 없습니다.</p>
        </DialogContent>
      </Dialog>
    );
  }

  const { job, matching, is_premium, is_urgent } = item;
  const isPast = job.is_past;
  const typeLabel = JOB_TYPE_LABELS[job.job_type] ?? job.job_type;
  const breakdown = matching.breakdown;

  const canApply = !isApplied && !isPast;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {typeLabel} | {job.region ?? '-'}
            {is_premium && (
              <Badge variant="default" className="bg-violet-600 text-xs text-white">
                Premium
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          {/* Hourly rate */}
          <p className="text-lg font-bold">
            {formatCurrency(job.hourly_rate)} / 시간
          </p>

          {/* Date + time range */}
          <p className="text-sm text-muted-foreground">
            {job.date} | {job.start_time?.slice(0, 5) ?? '-'} ~{' '}
            {job.end_time?.slice(0, 5) ?? '-'}
          </p>

          {/* Studio info */}
          {job.studio_name && (
            <p className="text-sm text-muted-foreground">
              스튜디오: {job.studio_name}
              {job.studio_rating != null && job.studio_rating > 0
                ? ` (${job.studio_rating.toFixed(1)})`
                : ''}
            </p>
          )}

          {/* Description (full) */}
          {job.description && (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {job.description}
            </p>
          )}

          {/* Matching breakdown */}
          <div>
            <h4 className="mb-2 text-sm font-semibold">매칭 분석</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="rounded-md bg-muted px-3 py-2">
                <span className="text-muted-foreground">지역</span>
                <span className="ml-2 font-medium">{breakdown.region?.score ?? 0}점</span>
              </div>
              <div className="rounded-md bg-muted px-3 py-2">
                <span className="text-muted-foreground">경력</span>
                <span className="ml-2 font-medium">{breakdown.experience?.score ?? 0}점</span>
              </div>
              <div className="rounded-md bg-muted px-3 py-2">
                <span className="text-muted-foreground">자격</span>
                <span className="ml-2 font-medium">{breakdown.certifications?.score ?? 0}점</span>
              </div>
              <div className="rounded-md bg-muted px-3 py-2">
                <span className="text-muted-foreground">시급</span>
                <span className="ml-2 font-medium">{breakdown.hourly_rate?.score ?? 0}점</span>
              </div>
            </div>
          </div>

          {/* Urgent badge info */}
          {is_urgent && (
            <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800 dark:bg-red-950 dark:text-red-200">
              긴급 매칭 - 24시간 내 수업
            </div>
          )}

          {/* Error message */}
          {applyError && (
            <p className="text-sm text-destructive" role="alert">
              {applyError}
            </p>
          )}

          {/* Apply button */}
          <Button
            className={cn('min-h-[44px] w-full', isPast && 'opacity-60')}
            disabled={!canApply || applyMutation.isPending}
            onClick={() => {
              setApplyError(null);
              applyMutation.mutate(job.id);
            }}
            aria-label={
              isApplied
                ? '지원 완료'
                : isPast
                  ? '지원 불가 - 지난 공고'
                  : '지원하기'
            }
          >
            {applyMutation.isPending
              ? '지원 중...'
              : isApplied
                ? '지원완료'
                : isPast
                  ? '지원 불가 (지난 공고)'
                  : '지원하기'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
