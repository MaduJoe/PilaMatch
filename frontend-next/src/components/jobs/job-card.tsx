'use client';

import { useState } from 'react';
import type { JobPostWithMatchingItem } from '@/lib/api-types';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MapPin, Clock, Banknote, ChevronDown, ChevronUp } from 'lucide-react';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const JOB_TYPE_MAP: Record<string, { label: string; emoji: string }> = {
  substitute: { label: '1회성', emoji: '\u{1F504}' },
  regular: { label: '여러 회', emoji: '\u{1F4C5}' },
  contract: { label: '계약', emoji: '\u{1F4DD}' },
};

const SCORE_THRESHOLDS = [
  { min: 80, color: 'bg-green-500' },
  { min: 60, color: 'bg-amber-500' },
] as const;

function scoreColor(score: number): string {
  return SCORE_THRESHOLDS.find((t) => score >= t.min)?.color ?? 'bg-gray-400';
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
  const [expanded, setExpanded] = useState(false);
  const { job, matching, is_urgent } = item;
  const score = matching.total;
  const isPast = job.is_past;
  const typeInfo = JOB_TYPE_MAP[job.job_type] ?? { label: job.job_type, emoji: '' };
  const breakdown = matching.breakdown;

  return (
    <Card
      className={cn(
        'flex flex-col transition-shadow hover:shadow-md overflow-hidden',
        isPast && 'opacity-60',
        is_urgent && !isPast && 'border-l-4 border-l-red-500 bg-red-50/50 dark:bg-red-950/20',
      )}
    >
      <CardContent className="flex flex-col gap-2.5 pb-3">
        {/* Row 1: Badges (max 3) + Score dot */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            {is_urgent && !isPast && (
              <Badge variant="destructive" className="text-xs font-bold px-2 py-0.5">
                긴급
              </Badge>
            )}
            <Badge variant={isPast ? 'outline' : 'secondary'} className="text-xs">
              {typeInfo.emoji} {typeInfo.label}
            </Badge>
          </div>
          <span
            className="flex items-center gap-1 text-xs font-bold text-muted-foreground"
            aria-label={`매칭 점수 ${score}%`}
          >
            <span className={cn('inline-block size-2 rounded-full', scoreColor(score))} />
            {score}
          </span>
        </div>

        {/* Row 2: Title + Expand toggle */}
        <div className="flex items-start justify-between gap-2">
          <h3
            className={cn(
              'text-base font-bold leading-tight cursor-pointer hover:underline flex-1',
              isPast && 'line-through text-muted-foreground',
            )}
            onClick={() => onDetail(item)}
            role="link"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter') onDetail(item); }}
          >
            {job.title}
          </h3>
          <button
            className="shrink-0 p-1 text-muted-foreground hover:text-foreground"
            onClick={() => setExpanded(!expanded)}
            aria-label={expanded ? '상세 접기' : '상세 펼치기'}
            aria-expanded={expanded}
          >
            {expanded ? (
              <ChevronUp className="size-4" aria-hidden="true" />
            ) : (
              <ChevronDown className="size-4" aria-hidden="true" />
            )}
          </button>
        </div>

        {/* Row 3: Date + Time */}
        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <Clock className="size-3.5 shrink-0" aria-hidden="true" />
          <span>{job.date}</span>
          {job.start_time && job.end_time && (
            <span>{job.start_time}~{job.end_time}</span>
          )}
        </div>

        {/* Row 4: Distance · Rate in one line */}
        <div className="flex items-center gap-1 text-sm">
          {job.distance_text && (
            <>
              <span className="flex items-center gap-1 text-blue-600 dark:text-blue-400 font-medium">
                <MapPin className="size-3.5 shrink-0" aria-hidden="true" />
                {job.distance_text}
                {job.travel_time_min && (
                  <span className="text-muted-foreground font-normal">({job.travel_time_min}분)</span>
                )}
              </span>
              <span className="text-muted-foreground">·</span>
            </>
          )}
          {!job.distance_text && job.region && (
            <>
              <span className="flex items-center gap-1 text-muted-foreground">
                <MapPin className="size-3.5 shrink-0" aria-hidden="true" />
                {job.region}
              </span>
              <span className="text-muted-foreground">·</span>
            </>
          )}
          <span className="flex items-center gap-1 font-bold">
            <Banknote className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
            {formatCurrency(job.hourly_rate)}/시간
          </span>
        </div>
      </CardContent>

      {/* Expandable detail section */}
      {expanded && (
        <div className="border-t px-6 py-3 bg-muted/30">
          {/* Matching breakdown */}
          {breakdown && (
            <div className="mb-2">
              <p className="text-xs font-medium text-muted-foreground mb-1">매칭 상세</p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs">
                {breakdown.distance && (
                  <span>거리: <strong>{breakdown.distance.score}점</strong></span>
                )}
                {breakdown.region && (
                  <span>지역: <strong>{breakdown.region.score}점</strong></span>
                )}
                {breakdown.experience && (
                  <span>경력: <strong>{breakdown.experience.score}점</strong></span>
                )}
                {breakdown.certifications && (
                  <span>자격: <strong>{breakdown.certifications.score}점</strong></span>
                )}
                {breakdown.hourly_rate && (
                  <span>시급: <strong>{breakdown.hourly_rate.score}점</strong></span>
                )}
                {breakdown.style && (
                  <span>스타일: <strong>{breakdown.style.score}점</strong></span>
                )}
              </div>
            </div>
          )}
          {/* Handoff note indicator */}
          {job.has_handoff_note && (
            <Badge variant="outline" className="mb-2 text-xs border-blue-300 text-blue-700 dark:border-blue-600 dark:text-blue-300">
              인수인계 노트 있음
            </Badge>
          )}
          {/* Description */}
          {job.description && (
            <p className="text-xs text-muted-foreground whitespace-pre-wrap">{job.description}</p>
          )}
        </div>
      )}

      {/* Action area - single apply button */}
      <div className="px-6 pb-4 pt-1">
        <Button
          variant={isApplied ? 'secondary' : is_urgent && !isPast ? 'destructive' : 'default'}
          size="sm"
          className="min-h-[44px] w-full font-bold"
          disabled={isApplied || isPast}
          onClick={(e) => {
            e.stopPropagation();
            onApply(job.id);
          }}
          aria-label={isApplied ? '지원 완료' : isPast ? '마감' : is_urgent ? '지금 지원하기' : '지원하기'}
        >
          {isApplied ? '지원완료' : isPast ? '마감' : is_urgent ? '지금 지원하기' : '지원하기'}
        </Button>
      </div>
    </Card>
  );
}
