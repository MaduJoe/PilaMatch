'use client';

import { useState, useMemo } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import Link from 'next/link';
import { Loader2, FileSearch, Phone, MapPin, MessageSquare, Pencil } from 'lucide-react';
import { toast } from 'sonner';
import api, { APIError } from '@/lib/api-client';
import type { ApplicationWithJobResponse } from '@/lib/api-types';
import { getApplicationStatusDisplay, formatDateTime } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { StarRating } from '@/components/reviews/star-rating';
import { WriteReviewDialog } from '@/components/reviews/write-review-dialog';

// ---------------------------------------------------------------------------
// Status badge color mapping
// ---------------------------------------------------------------------------

function statusBadgeVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'accepted':
      return 'default';
    case 'pending':
      return 'secondary';
    case 'rejected':
      return 'destructive';
    case 'withdrawn':
      return 'outline';
    default:
      return 'outline';
  }
}

// ---------------------------------------------------------------------------
// Application Card
// ---------------------------------------------------------------------------

function ApplicationCard({
  application,
  onWithdraw,
}: {
  application: ApplicationWithJobResponse;
  onWithdraw?: (id: string) => void;
}) {
  const statusDisplay = getApplicationStatusDisplay(application.status);
  const isAccepted = application.status === 'accepted';
  const isPending = application.status === 'pending';
  const [writeDialogOpen, setWriteDialogOpen] = useState(false);

  const eligibilityQuery = useQuery({
    queryKey: ['review-eligibility', application.id],
    queryFn: () => api.reviews.getEligibility(application.id),
    enabled: isAccepted && application.contact_revealed,
    refetchInterval: (query) => {
      const d = query.state.data;
      if (d && d.review_eligible && !d.review_expired && !d.both_reviewed) return 30000;
      return false;
    },
  });
  const eligibility = eligibilityQuery.data;

  return (
    <>
      <Card className={isAccepted ? 'border-green-300 dark:border-green-700' : undefined}>
        <CardContent className="flex flex-col gap-3 p-5">
          {/* Header: job title + status */}
          <div className="flex items-start justify-between gap-2">
            <div className="flex flex-col gap-1">
              <p className="text-base font-semibold leading-tight">
                {application.job_title ?? '(제목 없음)'}
              </p>
              {application.studio_name && (
                <p className="text-sm text-muted-foreground">
                  {application.studio_name}
                </p>
              )}
            </div>
            <Badge
              variant={statusBadgeVariant(application.status)}
              aria-label={`상태: ${statusDisplay.label}`}
            >
              {statusDisplay.label}
            </Badge>
          </div>

          {/* Applied date */}
          <p className="text-xs text-muted-foreground">
            지원일: {formatDateTime(application.created_at)}
          </p>

          {/* Contact revealed section (for accepted applications) */}
          {isAccepted && application.contact_revealed && (
            <>
              <Separator />
              <div className="rounded-lg bg-green-50 p-4 dark:bg-green-950/30">
                <p className="mb-3 text-sm font-medium text-green-800 dark:text-green-200">
                  매칭 완료!
                </p>
                {application.studio_name && (
                  <p className="text-sm font-semibold mb-1">{application.studio_name}</p>
                )}
                {application.studio_phone && (
                  <div className="flex items-center gap-2 mb-2">
                    <Phone className="size-4 text-green-600 dark:text-green-400" />
                    <span className="font-mono text-lg font-bold">{application.studio_phone}</span>
                  </div>
                )}
                {application.studio_address && (
                  <div className="flex items-center gap-1.5 text-sm text-muted-foreground mb-3">
                    <MapPin className="size-3.5 shrink-0" />
                    <span>{application.studio_address}</span>
                  </div>
                )}
                <div className="flex gap-2">
                  {application.studio_phone && (
                    <>
                      <Button asChild size="sm" className="min-h-[44px] flex-1 bg-green-600 hover:bg-green-700 text-white">
                        <a href={`tel:${application.studio_phone}`}>
                          <Phone className="size-4 mr-1" />
                          전화하기
                        </a>
                      </Button>
                      <Button asChild variant="outline" size="sm" className="min-h-[44px] flex-1 border-green-300 text-green-700">
                        <a href={`sms:${application.studio_phone}`}>
                          <MessageSquare className="size-4 mr-1" />
                          문자
                        </a>
                      </Button>
                    </>
                  )}
                </div>
              </div>

              {/* Review section */}
              {eligibility && (
                <div className="border-t pt-3">
                  {eligibility.has_written && eligibility.my_review ? (
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="default" className="text-xs">리뷰 완료</Badge>
                        {/* <StarRating value={eligibility.my_review.rating} readonly size="sm" /> */}
                      </div>
                      {eligibility.both_reviewed && eligibility.partner_review && (
                        <div className="rounded-md bg-muted p-2">
                          <p className="text-xs font-medium text-muted-foreground mb-1">스튜디오 리뷰</p>
                          <StarRating value={eligibility.partner_review.rating} readonly size="sm" />
                          {eligibility.partner_review.comment && (
                            <p className="text-xs mt-1">{eligibility.partner_review.comment}</p>
                          )}
                        </div>
                      )}
                      {!eligibility.both_reviewed && (
                        <p className="text-xs text-muted-foreground">스튜디오가 리뷰를 작성하면 서로 확인할 수 있습니다.</p>
                      )}
                    </div>
                  ) : eligibility.review_expired ? (
                    <p className="text-xs text-muted-foreground">리뷰 작성 기간이 지났습니다.</p>
                  ) : eligibility.review_eligible ? (
                    <Button
                      variant="outline"
                      className="min-h-[44px] w-full gap-1"
                      onClick={() => setWriteDialogOpen(true)}
                    >
                      <Pencil className="size-4" aria-hidden="true" />
                      리뷰 작성
                    </Button>
                  ) : (
                    <p className="text-xs text-muted-foreground">수업 종료 후 리뷰를 작성할 수 있습니다.</p>
                  )}
                </div>
              )}
            </>
          )}

          {/* Accepted but contact not yet revealed -- unlikely but handle gracefully */}
          {isAccepted && !application.contact_revealed && (
            <>
              <Separator />
              <p className="text-sm text-green-700 dark:text-green-300">
                수락되었습니다. 연락처 확인 중...
              </p>
            </>
          )}

          {/* Withdraw button for pending applications */}
          {isPending && onWithdraw && (
            <div className="flex justify-end pt-1">
              <Button
                variant="outline"
                size="sm"
                className="min-h-[44px]"
                onClick={() => onWithdraw(application.id)}
                aria-label={`${application.job_title ?? '공고'} 지원 철회`}
              >
                지원 철회
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Write review dialog */}
      <WriteReviewDialog
        applicationId={application.id}
        partnerName={application.studio_name ?? '스튜디오'}
        reviewerRole="instructor"
        open={writeDialogOpen}
        onOpenChange={setWriteDialogOpen}
        onSuccess={() => {}}
      />
    </>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function InstructorApplicationList() {
  const queryClient = useQueryClient();
  const [withdrawTargetId, setWithdrawTargetId] = useState<string | null>(null);

  // ---- Query: my applications ------------------------------------------------
  const applicationsQuery = useQuery({
    queryKey: ['my-applications'],
    queryFn: () => api.applications.getMyApplications(),
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  });

  // ---- Withdraw mutation -----------------------------------------------------
  const withdrawMutation = useMutation({
    mutationFn: (applicationId: string) => api.applications.withdraw(applicationId),
    onSuccess: () => {
      toast.success('지원이 철회되었습니다.');
      setWithdrawTargetId(null);
      void queryClient.invalidateQueries({ queryKey: ['my-applications'] });
    },
    onError: (error: Error) => {
      setWithdrawTargetId(null);
      if (error instanceof APIError) {
        toast.error(error.message);
      } else {
        toast.error('지원 철회 중 오류가 발생했습니다.');
      }
    },
  });

  // ---- Separate by status: accepted first, then pending, then others ----------
  // NOTE: useMemo must be called before any early returns (Rules of Hooks)
  const items = applicationsQuery.data?.items ?? [];
  const { accepted, pending, others } = useMemo(() => {
    const acc: ApplicationWithJobResponse[] = [];
    const pend: ApplicationWithJobResponse[] = [];
    const rest: ApplicationWithJobResponse[] = [];
    for (const a of items) {
      if (a.status === 'accepted') acc.push(a);
      else if (a.status === 'pending') pend.push(a);
      else rest.push(a);
    }
    return { accepted: acc, pending: pend, others: rest };
  }, [items]);

  // ---- Render: loading state --------------------------------------------------
  if (applicationsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-20" role="status">
        <Loader2 className="mr-2 size-6 animate-spin" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">
          지원 현황을 불러오는 중...
        </span>
      </div>
    );
  }

  // ---- Render: error state ----------------------------------------------------
  if (applicationsQuery.isError) {
    return (
      <div
        className="flex flex-col items-center justify-center gap-3 py-20"
        role="alert"
      >
        <p className="text-sm text-destructive">
          지원 목록을 불러오는 데 실패했습니다.
        </p>
        <Button
          variant="outline"
          size="sm"
          className="min-h-[44px]"
          onClick={() => void applicationsQuery.refetch()}
        >
          다시 시도
        </Button>
      </div>
    );
  }

  // ---- Render: empty state ----------------------------------------------------
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <FileSearch
          className="size-12 text-muted-foreground/40"
          aria-hidden="true"
        />
        <p className="text-sm text-muted-foreground">
          아직 지원한 공고가 없습니다
        </p>
        <Button asChild className="min-h-[44px]">
          <Link href="/steps/jobs">공고 찾아보기</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Accepted applications */}
      {accepted.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold">
            매칭 완료 ({accepted.length})
          </h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {accepted.map((app) => (
              <ApplicationCard key={app.id} application={app} />
            ))}
          </div>
        </section>
      )}

      {/* Pending applications */}
      {pending.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold">
            대기 중 ({pending.length})
          </h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {pending.map((app) => (
              <ApplicationCard
                key={app.id}
                application={app}
                onWithdraw={setWithdrawTargetId}
              />
            ))}
          </div>
        </section>
      )}

      {/* Rejected / Withdrawn */}
      {others.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold">
            처리 완료 ({others.length})
          </h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {others.map((app) => (
              <ApplicationCard key={app.id} application={app} />
            ))}
          </div>
        </section>
      )}

      {/* Withdraw confirmation dialog */}
      <Dialog
        open={withdrawTargetId !== null}
        onOpenChange={(open) => {
          if (!open) setWithdrawTargetId(null);
        }}
      >
        <DialogContent showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>지원을 철회하시겠습니까?</DialogTitle>
            <DialogDescription>
              철회 시 해당 공고에 재지원할 수 없습니다.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              className="min-h-[44px]"
              onClick={() => setWithdrawTargetId(null)}
            >
              취소
            </Button>
            <Button
              variant="destructive"
              className="min-h-[44px]"
              disabled={withdrawMutation.isPending}
              onClick={() => {
                if (withdrawTargetId) {
                  withdrawMutation.mutate(withdrawTargetId);
                }
              }}
            >
              {withdrawMutation.isPending ? (
                <>
                  <Loader2 className="mr-1 size-4 animate-spin" aria-hidden="true" />
                  철회 중...
                </>
              ) : (
                '철회하기'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
