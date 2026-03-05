'use client';

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Users, ArrowRight, Clock, CheckCircle2, XCircle, Briefcase, Calendar, MapPin } from 'lucide-react';
import { useAuthStore } from '@/stores/auth-store';
import api from '@/lib/api-client';
import type { JobPostResponse } from '@/lib/api-types';
import { cn, formatCurrency, formatDate, getDDay } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { JobList } from '@/components/jobs/job-list';
import { JobCreationForm } from '@/components/jobs/job-creation-form';
import { HandoffNoteForm } from '@/components/jobs/handoff-note-form';

// ---------------------------------------------------------------------------
// Status helpers
// ---------------------------------------------------------------------------

function getJobStatusConfig(status: string): {
  label: string;
  variant: 'default' | 'secondary' | 'outline';
  icon: typeof Clock;
  borderColor: string;
  bgColor: string;
} {
  switch (status) {
    case 'open':
      return {
        label: '모집중',
        variant: 'default',
        icon: Clock,
        borderColor: 'border-l-green-500',
        bgColor: 'bg-green-50 dark:bg-green-950/20',
      };
    case 'filled':
      return {
        label: '채용완료',
        variant: 'outline',
        icon: CheckCircle2,
        borderColor: 'border-l-blue-500',
        bgColor: '',
      };
    case 'closed':
      return {
        label: '마감',
        variant: 'secondary',
        icon: XCircle,
        borderColor: 'border-l-gray-300 dark:border-l-gray-600',
        bgColor: '',
      };
    default:
      return {
        label: status,
        variant: 'secondary',
        icon: Clock,
        borderColor: 'border-l-gray-300',
        bgColor: '',
      };
  }
}

const JOB_TYPE_LABELS: Record<string, string> = {
  substitute: '1회성',
  regular: '여러 회',
  contract: '계약',
};

// ---------------------------------------------------------------------------
// Studio's own job card (redesigned)
// ---------------------------------------------------------------------------

function StudioJobCard({ job }: { job: JobPostResponse }) {
  const router = useRouter();
  const config = getJobStatusConfig(job.status);
  const dDay = getDDay(job.date);
  const hasApplicants = job.application_count > 0;

  return (
    <Card className={cn('overflow-hidden border-l-4 transition-shadow hover:shadow-md', config.borderColor, config.bgColor)}>
      <CardContent className="p-4">
        {/* Row 1: Status + D-Day */}
        <div className="flex items-center justify-between">
          <Badge variant={config.variant} className="text-xs">
            {config.label}
          </Badge>
          <span className={cn(
            'text-xs font-medium',
            dDay === 'D-Day' ? 'text-pink-600 dark:text-pink-400' : 'text-muted-foreground',
          )}>
            {dDay}
          </span>
        </div>

        {/* Row 2: Title */}
        <p className="mt-2 text-sm font-semibold leading-snug">{job.title}</p>

        {/* Row 3: Meta info */}
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <Calendar className="size-3" aria-hidden="true" />
            {formatDate(job.date)}
          </span>
          {job.start_time && job.end_time && (
            <span className="inline-flex items-center gap-1">
              <Clock className="size-3" aria-hidden="true" />
              {job.start_time}~{job.end_time}
            </span>
          )}
          {job.region && (
            <span className="inline-flex items-center gap-1">
              <MapPin className="size-3" aria-hidden="true" />
              {job.region}
            </span>
          )}
          <span className="inline-flex items-center gap-1">
            <Briefcase className="size-3" aria-hidden="true" />
            {formatCurrency(job.hourly_rate)}/h
          </span>
        </div>

        {/* Row 4: Applicant count + action */}
        <div className="mt-3 flex items-center justify-between">
          {hasApplicants ? (
            <Badge variant="default" className="bg-pink-500 text-white hover:bg-pink-600 text-xs">
              <Users className="mr-1 size-3" aria-hidden="true" />
              지원 {job.application_count}명
            </Badge>
          ) : (
            <span className="text-xs text-muted-foreground">지원자 없음</span>
          )}
          <Button
            variant="outline"
            size="sm"
            className="min-h-[36px] text-xs"
            onClick={() => router.push(`/steps/offers?jobId=${job.id}`)}
            aria-label={`${job.title} 지원자 보기`}
          >
            지원자 보기
          </Button>
        </div>

        {/* Handoff note */}
        <div className="mt-3">
          <HandoffNoteForm jobPostId={job.id} isUrgentSubstitute={job.is_urgent} />
        </div>
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

  // Group jobs by status
  const { activeJobs, pastJobs } = useMemo(() => {
    const items = jobListData?.items ?? [];
    const active = items.filter((j: JobPostResponse) => j.status === 'open');
    const past = items.filter((j: JobPostResponse) => j.status !== 'open');
    return { activeJobs: active, pastJobs: past };
  }, [jobListData?.items]);

  const totalJobs = jobListData?.items?.length ?? 0;

  return (
    <div className="space-y-8">
      <JobCreationForm
        onSuccess={() => {
          const section = document.getElementById('my-jobs-section');
          section?.scrollIntoView({ behavior: 'smooth' });
        }}
      />

      {/* My job posts section */}
      <section id="my-jobs-section" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">내 공고 목록</h3>
          {totalJobs > 0 && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>총 {totalJobs}건</span>
              {activeJobs.length > 0 && (
                <>
                  <span className="text-muted-foreground/40">|</span>
                  <span className="text-green-600 dark:text-green-400">모집중 {activeJobs.length}</span>
                </>
              )}
              {pastJobs.length > 0 && (
                <>
                  <span className="text-muted-foreground/40">|</span>
                  <span>완료 {pastJobs.length}</span>
                </>
              )}
            </div>
          )}
        </div>

        {/* New applicants banner */}
        {jobsWithApplicants.length > 0 && (
          <Link
            href="/steps/offers"
            className="flex items-center justify-between rounded-lg border border-pink-200 bg-pink-50 px-4 py-3 transition-colors hover:bg-pink-100 dark:border-pink-800 dark:bg-pink-950/30 dark:hover:bg-pink-950/50"
          >
            <div className="flex items-center gap-2">
              <Users className="size-5 text-pink-600 dark:text-pink-400" aria-hidden="true" />
              <span className="text-sm font-medium text-pink-900 dark:text-pink-200">
                지원자 {totalPendingApplicants}명이 대기 중
              </span>
            </div>
            <ArrowRight className="size-4 text-pink-600 dark:text-pink-400" aria-hidden="true" />
          </Link>
        )}

        {isLoading && (
          <div className="flex justify-center py-8">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        )}

        {!isLoading && totalJobs === 0 && (
          <Card>
            <CardContent className="py-8 text-center text-sm text-muted-foreground">
              등록된 공고가 없습니다. 위에서 첫 공고를 등록해보세요.
            </CardContent>
          </Card>
        )}

        {/* Active jobs */}
        {activeJobs.length > 0 && (
          <div className="space-y-2">
            {activeJobs.map((job: JobPostResponse) => (
              <StudioJobCard key={job.id} job={job} />
            ))}
          </div>
        )}

        {/* Past jobs (collapsed visual) */}
        {pastJobs.length > 0 && (
          <div className="space-y-2">
            {activeJobs.length > 0 && (
              <p className="pt-2 text-xs font-medium text-muted-foreground">지난 공고</p>
            )}
            <div className="space-y-2 opacity-75">
              {pastJobs.map((job: JobPostResponse) => (
                <StudioJobCard key={job.id} job={job} />
              ))}
            </div>
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
