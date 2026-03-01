'use client';

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Users, ArrowRight } from 'lucide-react';
import { useAuthStore } from '@/stores/auth-store';
import api from '@/lib/api-client';
import type { JobPostResponse } from '@/lib/api-types';
import { formatCurrency, formatDate, getDDay } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { JobList } from '@/components/jobs/job-list';
import { JobCreationForm } from '@/components/jobs/job-creation-form';

// ---------------------------------------------------------------------------
// Status helpers
// ---------------------------------------------------------------------------

function getJobStatusDisplay(status: string): { label: string; variant: 'default' | 'secondary' | 'outline' } {
  switch (status) {
    case 'open':
      return { label: '모집중', variant: 'default' };
    case 'closed':
      return { label: '마감', variant: 'secondary' };
    case 'filled':
      return { label: '채용완료', variant: 'outline' };
    default:
      return { label: status, variant: 'secondary' };
  }
}

// ---------------------------------------------------------------------------
// Studio's own job card
// ---------------------------------------------------------------------------

function StudioJobCard({ job }: { job: JobPostResponse }) {
  const router = useRouter();
  const statusDisplay = getJobStatusDisplay(job.status);

  return (
    <Card>
      <CardContent className="flex items-center justify-between gap-4 px-4 py-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-semibold">{job.title}</p>
            <Badge variant={statusDisplay.variant}>{statusDisplay.label}</Badge>
          </div>
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
            <span>{formatDate(job.date)}</span>
            <span>{getDDay(job.date)}</span>
            <span>{formatCurrency(job.hourly_rate)}/h</span>
            {job.application_count > 0 ? (
              <Badge variant="default" className="text-xs">
                지원 {job.application_count}명
              </Badge>
            ) : (
              <span>지원 0건</span>
            )}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="min-h-[44px] shrink-0"
          onClick={() => router.push('/steps/offers')}
          aria-label={`${job.title} 지원자 보기`}
        >
          지원자 보기
        </Button>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Studio view
// ---------------------------------------------------------------------------

function StudioView() {
  const {
    data: jobListData,
    isLoading,
  } = useQuery({
    queryKey: ['studio-job-posts'],
    queryFn: () => api.jobPosts.listMine(),
    refetchInterval: 30000, // Poll every 30 seconds for new applicants
  });

  // Jobs with pending applicants
  const jobsWithApplicants = useMemo(() => {
    if (!jobListData?.items) return [];
    return jobListData.items.filter(
      (job: JobPostResponse) => job.status === 'open' && job.application_count > 0
    );
  }, [jobListData?.items]);

  const totalPendingApplicants = useMemo(() => {
    return jobsWithApplicants.reduce((sum, job) => sum + job.application_count, 0);
  }, [jobsWithApplicants]);

  return (
    <div className="space-y-8">
      <JobCreationForm
        onSuccess={() => {
          // Scroll to "my jobs" section after creation
          const section = document.getElementById('my-jobs-section');
          section?.scrollIntoView({ behavior: 'smooth' });
        }}
      />

      {/* My job posts section */}
      <section id="my-jobs-section" className="space-y-4">
        <h3 className="text-lg font-semibold">내 공고 목록</h3>

        {/* New applicants banner */}
        {jobsWithApplicants.length > 0 && (
          <Link
            href="/steps/offers"
            className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 transition-colors hover:bg-blue-100 dark:border-blue-800 dark:bg-blue-950/30 dark:hover:bg-blue-950/50"
          >
            <div className="flex items-center gap-2">
              <Users className="size-5 text-blue-600 dark:text-blue-400" aria-hidden="true" />
              <span className="text-sm font-medium text-blue-900 dark:text-blue-200">
                지원자 {totalPendingApplicants}명이 대기 중
              </span>
            </div>
            <ArrowRight className="size-4 text-blue-600 dark:text-blue-400" aria-hidden="true" />
          </Link>
        )}

        {isLoading && (
          <div className="flex justify-center py-8">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        )}

        {!isLoading && (!jobListData?.items || jobListData.items.length === 0) && (
          <Card>
            <CardContent className="py-8 text-center text-sm text-muted-foreground">
              등록된 공고가 없습니다. 위에서 첫 공고를 등록해보세요.
            </CardContent>
          </Card>
        )}

        {jobListData?.items && jobListData.items.length > 0 && (
          <div className="space-y-2">
            {jobListData.items.map((job: JobPostResponse) => (
              <StudioJobCard key={job.id} job={job} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function JobsPage() {
  const { user, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  const isInstructor = user?.role === 'instructor';

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">
        {isInstructor ? '일 찾기' : '공고 등록'}
      </h2>

      {isInstructor ? <JobList /> : <StudioView />}
    </div>
  );
}
