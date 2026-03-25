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
  substitute: { label: '1회성', emoji: '\u261D\uFE0F' },
  regular: { label: '여러 회', emoji: '\u{1F504}' },
  contract: { label: '계약', emoji: '\u{1F4DD}' },
};

const SCORE_THRESHOLDS = [
  { min: 80, bg: 'bg-success/15', text: 'text-success', ring: 'ring-success/20' },
  { min: 60, bg: 'bg-amber-500/15', text: 'text-amber-600 dark:text-amber-400', ring: 'ring-amber-500/20' },
] as const;

function scoreStyle(score: number) {
  return SCORE_THRESHOLDS.find((t) => score >= t.min) ?? {
    bg: 'bg-gray-500/10',
    text: 'text-muted-foreground',
    ring: 'ring-gray-500/10',
  };
}

// ---------------------------------------------------------------------------
// Handoff Note Read-only View
// ---------------------------------------------------------------------------

function NoteRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-2 text-xs">
      <span className="shrink-0 w-[60px] text-muted-foreground">{label}</span>
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
          <NoteRow label="수업 주제">{note.class_topic}</NoteRow>
        )}
        {note.class_sequence_info && (
          <NoteRow label="수업 진도">{note.class_sequence_info}</NoteRow>
        )}
        {note.atmosphere_preference && (
          <NoteRow label="분위기">
            <span className="inline-flex items-center rounded-md border bg-muted/50 text-[10px] px-1.5 py-0 h-4 font-normal">
              {note.atmosphere_preference}
            </span>
          </NoteRow>
        )}
        {note.additional_notes && (
          <NoteRow label="기타">{note.additional_notes}</NoteRow>
        )}
      </div>

      {/* Sensitive fields — shown after acceptance */}
      {isFull ? (
        <div className="rounded-lg border border-success/30 bg-success/5 p-3 space-y-2">
          <p className="text-[10px] font-medium text-success mb-1">수락 후 공개</p>
          {fullNote.member_notes && (
            <NoteRow label="회원 정보">{fullNote.member_notes}</NoteRow>
          )}
          {fullNote.equipment_notes && (
            <NoteRow label="기구 세팅">{fullNote.equipment_notes}</NoteRow>
          )}
        </div>
      ) : note.has_sensitive_info ? (
        <div className="rounded-lg border border-dashed border-amber-300 bg-amber-50/50 px-3 py-2.5 dark:border-amber-700 dark:bg-amber-950/20">
          <p className="flex items-center gap-1.5 text-[11px] text-amber-700 dark:text-amber-300">
            <Lock className="size-3" />
            회원 정보 및 기구 세팅은 수락 후 공개됩니다
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
  const [expanded, setExpanded] = useState(false);
  const { job, matching, is_urgent } = item;
  const score = matching.total;
  const isPast = job.is_past;
  const typeInfo = JOB_TYPE_MAP[job.job_type] ?? { label: job.job_type, emoji: '' };
  const ss = scoreStyle(score);

  const handoffQuery = useQuery({
    queryKey: ['handoff-note', job.id],
    queryFn: () => api.handoffNotes.get(job.id),
    enabled: expanded && !!job.has_handoff_note,
    retry: false,
  });

  return (
    <Card
      className={cn(
        'group relative flex flex-col overflow-hidden transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5',
        isPast && 'opacity-50',
        is_urgent && !isPast && 'border-urgent/40 bg-urgent/[0.03] shadow-urgent/[0.06] shadow-md',
      )}
    >
      {/* Urgent top bar */}
      {is_urgent && !isPast && (
        <div className="h-1 w-full bg-gradient-to-r from-urgent via-urgent/80 to-urgent/40" />
      )}


      <CardContent className="flex flex-col gap-3 pb-3">
        {/* Row 1: Badges + Score pill */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            {is_urgent && !isPast && (
              <span className="inline-flex items-center rounded-md bg-urgent px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-urgent-foreground font-display animate-pulse-soft">
                Urgent
              </span>
            )}
            <Badge variant={isPast ? 'outline' : 'secondary'} className="text-[10px] font-display tracking-wide">
              {typeInfo.emoji} {typeInfo.label}
            </Badge>
          </div>
          <span
            className={cn(
              'inline-flex items-center gap-1 rounded-lg px-2 py-0.5 text-xs font-bold font-display ring-1',
              ss.bg, ss.text, ss.ring,
            )}
            aria-label={`Match score ${score}%`}
          >
            {score}%
          </span>
        </div>

        {/* Row 2: Title + Expand toggle */}
        <div className="flex items-start justify-between gap-2">
          <h3
            className={cn(
              'text-[15px] font-bold leading-snug cursor-pointer hover:text-primary transition-colors flex-1',
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
            className="shrink-0 p-1 text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-muted/50"
            onClick={() => setExpanded(!expanded)}
            aria-label={expanded ? 'Collapse' : 'Expand'}
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
            <span className="font-medium text-foreground">{job.start_time}~{job.end_time}</span>
          )}
        </div>

        {/* Row 4: Distance + Rate */}
        <div className="flex items-center gap-1.5 text-sm">
          {job.distance_text && (
            <>
              <span className="flex items-center gap-1 text-primary font-medium">
                <MapPin className="size-3.5 shrink-0" aria-hidden="true" />
                {job.distance_text}
                {job.travel_time_min && (
                  <span className="text-muted-foreground font-normal">({job.travel_time_min}min)</span>
                )}
              </span>
              <span className="text-border">&middot;</span>
            </>
          )}
          {!job.distance_text && job.region && (
            <>
              <span className="flex items-center gap-1 text-muted-foreground">
                <MapPin className="size-3.5 shrink-0" aria-hidden="true" />
                {job.region}
              </span>
              <span className="text-border">&middot;</span>
            </>
          )}
          <span className="flex items-center gap-1 font-bold">
            <Banknote className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
            {formatCurrency(job.hourly_rate)}/시간
          </span>
        </div>

        {/* Row 5: Premium info */}
        <div className="flex items-center gap-3 text-[11px]">
          {isPremium ? (
            <span className="flex items-center gap-1 text-muted-foreground">
              <Users className="size-3" />
              지원자 {item.application_count}명
            </span>
          ) : (
            <span className="flex items-center gap-1 text-muted-foreground/50">
              <Lock className="size-3" />
              지원자 ?명
            </span>
          )}
          <span className="text-border">&middot;</span>
          {isPremium && item.studio_avg_response_hours != null ? (
            <span className="flex items-center gap-1 text-muted-foreground">
              <Timer className="size-3" />
              ~{item.studio_avg_response_hours < 1
                ? `${Math.round(item.studio_avg_response_hours * 60)}분`
                : `${item.studio_avg_response_hours.toFixed(1)}시간`} 응답
            </span>
          ) : (
            <span className="flex items-center gap-1 text-muted-foreground/50">
              <Lock className="size-3" />
              응답 시간
            </span>
          )}
        </div>
      </CardContent>

      {/* Expandable detail section */}
      {expanded && (
        <div className="border-t border-border/50 px-6 py-3 bg-muted/20 animate-fade-in">
          {job.has_handoff_note ? (
            handoffQuery.isLoading ? (
              <div className="flex items-center gap-2 py-2">
                <Loader2 className="size-4 animate-spin text-primary" />
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

      {/* Action area */}
      <div className="px-6 pb-4 pt-2">
        <Button
          variant={isApplied ? 'secondary' : is_urgent && !isPast ? 'destructive' : 'default'}
          size="sm"
          className={cn(
            'min-h-[44px] w-full font-bold transition-all duration-200',
            !isApplied && !isPast && 'hover:scale-[1.01] active:scale-[0.99]',
            is_urgent && !isPast && !isApplied && 'bg-urgent text-urgent-foreground hover:bg-urgent/90',
          )}
          disabled={isApplied || isPast}
          onClick={(e) => {
            e.stopPropagation();
            onApply(job.id);
          }}
          aria-label={isApplied ? '지원 완료' : isPast ? '마감' : is_urgent ? '지금 지원' : '지원하기'}
        >
          {isApplied ? '지원 완료' : isPast ? '마감' : is_urgent ? '지금 지원' : '지원하기'}
        </Button>
      </div>
    </Card>
  );
}
