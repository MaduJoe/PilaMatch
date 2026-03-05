'use client';

import { useMemo, useState } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import { Clock, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { toast } from 'sonner';
import api, { APIError } from '@/lib/api-client';
import type { ContactRevealResponse, JobPostResponse } from '@/lib/api-types';
import { formatCurrency, formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ApplicantCard } from './applicant-card';
import { ContactRevealScreen } from './contact-reveal-screen';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const JOB_TYPE_LABELS: Record<string, string> = {
  substitute: '1회성',
  regular: '여러 회',
  contract: '계약',
};

function buildJobLabel(job: JobPostResponse): string {
  const pastLabel = job.is_past ? ' [지난공고]' : '';
  return `${job.title}${pastLabel} | ${job.date} | 지원자 ${job.application_count}명`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ApplicantList() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const jobIdFromQuery = searchParams.get('jobId');

  // ---- State ---------------------------------------------------------------
  const [selectedJobId, setSelectedJobId] = useState<string | undefined>(jobIdFromQuery ?? undefined);
  const [contactReveal, setContactReveal] = useState<ContactRevealResponse | null>(null);
  const [contactRevealJob, setContactRevealJob] = useState<JobPostResponse | null>(null);

  // ---- Query: my job posts (studio only) -----------------------------------
  const jobsQuery = useQuery({
    queryKey: ['studio-job-posts'],
    queryFn: () => api.jobPosts.listMine(),
  });

  const myJobs = useMemo(() => {
    return jobsQuery.data?.items ?? [];
  }, [jobsQuery.data?.items]);

  // Auto-select first job if none selected
  const effectiveJobId = selectedJobId ?? myJobs[0]?.id;

  // ---- Query: applications for selected job --------------------------------
  const applicationsQuery = useQuery({
    queryKey: ['job-applications', effectiveJobId],
    queryFn: () => api.applications.getForJobPost(effectiveJobId!),
    enabled: !!effectiveJobId,
    refetchInterval: 15000, // Poll every 15 seconds for new applicants
  });

  // ---- Selected job info ---------------------------------------------------
  const selectedJob = useMemo(
    () => myJobs.find((j) => j.id === effectiveJobId),
    [myJobs, effectiveJobId],
  );

  // ---- Accept mutation (replaces offer flow) --------------------------------
  const acceptMutation = useMutation({
    mutationFn: (applicationId: string) => api.applications.accept(applicationId),
    onSuccess: (data: ContactRevealResponse) => {
      // Snapshot job data before invalidation can remove it from the query cache
      setContactRevealJob(selectedJob ?? null);
      setContactReveal(data);
      void queryClient.invalidateQueries({ queryKey: ['job-applications', effectiveJobId] });
      void queryClient.invalidateQueries({ queryKey: ['studio-job-posts'] });
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(error.message);
      } else {
        toast.error('수락 중 오류가 발생했습니다.');
      }
    },
  });

  // ---- Render: loading state -----------------------------------------------
  if (jobsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-20" role="status">
        <Loader2 className="mr-2 size-6 animate-spin" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">공고를 불러오는 중...</span>
      </div>
    );
  }

  // ---- Render: error state -------------------------------------------------
  if (jobsQuery.isError) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20" role="alert">
        <p className="text-sm text-destructive">
          공고를 불러오는 데 실패했습니다.
        </p>
        <Button
          variant="outline"
          size="sm"
          className="min-h-[44px]"
          onClick={() => void jobsQuery.refetch()}
        >
          다시 시도
        </Button>
      </div>
    );
  }

  // ---- Render: no jobs (empty state) ---------------------------------------
  if (myJobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <p className="text-sm text-muted-foreground">등록된 공고가 없습니다.</p>
        <Button asChild className="min-h-[44px]">
          <Link href="/steps/jobs">공고 등록하기</Link>
        </Button>
      </div>
    );
  }

  // ---- Render: main content ------------------------------------------------
  return (
    <div className="flex flex-col gap-6">
      {/* Job selector */}
      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium" id="job-select-label">
          내 공고 선택
        </label>
        <Select
          value={effectiveJobId}
          onValueChange={(value) => setSelectedJobId(value)}
        >
          <SelectTrigger className="w-full min-h-[44px]" aria-labelledby="job-select-label">
            <SelectValue placeholder="공고를 선택하세요" />
          </SelectTrigger>
          <SelectContent>
            {myJobs.map((job) => (
              <SelectItem key={job.id} value={job.id}>
                {buildJobLabel(job)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Selected job summary */}
      {selectedJob && (
        <p className="text-sm text-muted-foreground">
          유형: {JOB_TYPE_LABELS[selectedJob.job_type] ?? selectedJob.job_type} |{' '}
          시급: {formatCurrency(selectedJob.hourly_rate)} |{' '}
          날짜: {formatDate(selectedJob.date)} |{' '}
          지역: {selectedJob.region ?? '-'}
        </p>
      )}

      {/* Applications area */}
      {applicationsQuery.isLoading ? (
        <div className="flex items-center justify-center py-12" role="status">
          <Loader2 className="mr-2 size-5 animate-spin" aria-hidden="true" />
          <span className="text-sm text-muted-foreground">지원자를 불러오는 중...</span>
        </div>
      ) : applicationsQuery.isError ? (
        <div className="flex flex-col items-center justify-center gap-3 py-12" role="alert">
          <p className="text-sm text-destructive">
            지원자 정보를 불러올 수 없습니다.
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
      ) : !applicationsQuery.data?.items || applicationsQuery.data.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 py-12">
          <div className="flex size-12 items-center justify-center rounded-full bg-muted">
            <Clock className="size-5 text-muted-foreground" aria-hidden="true" />
          </div>
          <p className="text-sm font-medium">지원자를 기다리는 중</p>
          <p className="text-center text-xs text-muted-foreground max-w-[260px]">
            공고 등록 후 보통 30분 내에 첫 지원이 옵니다. 이 페이지는 자동으로 새로고침됩니다.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">
            지원자 ({applicationsQuery.data.total}명)
          </p>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {applicationsQuery.data.items.map((app) => (
              <ApplicantCard
                key={app.id}
                application={app}
                onSendOffer={(a) => acceptMutation.mutate(a.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Contact reveal screen (shown after accepting applicant) */}
      {contactReveal && contactRevealJob && (
        <ContactRevealScreen
          open={!!contactReveal}
          onClose={() => {
            setContactReveal(null);
            setContactRevealJob(null);
          }}
          contactData={contactReveal}
          jobTitle={contactRevealJob.title}
          jobDate={contactRevealJob.date}
          jobTime={
            contactRevealJob.start_time && contactRevealJob.end_time
              ? `${contactRevealJob.start_time}~${contactRevealJob.end_time}`
              : undefined
          }
          jobRegion={contactRevealJob.region ?? undefined}
          hourlyRate={contactRevealJob.hourly_rate}
          viewerRole="studio"
        />
      )}
    </div>
  );
}
