'use client';

import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  MapPin,
  Clock,
  Phone,
  MessageSquare,
  FileText,
  LockOpen,
  CheckCircle2,
} from 'lucide-react';
import type {
  DispatchRecordResponse,
  DispatchContactRevealResponse,
  HandoffNoteFullResponse,
} from '@/lib/api-types';
import { APIError } from '@/lib/api-client';
import api from '@/lib/api-client';
import { formatCurrency } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const CATEGORY_LABELS: Record<string, string> = {
  pilates: '필라테스',
  yoga: '요가',
};

function formatTimeAgo(isoString: string): string {
  const now = Date.now();
  const dispatched = new Date(isoString).getTime();
  const diffMs = now - dispatched;
  const diffMin = Math.max(0, Math.floor(diffMs / 60_000));

  if (diffMin < 1) return '방금 전 요청';
  if (diffMin < 60) return `${diffMin}분 전 요청`;
  const diffHours = Math.floor(diffMin / 60);
  return `${diffHours}시간 ${diffMin % 60}분 전 요청`;
}

function formatTimeRange(start: string, end: string): string {
  return `${start?.slice(0, 5) ?? '-'} ~ ${end?.slice(0, 5) ?? '-'}`;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface DispatchAcceptDialogProps {
  dispatch: DispatchRecordResponse | null;
  open: boolean;
  onClose: () => void;
  onAccepted: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function DispatchAcceptDialog({
  dispatch,
  open,
  onClose,
  onAccepted,
}: DispatchAcceptDialogProps) {
  const queryClient = useQueryClient();

  // Phase: 'detail' (before accept) or 'contact' (after accept)
  const [phase, setPhase] = useState<'detail' | 'contact'>('detail');
  const [contactData, setContactData] =
    useState<DispatchContactRevealResponse | null>(null);

  // Reset phase when dialog opens/closes or dispatch changes
  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) {
      // Delay reset to avoid flicker during close animation
      setTimeout(() => {
        setPhase('detail');
        setContactData(null);
      }, 200);
      onClose();
    }
  };

  // ---- Data fetching: job details ----
  const jobQuery = useQuery({
    queryKey: ['job-post', dispatch?.job_post_id],
    queryFn: () => api.jobPosts.get(dispatch!.job_post_id),
    enabled: open && !!dispatch?.job_post_id,
    staleTime: 30_000,
  });

  // ---- Data fetching: handoff note (only after accept) ----
  const handoffQuery = useQuery({
    queryKey: ['handoff-note', dispatch?.job_post_id],
    queryFn: () =>
      api.handoffNotes.get(dispatch!.job_post_id) as Promise<HandoffNoteFullResponse>,
    enabled: phase === 'contact' && !!dispatch?.job_post_id,
    staleTime: 60_000,
  });

  // ---- Mutations ----
  const acceptMutation = useMutation({
    mutationFn: (dispatchId: string) => api.dispatch.accept(dispatchId),
    onSuccess: (data) => {
      setContactData(data);
      setPhase('contact');
      void queryClient.invalidateQueries({ queryKey: ['dispatch-pending'] });
      onAccepted();
    },
    onError: (error: Error) => {
      if (error instanceof APIError && error.code === 'ALREADY_MATCHED') {
        toast.error('다른 강사가 먼저 수락했습니다');
        handleOpenChange(false);
      } else if (error instanceof APIError) {
        toast.error(`오류: ${error.message}`);
      } else {
        toast.error('수락 처리 중 오류가 발생했습니다');
      }
    },
  });

  const declineMutation = useMutation({
    mutationFn: (dispatchId: string) => api.dispatch.decline(dispatchId),
    onSuccess: () => {
      toast.info('요청을 거절했습니다');
      void queryClient.invalidateQueries({ queryKey: ['dispatch-pending'] });
      handleOpenChange(false);
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(`오류: ${error.message}`);
      } else {
        toast.error('거절 처리 중 오류가 발생했습니다');
      }
    },
  });

  // ---- Derived values ----
  const job = jobQuery.data ?? null;

  const timeAgoText = useMemo(
    () => (dispatch?.dispatched_at ? formatTimeAgo(dispatch.dispatched_at) : ''),
    [dispatch?.dispatched_at],
  );

  // ---- Guard: null dispatch ----
  if (!dispatch) {
    return (
      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>디스패치 요청</DialogTitle>
            <DialogDescription>요청 정보를 불러올 수 없습니다.</DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
  }

  // ======================================================================
  // Phase 3: Contact + Handoff Reveal
  // ======================================================================
  if (phase === 'contact' && contactData) {
    return (
      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle2 className="size-5 text-emerald-600" />
              수락 완료
            </DialogTitle>
            <DialogDescription>
              수락과 동시에 연락처와 인수인계 정보가 공개되었습니다
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4">
            {/* ---- Contact Info Card ---- */}
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-950/20">
              <h3 className="mb-3 text-sm font-semibold text-emerald-800 dark:text-emerald-200">
                스튜디오 연락처
              </h3>

              {contactData.studio_name && (
                <p className="mb-1 text-sm font-medium">
                  {contactData.studio_name}
                </p>
              )}
              {contactData.studio_address && (
                <p className="mb-3 text-sm text-muted-foreground">
                  {contactData.studio_address}
                </p>
              )}

              {contactData.studio_phone && (
                <div className="flex gap-2">
                  <a
                    href={`tel:${contactData.studio_phone}`}
                    className="flex-1"
                    aria-label="스튜디오에 전화하기"
                  >
                    <Button
                      className="min-h-[44px] w-full bg-emerald-600 text-white hover:bg-emerald-700"
                      asChild
                    >
                      <span>
                        <Phone className="mr-2 size-4" />
                        전화
                      </span>
                    </Button>
                  </a>
                  <a
                    href={`sms:${contactData.studio_phone}`}
                    className="flex-1"
                    aria-label="스튜디오에 문자 보내기"
                  >
                    <Button
                      variant="outline"
                      className="min-h-[44px] w-full"
                      asChild
                    >
                      <span>
                        <MessageSquare className="mr-2 size-4" />
                        문자
                      </span>
                    </Button>
                  </a>
                </div>
              )}

              {contactData.studio_phone && (
                <p className="mt-2 text-center text-xs text-muted-foreground">
                  {contactData.studio_phone}
                </p>
              )}
            </div>

            {/* ---- Handoff Note Card ---- */}
            <div className="rounded-lg border bg-card p-4">
              <div className="mb-3 flex items-center gap-2">
                <LockOpen className="size-4 text-emerald-600" />
                <h3 className="text-sm font-semibold">인수인계 노트</h3>
              </div>
              <p className="mb-3 text-xs text-muted-foreground">
                수락과 동시에 자동으로 공개되었습니다
              </p>

              {handoffQuery.isLoading && (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  인수인계 정보를 불러오는 중...
                </p>
              )}

              {handoffQuery.isError && (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  인수인계 정보를 불러올 수 없습니다
                </p>
              )}

              {handoffQuery.data && (
                <div className="flex flex-col gap-3">
                  <HandoffField
                    icon={<FileText className="size-4" />}
                    label="수업 주제"
                    value={handoffQuery.data.class_topic}
                  />
                  <HandoffField
                    icon={<FileText className="size-4" />}
                    label="수업 순서/진도"
                    value={handoffQuery.data.class_sequence_info}
                  />
                  <HandoffField
                    icon={<FileText className="size-4" />}
                    label="분위기 선호"
                    value={handoffQuery.data.atmosphere_preference}
                  />
                  <HandoffField
                    icon={<FileText className="size-4" />}
                    label="추가 안내"
                    value={handoffQuery.data.additional_notes}
                  />
                  {/* Sensitive fields */}
                  <HandoffField
                    icon={<LockOpen className="size-4 text-amber-600" />}
                    label="회원 참고사항"
                    value={handoffQuery.data.member_notes}
                    sensitive
                  />
                  <HandoffField
                    icon={<LockOpen className="size-4 text-amber-600" />}
                    label="기구/장비 안내"
                    value={handoffQuery.data.equipment_notes}
                    sensitive
                  />
                </div>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              className="min-h-[48px] w-full"
              onClick={() => handleOpenChange(false)}
              aria-label="확인하고 닫기"
            >
              확인
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  // ======================================================================
  // Phase 1 + 2: Dispatch Detail + Accept/Decline
  // ======================================================================
  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>디스패치 요청</DialogTitle>
          <DialogDescription className="sr-only">
            디스패치 요청 상세 정보를 확인하고 수락 또는 거절할 수 있습니다
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          {/* ---- Loading state ---- */}
          {jobQuery.isLoading && (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-muted-foreground">공고 정보를 불러오는 중...</p>
            </div>
          )}

          {/* ---- Job info ---- */}
          {job && (
            <>
              {/* Title + Category Badge */}
              <div className="flex items-start gap-2">
                <h3 className="flex-1 text-base font-bold leading-snug">
                  {job.title}
                </h3>
                <Badge variant="secondary" className="shrink-0">
                  {CATEGORY_LABELS[job.category] ?? job.category}
                </Badge>
              </div>

              {/* Date + Time */}
              <div className="flex flex-col gap-1.5">
                <p className="text-sm text-foreground">
                  {job.date} | {formatTimeRange(job.start_time, job.end_time)}
                </p>
                <p className="text-lg font-bold">
                  시급 {formatCurrency(job.hourly_rate)}
                </p>
              </div>

              {/* Distance + Time ago + Wave */}
              <div className="flex flex-wrap items-center gap-2">
                {dispatch.distance_km != null && (
                  <Badge variant="outline" className="gap-1">
                    <MapPin className="size-3" />
                    {dispatch.distance_km.toFixed(1)}km
                  </Badge>
                )}

                {timeAgoText && (
                  <Badge variant="outline" className="gap-1">
                    <Clock className="size-3" />
                    {timeAgoText}
                  </Badge>
                )}

                <Badge
                  variant="secondary"
                  className="bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
                >
                  Wave {dispatch.wave_number}
                </Badge>
              </div>

              {/* Studio info */}
              {job.studio_name && (
                <p className="text-sm text-muted-foreground">
                  {job.studio_name}
                  {job.region ? ` - ${job.region}` : ''}
                </p>
              )}

              {/* Description (if present) */}
              {job.description && (
                <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">
                  {job.description}
                </p>
              )}
            </>
          )}

          {/* ---- Error loading job ---- */}
          {jobQuery.isError && (
            <p className="py-4 text-center text-sm text-destructive">
              공고 정보를 불러올 수 없습니다
            </p>
          )}
        </div>

        {/* ---- Accept / Decline buttons ---- */}
        <DialogFooter className="flex flex-col gap-2 sm:flex-col">
          <Button
            className="min-h-[56px] w-full bg-emerald-600 text-lg font-semibold text-white hover:bg-emerald-700"
            disabled={acceptMutation.isPending || declineMutation.isPending}
            onClick={() => acceptMutation.mutate(dispatch.id)}
            aria-label="디스패치 요청 수락"
          >
            {acceptMutation.isPending ? '수락 중...' : '수락'}
          </Button>
          <Button
            variant="ghost"
            className="min-h-[44px] w-full text-muted-foreground"
            disabled={acceptMutation.isPending || declineMutation.isPending}
            onClick={() => declineMutation.mutate(dispatch.id)}
            aria-label="디스패치 요청 거절"
          >
            {declineMutation.isPending ? '거절 중...' : '거절'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Internal sub-component: HandoffField
// ---------------------------------------------------------------------------

function HandoffField({
  icon,
  label,
  value,
  sensitive = false,
}: {
  icon: React.ReactNode;
  label: string;
  value?: string | null;
  sensitive?: boolean;
}) {
  if (!value) return null;

  return (
    <div
      className={
        sensitive
          ? 'rounded-md border border-amber-200 bg-amber-50/50 p-3 dark:border-amber-800 dark:bg-amber-950/20'
          : 'rounded-md bg-muted/50 p-3'
      }
    >
      <div className="mb-1 flex items-center gap-1.5">
        {icon}
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
      </div>
      <p className="text-sm leading-relaxed whitespace-pre-wrap">{value}</p>
    </div>
  );
}
