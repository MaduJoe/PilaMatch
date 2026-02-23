'use client';

import type { ApplicationWithInstructorResponse } from '@/lib/api-types';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Star, Crown, Send } from 'lucide-react';

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
  if (app.has_offer) {
    // When an offer has been sent, show offer-related statuses.
    // The `status` field on ApplicationWithInstructorResponse reflects the
    // application status. When an offer exists, the backend typically marks
    // the application status accordingly:
    //  - pending  -> offer sent, awaiting response
    //  - accepted -> instructor accepted
    //  - rejected -> instructor rejected
    switch (app.status) {
      case 'accepted':
        return { label: '수락됨', variant: 'default' };
      case 'rejected':
        return { label: '거절됨', variant: 'destructive' };
      default:
        return { label: '오퍼 전송됨 (응답 대기)', variant: 'secondary' };
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

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ApplicantCard({ application, onSendOffer }: ApplicantCardProps) {
  const instructorName = application.instructor_name ?? '강사';
  const experienceYears = application.instructor_experience_years ?? 0;
  const rating = application.instructor_rating;
  const coverLetter = application.cover_letter;
  const statusDisplay = getStatusDisplay(application);
  const canSendOffer = application.status === 'pending' && !application.has_offer;

  return (
    <Card className="flex flex-col gap-4 py-4">
      <CardContent className="flex flex-col gap-3">
        {/* Header: name + premium badge */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-base font-semibold" aria-label={`강사 이름: ${instructorName}`}>
            {instructorName}
          </span>
          <span className="text-sm text-muted-foreground">
            (경력 {experienceYears}년)
          </span>
          {application.is_premium && (
            <Badge variant="default" className="bg-violet-600 text-white">
              <Crown className="size-3" aria-hidden="true" />
              Premium
            </Badge>
          )}
        </div>

        {/* Rating */}
        {rating != null && rating > 0 && (
          <div className="flex items-center gap-1 text-sm text-muted-foreground" aria-label={`평점 ${rating.toFixed(1)} / 5.0`}>
            <Star className="size-4 fill-amber-400 text-amber-400" aria-hidden="true" />
            <span>{rating.toFixed(1)} / 5.0</span>
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

        {/* Send offer button */}
        {canSendOffer && (
          <Button
            className="min-h-[44px] w-full"
            onClick={() => onSendOffer(application)}
            aria-label={`${instructorName} 강사에게 오퍼 보내기`}
          >
            <Send className="size-4" aria-hidden="true" />
            오퍼 보내기
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
