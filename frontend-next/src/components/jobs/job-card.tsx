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
  substitute: { label: '대타', emoji: '\u{1F504}' },
  regular: { label: '정규', emoji: '\u{1F4C5}' },
  contract: { label: '계약', emoji: '\u{1F4DD}' },
};

function scoreLabel(score: number): { text: string; className: string } {
  if (score >= 80) return { text: `최적 ${score}%`, className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' };
  if (score >= 60) return { text: `적합 ${score}%`, className: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200' };
  return { text: `${score}%`, className: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' };
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
  const matchLabel = scoreLabel(score);

  return (
    <Card
      className={cn(
        'flex flex-col transition-shadow hover:shadow-md overflow-hidden',
        isPast && 'opacity-60',
        is_urgent && !isPast && 'border-l-4 border-l-red-500 bg-red-50/50 dark:bg-red-950/20',
      )}
    >
      <CardContent className="flex flex-col gap-2.5 pb-3">
        {/* Row 1: Status badges + Score */}
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
            {isPast && (
              <Badge variant="outline" className="text-xs text-muted-foreground">
                마감
              </Badge>
            )}
          </div>
          <span
            className={cn('rounded-full px-2.5 py-0.5 text-xs font-bold', matchLabel.className)}
            aria-label={`매칭 점수 ${score}%`}
          >
            {matchLabel.text}
          </span>
        </div>

        {/* Row 2: Title + Region */}
        <h3
          className={cn(
            'text-base font-bold leading-tight cursor-pointer hover:underline',
            isPast && 'line-through text-muted-foreground',
          )}
          onClick={() => onDetail(item)}
          role="link"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter') onDetail(item); }}
        >
          {job.title}
        </h3>

        {/* Row 3: Date + Time */}
        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <Clock className="size-3.5 shrink-0" aria-hidden="true" />
          <span>{job.date}</span>
          {job.start_time && job.end_time && (
            <span>{job.start_time}~{job.end_time}</span>
          )}
        </div>

        {/* Row 4: Distance + Rate (key decision factors) */}
        <div className="flex items-center gap-3 text-sm">
          {job.distance_text && (
            <span className="flex items-center gap-1 text-blue-600 dark:text-blue-400 font-medium">
              <MapPin className="size-3.5 shrink-0" aria-hidden="true" />
              {job.distance_text}
              {job.travel_time_min && (
                <span className="text-muted-foreground font-normal">({job.travel_time_min}분)</span>
              )}
            </span>
          )}
          {!job.distance_text && job.region && (
            <span className="flex items-center gap-1 text-muted-foreground">
              <MapPin className="size-3.5 shrink-0" aria-hidden="true" />
              {job.region}
            </span>
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
              </div>
            </div>
          )}
          {/* Description */}
          {job.description && (
            <p className="text-xs text-muted-foreground whitespace-pre-wrap">{job.description}</p>
          )}
        </div>
      )}

      {/* Action area */}
      <div className="flex gap-2 px-6 pb-4 pt-1">
        <Button
          variant={isApplied ? 'secondary' : is_urgent && !isPast ? 'destructive' : 'default'}
          size="sm"
          className="min-h-[44px] flex-1 font-bold"
          disabled={isApplied || isPast}
          onClick={(e) => {
            e.stopPropagation();
            onApply(job.id);
          }}
          aria-label={isApplied ? '지원 완료' : isPast ? '마감' : is_urgent ? '지금 지원하기' : '지원하기'}
        >
          {isApplied ? '지원완료' : isPast ? '마감' : is_urgent ? '지금 지원하기' : '지원하기'}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="min-h-[44px] px-3"
          onClick={() => setExpanded(!expanded)}
          aria-label={expanded ? '상세 접기' : '상세 펼치기'}
          aria-expanded={expanded}
        >
          {expanded ? (
            <ChevronUp className="size-4" aria-hidden="true" />
          ) : (
            <ChevronDown className="size-4" aria-hidden="true" />
          )}
        </Button>
      </div>
    </Card>
  );
}
