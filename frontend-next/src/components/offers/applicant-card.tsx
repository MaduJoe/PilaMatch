'use client';

import type { ApplicationWithInstructorResponse } from '@/lib/api-types';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Star, CheckCircle, Phone, MessageSquare } from 'lucide-react';
import { TierBadge } from '@/components/trust/tier-badge';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ApplicantCardProps {
  application: ApplicationWithInstructorResponse;
  onSendOffer: (app: ApplicationWithInstructorResponse) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getStatusDisplay(app: ApplicationWithInstructorResponse): {
  label: string;
  variant: 'default' | 'secondary' | 'destructive' | 'outline';
} {
  if (app.status === 'accepted') {
    return { label: '수락됨 (연락처 공개)', variant: 'default' };
  }

  if (app.has_offer) {
    switch (app.status) {
      case 'rejected':
        return { label: '거절됨', variant: 'destructive' };
      default:
        return { label: '수락 대기중', variant: 'secondary' };
    }
  }

  // No offer yet
  switch (app.status) {
    case 'withdrawn':
      return { label: '철회됨', variant: 'outline' };
    default:
      return { label: '대기중', variant: 'secondary' };
  }
}

/** Mask phone number for display: 010-1234-**** */
function maskPhone(phone: string): string {
  if (phone.length >= 8) {
    return phone.slice(0, -4) + '****';
  }
  return '***-****-****';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ApplicantCard({ application, onSendOffer }: ApplicantCardProps) {
  const instructorName = application.instructor_name ?? '강사';
  const experienceYears = application.instructor_experience_years ?? 0;
  const rating = application.instructor_rating;
  const coverLetter = application.cover_letter;
  const statusDisplay = getStatusDisplay(application);
  const canAccept = application.status === 'pending' && !application.has_offer;

  // Trust-tech data
  const completedSubs = application.instructor_completed_substitutes ?? 0;
  const noShowCount = application.instructor_no_show_count ?? 0;
  const reviewCount = application.instructor_review_count ?? 0;

  // Contact reveal
  const contactRevealed = application.contact_revealed;
  const fullPhone = application.instructor_full_phone;
  const maskedPhone = application.instructor_phone;

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 p-4">
        {/* Header: name + experience */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-base font-semibold" aria-label={`강사 이름: ${instructorName}`}>
            {instructorName}
          </span>
          <span className="text-sm text-muted-foreground">
            (경력 {experienceYears}년)
          </span>
          <TierBadge tier={application.instructor_tier ?? 't1_basic'} label={application.instructor_tier_label ?? undefined} />
        </div>

        {/* Rating */}
        {rating != null && rating > 0 && (
          <div className="flex items-center gap-1 text-sm text-muted-foreground" aria-label={`평점 ${rating.toFixed(1)} / 5.0`}>
            <Star className="size-4 fill-amber-400 text-amber-400" aria-hidden="true" />
            <span>{rating.toFixed(1)} / 5.0</span>
          </div>
        )}

        {/* Trust-tech data */}
        <div className="text-sm text-muted-foreground">
          대타 완료 {completedSubs}건 |{' '}
          노쇼 {noShowCount}회 |{' '}
          리뷰 {reviewCount}건
        </div>

        {/* Contact info - show directly when revealed */}
        {contactRevealed && fullPhone ? (
          <div className="rounded-lg border border-green-200 bg-green-50 p-3 dark:border-green-800 dark:bg-green-950/30">
            <div className="flex items-center gap-2 text-sm font-medium text-green-800 dark:text-green-300">
              <Phone className="size-4" aria-hidden="true" />
              <a href={`tel:${fullPhone}`} className="underline underline-offset-2">
                {fullPhone}
              </a>
            </div>
            <div className="mt-2 flex gap-2">
              <a
                href={`tel:${fullPhone}`}
                className="inline-flex min-h-[36px] flex-1 items-center justify-center gap-1.5 rounded-md bg-green-600 px-3 text-xs font-medium text-white transition-colors hover:bg-green-700"
                aria-label={`${instructorName} 강사에게 전화`}
              >
                <Phone className="size-3.5" aria-hidden="true" />
                전화
              </a>
              <a
                href={`sms:${fullPhone}`}
                className="inline-flex min-h-[36px] flex-1 items-center justify-center gap-1.5 rounded-md border border-green-300 bg-white px-3 text-xs font-medium text-green-700 transition-colors hover:bg-green-50 dark:border-green-700 dark:bg-green-950 dark:text-green-300 dark:hover:bg-green-900"
                aria-label={`${instructorName} 강사에게 문자`}
              >
                <MessageSquare className="size-3.5" aria-hidden="true" />
                문자
              </a>
            </div>
          </div>
        ) : contactRevealed && !fullPhone ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-800 dark:bg-amber-950/30">
            <p className="text-xs text-amber-800 dark:text-amber-300">
              수락 완료 — 강사가 아직 연락처를 등록하지 않았습니다.
            </p>
          </div>
        ) : maskedPhone ? (
          <div className="flex items-center gap-2 text-sm">
            <Phone className="size-4" aria-hidden="true" />
            <span className="text-muted-foreground">
              {maskPhone(maskedPhone)}
            </span>
          </div>
        ) : null}

        {/* Cover letter */}
        {coverLetter && (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {coverLetter}
          </p>
        )}

        {/* Status badge - only show non-accepted statuses */}
        {!contactRevealed && (
          <div>
            <Badge variant={statusDisplay.variant}>
              {statusDisplay.label}
            </Badge>
          </div>
        )}

        {/* Accept button (replaces "Send offer") */}
        {canAccept && (
          <Button
            className="min-h-[44px] w-full"
            onClick={() => onSendOffer(application)}
            aria-label={`${instructorName} 강사 수락 (연락처 공개)`}
          >
            <CheckCircle className="size-4" aria-hidden="true" />
            수락 (연락처 공개)
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
