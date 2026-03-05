'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { JobPostWithMatchingItem, HandoffNotePublicResponse, HandoffNoteFullResponse } from '@/lib/api-types';
import api from '@/lib/api-client';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MapPin, Clock, Banknote, ChevronDown, ChevronUp, FileText, Lock, Loader2, Users, Timer } from 'lucide-react';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const JOB_TYPE_MAP: Record<string, { label: string; emoji: string }> = {
  substitute: { label: '1회성', emoji: '☝️' },
  // substitute: { label: '1회성', emoji: '\u{1F504}' },
  regular: { label: '여러 회', emoji: '\u{1F504}' },
  // regular: { label: '여러 회', emoji: '\u{1F4C5}' },
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
// Handoff Note Read-only View
// ---------------------------------------------------------------------------

function NoteRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-2 text-xs">
      <span className="shrink-0 w-[52px] text-muted-foreground">{label}</span>
      <span className="flex-1 whitespace-pre-wrap">{children}</span>
    </div>
  );
}

function HandoffNoteView({ note }: { note: HandoffNotePublicResponse | HandoffNoteFullResponse }) {
  const fullNote = note as HandoffNoteFullResponse;
  const hasSensitive = 'member_notes' in note || 'equipment_notes' in note;
  const isFull = hasSensitive && !!(fullNote.member_notes || fullNote.equipment_notes);

  return (
    <div className="space-y-2.5">
      <p className="flex items-center gap-1.5 text-xs font-semibold">
        <FileText className="size-3.5 text-primary" />
        인수인계 노트
      </p>

      <div className="rounded-lg border bg-background p-3 space-y-2">
        {note.class_topic && (
          <NoteRow label="주제">{note.class_topic}</NoteRow>
        )}
        {note.class_sequence_info && (
          <NoteRow label="진도">{note.class_sequence_info}</NoteRow>
        )}
        {note.atmosphere_preference && (
          <NoteRow label="분위기">
            <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 font-normal">
              {note.atmosphere_preference}
            </Badge>
          </NoteRow>
        )}
        {note.additional_notes && (
          <NoteRow label="안내">{note.additional_notes}</NoteRow>
        )}
      </div>

      {/* Sensitive fields — shown after acceptance */}
      {isFull ? (
        <div className="rounded-lg border border-green-200 bg-green-50/60 p-3 space-y-2 dark:border-green-800 dark:bg-green-950/20">
          <p className="text-[10px] font-medium text-green-700 dark:text-green-300 mb-1">수락 후 공개 정보</p>
          {fullNote.member_notes && (
            <NoteRow label="회원">{fullNote.member_notes}</NoteRow>
          )}
          {fullNote.equipment_notes && (
            <NoteRow label="기구">{fullNote.equipment_notes}</NoteRow>
          )}
        </div>
      ) : note.has_sensitive_info ? (
        <div className="rounded-lg border border-dashed border-amber-300 bg-amber-50/50 px-3 py-2.5 dark:border-amber-700 dark:bg-amber-950/20">
          <p className="flex items-center gap-1.5 text-[11px] text-amber-700 dark:text-amber-300">
            <Lock className="size-3" />
            회원 정보·기구 세팅은 수락 후 공개됩니다
          </p>
        </div>
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface JobCardProps {
  item: JobPostWithMatchingItem;
  isApplied: boolean;
  isPremium?: boolean;
  onApply: (jobId: string) => void;
  onDetail: (item: JobPostWithMatchingItem) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function JobCard({ item, isApplied, isPremium = false, onApply, onDetail }: JobCardProps) {
  const [expanded, setExpanded] = useState(true);
  const { job, matching, is_urgent } = item;
  const score = matching.total;
  const isPast = job.is_past;
  const isEarlyLocked = item.early_access_locked;
  const typeInfo = JOB_TYPE_MAP[job.job_type] ?? { label: job.job_type, emoji: '' };

  const handoffQuery = useQuery({
    queryKey: ['handoff-note', job.id],
    queryFn: () => api.handoffNotes.get(job.id),
    enabled: expanded && !!job.has_handoff_note,
    retry: false,
  });

  return (
    <Card
      className={cn(
        'relative flex flex-col transition-shadow hover:shadow-md overflow-hidden',
        isPast && 'opacity-60',
        isEarlyLocked && 'opacity-50',
        is_urgent && !isPast && 'border-l-4 border-l-red-500 bg-red-50/50 dark:bg-red-950/20',
      )}
    >
      {isEarlyLocked && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/60 backdrop-blur-[2px]">
          <div className="flex flex-col items-center gap-1.5 text-center px-4">
            <Lock className="size-5 text-primary" />
            <p className="text-xs font-semibold">프리미엄 회원 전용</p>
            <p className="text-[10px] text-muted-foreground">긴급 공고를 10분 먼저 확인하세요</p>
          </div>
        </div>
      )}
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

        {/* Row 5: Premium info — 경쟁률 + 응답률 */}
        <div className="flex items-center gap-3 text-xs">
          {isPremium ? (
            <span className="flex items-center gap-1 text-muted-foreground">
              <Users className="size-3" />
              {item.application_count}명 지원 중
            </span>
          ) : (
            <span className="flex items-center gap-1 text-muted-foreground/60">
              <Lock className="size-3" />
              ?명 지원 중
            </span>
          )}
          <span className="text-muted-foreground/30">·</span>
          {isPremium && item.studio_avg_response_hours != null ? (
            <span className="flex items-center gap-1 text-muted-foreground">
              <Timer className="size-3" />
              평균 {item.studio_avg_response_hours < 1
                ? `${Math.round(item.studio_avg_response_hours * 60)}분`
                : `${item.studio_avg_response_hours.toFixed(1)}시간`} 내 응답
            </span>
          ) : (
            <span className="flex items-center gap-1 text-muted-foreground/60">
              <Lock className="size-3" />
              응답 시간
            </span>
          )}
        </div>
      </CardContent>

      {/* Expandable detail section — Handoff Note */}
      {expanded && (
        <div className="border-t px-6 py-3 bg-muted/30">
          {job.has_handoff_note ? (
            handoffQuery.isLoading ? (
              <div className="flex items-center gap-2 py-2">
                <Loader2 className="size-4 animate-spin" />
                <span className="text-xs text-muted-foreground">인수인계 노트 불러오는 중...</span>
              </div>
            ) : handoffQuery.data ? (
              <HandoffNoteView note={handoffQuery.data} />
            ) : (
              <p className="text-xs text-muted-foreground">인수인계 노트를 불러올 수 없습니다.</p>
            )
          ) : (
            <p className="text-xs text-muted-foreground">인수인계 노트가 없습니다.</p>
          )}
        </div>
      )}

      {/* Action area - single apply button */}
      <div className="px-6 pb-4 pt-1">
        <Button
          variant={isApplied ? 'secondary' : is_urgent && !isPast ? 'destructive' : 'default'}
          size="sm"
          className="min-h-[44px] w-full font-bold"
          disabled={isApplied || isPast || isEarlyLocked}
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
