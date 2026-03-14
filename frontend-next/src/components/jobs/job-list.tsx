'use client';

import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import Link from 'next/link';
import { Loader2, Search } from 'lucide-react';
import api, { APIError } from '@/lib/api-client';
import type { JobPostWithMatchingItem, ApplicationResponse } from '@/lib/api-types';
// PMF pivot: FREE_DAILY_APPLICATION_LIMIT no longer used
// import { FREE_DAILY_APPLICATION_LIMIT } from '@/lib/constants';
import { Button } from '@/components/ui/button';
// PMF pivot: Badge no longer used for subscription status
// import { Badge } from '@/components/ui/badge';
import { JobFiltersBar, type JobFilters } from './job-filters';
import { JobCard } from './job-card';
import { JobDetailDialog } from './job-detail-dialog';
import { ProfileNudgeBanner } from './profile-nudge-banner';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PAGE_SIZE = 20;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function JobList() {
  const queryClient = useQueryClient();

  // ---- Filter state -------------------------------------------------------
  const [filters, setFilters] = useState<JobFilters>({
    category: 'all',
    regions: [],
    urgentOnly: false,
  });

  const [page, setPage] = useState(1);

  // ---- Detail dialog state ------------------------------------------------
  const [detailItem, setDetailItem] = useState<JobPostWithMatchingItem | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [showProfileNudge, setShowProfileNudge] = useState(false);

  // ---- Build query params -------------------------------------------------
  const queryParams = useMemo(() => {
    const params: Record<string, string> = {
      page: String(page),
      page_size: String(PAGE_SIZE),
    };
    if (filters.category !== 'all') params.category = filters.category;
    if (filters.regions.length > 0) params.region = filters.regions.join(',');
    return params;
  }, [filters.category, filters.regions, page]);

  // ---- Queries ------------------------------------------------------------
  const jobsQuery = useQuery({
    queryKey: ['jobs-with-matching', queryParams],
    queryFn: () => api.jobPosts.listWithMatching(queryParams),
  });

  const applicationsQuery = useQuery({
    queryKey: ['my-applications'],
    queryFn: () => api.applications.getMyApplications(),
  });

  const subscriptionQuery = useQuery({
    queryKey: ['subscription-status'],
    queryFn: () => api.subscriptions.getStatus(),
  });

  const profileQuery = useQuery({
    queryKey: ['profile', 'completeness'],
    queryFn: () => api.profileCompleteness.get(),
  });

  // ---- Derived data -------------------------------------------------------
  const appliedJobIds = useMemo(() => {
    if (!applicationsQuery.data) return new Set<string>();
    const apps = applicationsQuery.data.items ?? [];
    return new Set(apps.map((app) => app.job_post_id));
  }, [applicationsQuery.data]);

  // ---- Filter + Sort jobs -------------------------------------------------
  const sortedJobs = useMemo(() => {
    let items = jobsQuery.data?.items ?? [];

    // Apply urgent-only filter
    if (filters.urgentOnly) {
      items = items.filter((item) => item.is_urgent);
    }

    // Apply region filter (client-side, complement to server-side)
    if (filters.regions.length > 0) {
      items = items.filter((item) =>
        item.job.region != null && filters.regions.includes(item.job.region),
      );
    }

    return [...items].sort((a, b) => {
      // Past jobs always at bottom
      if (a.job.is_past !== b.job.is_past) {
        return a.job.is_past ? 1 : -1;
      }

      // Higher matching score first
      const scoreDiff = b.matching.total - a.matching.total;
      if (scoreDiff !== 0) return scoreDiff;

      // Newer first (fallback)
      return (b.job.created_at ?? '').localeCompare(a.job.created_at ?? '');
    });
  }, [jobsQuery.data?.items, filters.urgentOnly, filters.regions]);

  const total = jobsQuery.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const isPremium = subscriptionQuery.data?.has_subscription === true;

  const appliedCount = sortedJobs.filter((item) =>
    appliedJobIds.has(item.job.id),
  ).length;

  // ---- Apply mutation (from card) -----------------------------------------
  const applyMutation = useMutation({
    mutationFn: (jobId: string) => api.applications.apply(jobId),
    onSuccess: () => {
      toast.success('지원 완료! 보통 30분 내에 연락이 옵니다.', {
        duration: 5000,
      });
      void queryClient.invalidateQueries({ queryKey: ['my-applications'] });
      void queryClient.invalidateQueries({ queryKey: ['jobs-with-matching'] });
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        if (error.code === 'ALREADY_APPLIED') {
          toast.warning('이미 지원한 공고입니다.');
        } else if (error.code === 'INCOMPLETE_PROFILE') {
          setShowProfileNudge(true);
        } else if (error.code === 'APPLICATION_LIMIT') {
          toast.error(error.message);
        } else {
          toast.error(`오류: ${error.message}`);
        }
      } else {
        toast.error('지원 중 오류가 발생했습니다.');
      }
    },
  });

  // ---- Handlers -----------------------------------------------------------
  function handleApply(jobId: string) {
    applyMutation.mutate(jobId);
  }

  function handleDetail(item: JobPostWithMatchingItem) {
    setDetailItem(item);
    setDialogOpen(true);
  }

  function handleFiltersChange(newFilters: JobFilters) {
    setFilters(newFilters);
    setPage(1); // Reset to first page on filter change
  }

  // ---- Render: loading state ----------------------------------------------
  if (jobsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-20" role="status">
        <Loader2 className="mr-2 size-6 animate-spin" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">공고를 불러오는 중...</span>
      </div>
    );
  }

  // ---- Render: error state ------------------------------------------------
  if (jobsQuery.isError) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20" role="alert">
        <p className="text-sm text-destructive">
          공고를 불러오는 데 실패했습니다.
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void jobsQuery.refetch()}
        >
          다시 시도
        </Button>
      </div>
    );
  }

  // ---- Render -------------------------------------------------------------
  return (
    <div className="flex flex-col gap-6">
      {/* PMF pivot: subscription/premium status bar removed */}

      {/* Subtle profile hint */}
      {!showProfileNudge && profileQuery.data && profileQuery.data.percentage < 70 && (
        <p className="text-xs text-muted-foreground">
          프로필 {profileQuery.data.percentage}% 완성 &mdash;{' '}
          <Link href="/steps/profile" className="text-primary underline underline-offset-2">
            완성하면 지원 가능
          </Link>
        </p>
      )}

      {/* Filters */}
      <JobFiltersBar filters={filters} onChange={handleFiltersChange} />

      {/* Profile nudge (shown when apply fails due to incomplete profile) */}
      <ProfileNudgeBanner
        show={showProfileNudge}
        onDismiss={() => setShowProfileNudge(false)}
      />

      {/* Summary + encouragement */}
      {sortedJobs.length > 0 && (
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">
            총 {total}개 공고 | 지원 완료 {appliedCount}건
          </p>
          {appliedCount > 0 && appliedCount < 3 && (
            <p className="text-xs text-muted-foreground">
              여러 곳에 지원하면 매칭 확률이 높아집니다
            </p>
          )}
        </div>
      )}

      {/* Empty state */}
      {sortedJobs.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 py-16">
          <div className="flex size-14 items-center justify-center rounded-full bg-muted">
            <Search className="size-6 text-muted-foreground" aria-hidden="true" />
          </div>
          <p className="text-sm font-medium">아직 등록된 공고가 없습니다</p>
          <p className="text-center text-xs text-muted-foreground max-w-[240px]">
            프로필을 완성해두면 새 공고 등록 시 알림을 받을 수 있습니다
          </p>
          <Button variant="outline" size="sm" className="mt-1 min-h-[44px]" asChild>
            <Link href="/steps/profile">프로필 확인하기</Link>
          </Button>
        </div>
      ) : (
        <>
          {/* Job cards grid */}
          <div className="stagger-list grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {sortedJobs.map((item) => (
              <JobCard
                key={item.job.id}
                item={item}
                isApplied={appliedJobIds.has(item.job.id)}
                isPremium={isPremium}
                onApply={handleApply}
                onDetail={handleDetail}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 pt-2">
              <Button
                variant="outline"
                size="sm"
                className="min-h-[44px]"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                aria-label="이전 페이지"
              >
                이전
              </Button>
              <span className="text-sm text-muted-foreground">
                페이지 {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                className="min-h-[44px]"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                aria-label="다음 페이지"
              >
                다음
              </Button>
            </div>
          )}
        </>
      )}

      {/* Detail dialog */}
      <JobDetailDialog
        item={detailItem}
        isApplied={detailItem ? appliedJobIds.has(detailItem.job.id) : false}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onApplied={() => {
          void queryClient.invalidateQueries({ queryKey: ['my-applications'] });
        }}
      />
    </div>
  );
}
