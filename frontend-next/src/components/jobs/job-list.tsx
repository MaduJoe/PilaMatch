'use client';

import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import api, { APIError } from '@/lib/api-client';
import type { JobPostWithMatchingItem, ApplicationResponse } from '@/lib/api-types';
import { FREE_DAILY_APPLICATION_LIMIT } from '@/lib/constants';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { JobFiltersBar, type JobFilters } from './job-filters';
import { JobCard } from './job-card';
import { JobDetailDialog } from './job-detail-dialog';

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
    region: 'all',
    sortByScore: true,
  });

  const [page, setPage] = useState(1);

  // ---- Detail dialog state ------------------------------------------------
  const [detailItem, setDetailItem] = useState<JobPostWithMatchingItem | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  // ---- Build query params -------------------------------------------------
  const queryParams = useMemo(() => {
    const params: Record<string, string> = {
      page: String(page),
      page_size: String(PAGE_SIZE),
    };
    if (filters.category !== 'all') params.category = filters.category;
    if (filters.region !== 'all') params.region = filters.region;
    return params;
  }, [filters.category, filters.region, page]);

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

  // ---- Derived data -------------------------------------------------------
  const appliedJobIds = useMemo(() => {
    if (!applicationsQuery.data) return new Set<string>();
    const apps = applicationsQuery.data.items ?? [];
    return new Set(apps.map((app) => app.job_post_id));
  }, [applicationsQuery.data]);

  const isPremium = subscriptionQuery.data?.membership_tier === 'premium';

  const activeApplicationCount = useMemo(() => {
    if (!applicationsQuery.data) return 0;
    const apps = applicationsQuery.data.items ?? [];
    return apps.filter((app) => app.status === 'pending').length;
  }, [applicationsQuery.data]);

  // ---- Sort jobs ----------------------------------------------------------
  const sortedJobs = useMemo(() => {
    const items = jobsQuery.data?.items ?? [];
    return [...items].sort((a, b) => {
      // Past jobs always at bottom
      if (a.job.is_past !== b.job.is_past) {
        return a.job.is_past ? 1 : -1;
      }

      if (filters.sortByScore) {
        // Higher matching score first
        const scoreDiff = b.matching.total - a.matching.total;
        if (scoreDiff !== 0) return scoreDiff;
      }

      // Newer first (fallback)
      return b.job.created_at.localeCompare(a.job.created_at);
    });
  }, [jobsQuery.data?.items, filters.sortByScore]);

  const total = jobsQuery.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const appliedCount = sortedJobs.filter((item) =>
    appliedJobIds.has(item.job.id),
  ).length;

  // ---- Apply mutation (from card) -----------------------------------------
  const applyMutation = useMutation({
    mutationFn: (jobId: string) => api.applications.apply(jobId),
    onSuccess: () => {
      toast.success('지원 완료! 스튜디오 응답을 기다려주세요.');
      void queryClient.invalidateQueries({ queryKey: ['my-applications'] });
      void queryClient.invalidateQueries({ queryKey: ['jobs-with-matching'] });
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        if (error.code === 'ALREADY_APPLIED') {
          toast.warning('이미 지원한 공고입니다.');
        } else if (error.code === 'INCOMPLETE_PROFILE') {
          toast.warning(`프로필 미완성: ${error.message}`);
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
      {/* Application limit status bar */}
      <div className="flex flex-wrap items-center gap-2">
        {isPremium ? (
          <Badge variant="default" className="bg-violet-600 text-white">
            Premium - 무제한 지원 가능
          </Badge>
        ) : (
          <Badge
            variant={
              activeApplicationCount >= FREE_DAILY_APPLICATION_LIMIT
                ? 'destructive'
                : 'secondary'
            }
          >
            지원 현황: {activeApplicationCount}/{FREE_DAILY_APPLICATION_LIMIT}
            {activeApplicationCount >= FREE_DAILY_APPLICATION_LIMIT
              ? ' (한도 도달)'
              : ` (${FREE_DAILY_APPLICATION_LIMIT - activeApplicationCount}개 남음)`}
          </Badge>
        )}
      </div>

      {/* Filters */}
      <JobFiltersBar filters={filters} onChange={handleFiltersChange} />

      {/* Summary */}
      {sortedJobs.length > 0 && (
        <p className="text-sm text-muted-foreground">
          총 {total}개 공고 | 지원 완료 {appliedCount}건
        </p>
      )}

      {/* Empty state */}
      {sortedJobs.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-2 py-20">
          <p className="text-sm text-muted-foreground">등록된 공고가 없습니다.</p>
          <p className="text-xs text-muted-foreground">
            스튜디오가 공고를 등록하면 여기에 표시됩니다.
          </p>
        </div>
      ) : (
        <>
          {/* Job cards grid */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {sortedJobs.map((item) => (
              <JobCard
                key={item.job.id}
                item={item}
                isApplied={appliedJobIds.has(item.job.id)}
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
