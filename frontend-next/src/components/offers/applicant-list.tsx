'use client';

import { useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import type { ApplicationWithInstructorResponse, JobPostResponse } from '@/lib/api-types';
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
import { SendOfferDialog } from './send-offer-dialog';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const JOB_TYPE_LABELS: Record<string, string> = {
  substitute: '대타',
  regular: '정규',
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
  const profileId = useAuthStore((s) => s.profileId);

  // ---- State ---------------------------------------------------------------
  const [selectedJobId, setSelectedJobId] = useState<string | undefined>(undefined);
  const [offerTarget, setOfferTarget] = useState<ApplicationWithInstructorResponse | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  // ---- Query: job posts ----------------------------------------------------
  const jobsQuery = useQuery({
    queryKey: ['studio-job-posts'],
    queryFn: () => api.jobPosts.list(),
  });

  // Filter to only my jobs (extra safety - API should already filter)
  const myJobs = useMemo(() => {
    if (!jobsQuery.data?.items) return [];
    if (!profileId) return jobsQuery.data.items;
    return jobsQuery.data.items.filter(
      (job) => job.studio_id === profileId,
    );
  }, [jobsQuery.data?.items, profileId]);

  // Auto-select first job if none selected
  const effectiveJobId = selectedJobId ?? myJobs[0]?.id;

  // ---- Query: applications for selected job --------------------------------
  const applicationsQuery = useQuery({
    queryKey: ['job-applications', effectiveJobId],
    queryFn: () => api.applications.getForJobPost(effectiveJobId!),
    enabled: !!effectiveJobId,
  });

  // ---- Selected job info ---------------------------------------------------
  const selectedJob = useMemo(
    () => myJobs.find((j) => j.id === effectiveJobId),
    [myJobs, effectiveJobId],
  );

  // ---- Handlers ------------------------------------------------------------
  function handleSendOffer(app: ApplicationWithInstructorResponse) {
    setOfferTarget(app);
    setDialogOpen(true);
  }

  function handleOfferSuccess() {
    // Refetch applications to update has_offer status
    void queryClient.invalidateQueries({
      queryKey: ['job-applications', effectiveJobId],
    });
  }

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
      ) : !applicationsQuery.data || applicationsQuery.data.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-2 py-12">
          <p className="text-sm text-muted-foreground">아직 지원자가 없습니다.</p>
          <p className="text-xs text-muted-foreground">
            강사가 공고에 지원하면 여기에 표시됩니다.
          </p>
        </div>
      ) : (
        <>
          <p className="text-sm font-medium">
            지원자 ({applicationsQuery.data.length}명)
          </p>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {applicationsQuery.data.map((app) => (
              <ApplicantCard
                key={app.id}
                application={app}
                onSendOffer={handleSendOffer}
              />
            ))}
          </div>
        </>
      )}

      {/* Send offer dialog */}
      <SendOfferDialog
        application={offerTarget}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSuccess={handleOfferSuccess}
      />
    </div>
  );
}
