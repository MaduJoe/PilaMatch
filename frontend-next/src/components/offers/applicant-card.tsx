'use client';

import type { ApplicationWithInstructorResponse } from '@/lib/api-types';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Star, CheckCircle, Phone } from 'lucide-react';

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
    <Card className="flex flex-col gap-4 py-4">
      <CardContent className="flex flex-col gap-3">
        {/* Header: name + experience */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-base font-semibold" aria-label={`강사 이름: ${instructorName}`}>
            {instructorName}
          </span>
          <span className="text-sm text-muted-foreground">
            (경력 {experienceYears}년)
          </span>
          {/* PMF pivot: Premium badge hidden */}
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

        {/* Contact info */}
        {maskedPhone && (
          <div className="flex items-center gap-2 text-sm">
            <Phone className="size-4" aria-hidden="true" />
            {contactRevealed && fullPhone ? (
              <span className="font-medium text-foreground">{fullPhone}</span>
            ) : (
              <span className="text-muted-foreground">
                {maskPhone(maskedPhone)}
              </span>
            )}
          </div>
        )}

        {/* Cover letter */}
        {coverLetter && (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {coverLetter}
          </p>
        )}

        {/* Status badge */}
        <div>
          <Badge variant={statusDisplay.variant}>
            {statusDisplay.label}
          </Badge>
        </div>

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
