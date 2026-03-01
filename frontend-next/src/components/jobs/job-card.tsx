'use client';

import type { JobPostWithMatchingItem } from '@/lib/api-types';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const JOB_TYPE_MAP: Record<string, { label: string; emoji: string }> = {
  substitute: { label: '대타', emoji: '\u{1F504}' },
  regular: { label: '정규', emoji: '\u{1F4C5}' },
  contract: { label: '계약', emoji: '\u{1F4DD}' },
};

function scoreColorClass(score: number): string {
  if (score >= 80) return 'text-green-600 dark:text-green-400';
  if (score >= 60) return 'text-orange-500 dark:text-orange-400';
  return 'text-muted-foreground';
}

function scoreBadgeVariant(score: number): 'default' | 'secondary' | 'outline' {
  if (score >= 80) return 'default';
  if (score >= 60) return 'secondary';
  return 'outline';
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface JobCardProps {
  item: JobPostWithMatchingItem;
  isApplied: boolean;
  onApply: (jobId: string) => void;
  onDetail: (item: JobPostWithMatchingItem) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function JobCard({ item, isApplied, onApply, onDetail }: JobCardProps) {
  const { job, matching, is_premium, is_urgent } = item;
  const score = matching.total;
  const isPast = job.is_past;
  const typeInfo = JOB_TYPE_MAP[job.job_type] ?? { label: job.job_type, emoji: '' };
  const breakdown = matching.breakdown;

  return (
    <Card
      className={cn(
        'flex flex-col justify-between transition-shadow hover:shadow-md',
        isPast && 'opacity-60',
      )}
    >
      <CardContent className="flex flex-col gap-3">
        {/* Row 1: Type + badges + score */}
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={isPast ? 'outline' : 'secondary'} className="text-xs">
            {typeInfo.emoji} {typeInfo.label}
          </Badge>

          {is_premium && (
            <Badge variant="default" className="bg-violet-600 text-xs text-white">
              Premium
            </Badge>
          )}

          {is_urgent && (
            <Badge variant="destructive" className="text-xs">
              긴급
            </Badge>
          )}

          {isPast && (
            <Badge variant="outline" className="text-xs text-muted-foreground">
              지난공고
            </Badge>
          )}

          {/* Matching score */}
          <span
            className={cn('ml-auto text-sm font-bold', scoreColorClass(score))}
            aria-label={`매칭 점수 ${score}%`}
          >
            <Badge variant={scoreBadgeVariant(score)} className="text-xs">
              {score}%
            </Badge>
          </span>
        </div>

        {/* Row 2: Title (strikethrough if past) */}
        <h3
          className={cn(
            'text-base font-semibold leading-tight',
            isPast && 'line-through text-muted-foreground',
          )}
        >
          {job.title}
        </h3>

        {/* Row 3: Region + date */}
        <p className="text-sm text-muted-foreground">
          {job.region ?? '-'} | {job.date}
        </p>

        {/* Row 4: Hourly rate */}
        <p className="text-base font-bold">
          {formatCurrency(job.hourly_rate)} / 시간
        </p>

        {/* Row 5: Description (truncated) */}
        {job.description && (
          <p className="text-sm text-muted-foreground line-clamp-1">
            {job.description.length > 40
              ? job.description.slice(0, 40) + '...'
              : job.description}
          </p>
        )}

        {/* Row 6: Matching breakdown (inline) */}
        {breakdown && (
          <p className="text-xs text-muted-foreground">
            지역 {breakdown.region?.score ?? 0} | 경력 {breakdown.experience?.score ?? 0} | 자격{' '}
            {breakdown.certifications?.score ?? 0} | 시급 {breakdown.hourly_rate?.score ?? 0}
          </p>
        )}
      </CardContent>

      {/* Row 7: Action buttons */}
      <div className="flex gap-2 px-6 pb-6">
        <Button
          variant={isApplied ? 'secondary' : 'default'}
          size="sm"
          className="min-h-[44px] flex-1"
          disabled={isApplied || isPast}
          onClick={() => onApply(job.id)}
          aria-label={isApplied ? '지원 완료' : isPast ? '지원 불가' : '지원하기'}
        >
          {isApplied ? '지원완료' : isPast ? '지원 불가' : '지원하기'}
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="min-h-[44px] flex-1"
          onClick={() => onDetail(item)}
          aria-label="공고 상세 보기"
        >
          상세
        </Button>
      </div>
    </Card>
  );
}
