'use client';

import { CheckCircle2, Phone, MessageSquare, MapPin, Clock, Calendar, Coins } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { formatCurrency, formatDate } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ContactRevealScreenProps {
  open: boolean;
  onClose: () => void;
  contactData: {
    instructor_phone: string;
    instructor_name: string;
    studio_phone: string;
    studio_name: string;
    studio_address?: string | null;
  };
  /** Job context for display */
  jobTitle?: string;
  jobDate?: string;
  jobTime?: string;
  jobRegion?: string;
  hourlyRate?: number;
  /** Which role is viewing this */
  viewerRole: 'instructor' | 'studio';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ContactRevealScreen({
  open,
  onClose,
  contactData,
  jobTitle,
  jobDate,
  jobTime,
  jobRegion,
  hourlyRate,
  viewerRole,
}: ContactRevealScreenProps) {
  // Determine which partner info to display based on viewer role
  const partnerName =
    viewerRole === 'studio'
      ? contactData.instructor_name
      : contactData.studio_name;

  const partnerPhone =
    viewerRole === 'studio'
      ? contactData.instructor_phone
      : contactData.studio_phone;

  const partnerLabel = viewerRole === 'studio' ? '강사' : '스튜디오';

  const studioAddress = contactData.studio_address;

  const hasJobContext = jobTitle || jobDate || jobTime || jobRegion || hourlyRate;

  return (
    <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose(); }}>
      <DialogContent
        showCloseButton={false}
        className="fixed inset-0 z-50 flex h-dvh max-h-dvh w-full max-w-full translate-x-0 translate-y-0 top-0 left-0 flex-col items-center justify-center rounded-none border-none bg-green-50 p-6 dark:bg-green-950/30 sm:max-w-full data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95"
      >
        {/* Accessible dialog title and description */}
        <DialogTitle className="sr-only">매칭 완료</DialogTitle>
        <DialogDescription className="sr-only">
          {partnerLabel} {partnerName}님과 매칭이 완료되었습니다.
          연락처가 공개되었습니다.
        </DialogDescription>

        {/* Scrollable content area */}
        <div className="flex w-full max-w-md flex-col items-center gap-6 overflow-y-auto py-4">
          {/* --- Success icon & heading --- */}
          <div className="flex flex-col items-center gap-3">
            <div
              className="flex items-center justify-center rounded-full bg-green-100 p-4 dark:bg-green-900/50"
              aria-hidden="true"
            >
              <CheckCircle2 className="size-16 text-green-600 dark:text-green-400" />
            </div>
            <h2 className="text-2xl font-bold text-green-800 dark:text-green-200">
              매칭 완료!
            </h2>
            <p className="text-center text-sm text-green-700 dark:text-green-300">
              {partnerLabel} {partnerName}님과 매칭되었습니다.
              <br />
              아래 연락처로 직접 연락해 주세요.
            </p>
          </div>

          {/* --- Contact card --- */}
          <Card className="w-full border-green-200 bg-white shadow-lg dark:border-green-800 dark:bg-green-950/50">
            <CardContent className="flex flex-col gap-4 p-5">
              {/* Partner name */}
              <div className="text-center">
                <p className="text-sm text-muted-foreground">{partnerLabel}</p>
                <p className="text-xl font-bold">{partnerName}</p>
              </div>

              {/* Phone number */}
              <div className="flex items-center justify-center gap-2">
                <Phone className="size-5 text-green-600 dark:text-green-400" aria-hidden="true" />
                <span
                  className="text-2xl font-bold font-mono tracking-wide"
                  aria-label={`전화번호 ${partnerPhone}`}
                >
                  {partnerPhone}
                </span>
              </div>

              {/* Studio address (shown when instructor is viewing) */}
              {viewerRole === 'instructor' && studioAddress && (
                <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                  <MapPin className="size-4 shrink-0" aria-hidden="true" />
                  <span>{studioAddress}</span>
                </div>
              )}

              <Separator />

              {/* Action buttons */}
              <div className="flex flex-col gap-3">
                <Button
                  asChild
                  size="lg"
                  className="min-h-[48px] w-full bg-green-600 text-white hover:bg-green-700 dark:bg-green-600 dark:hover:bg-green-500"
                >
                  <a
                    href={`tel:${partnerPhone}`}
                    aria-label={`${partnerName}님에게 전화하기`}
                  >
                    <Phone className="size-5" aria-hidden="true" />
                    전화하기
                  </a>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="min-h-[48px] w-full border-green-300 text-green-700 hover:bg-green-50 dark:border-green-700 dark:text-green-300 dark:hover:bg-green-950/50"
                >
                  <a
                    href={`sms:${partnerPhone}`}
                    aria-label={`${partnerName}님에게 문자 보내기`}
                  >
                    <MessageSquare className="size-5" aria-hidden="true" />
                    문자 보내기
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* --- Job context --- */}
          {hasJobContext && (
            <div className="flex w-full flex-col gap-2 rounded-lg bg-green-100/50 p-4 dark:bg-green-900/20">
              {jobTitle && (
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  {jobTitle}
                </p>
              )}
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-green-700 dark:text-green-300">
                {jobDate && (
                  <span className="flex items-center gap-1">
                    <Calendar className="size-3.5 shrink-0" aria-hidden="true" />
                    {formatDate(jobDate)}
                  </span>
                )}
                {jobTime && (
                  <span className="flex items-center gap-1">
                    <Clock className="size-3.5 shrink-0" aria-hidden="true" />
                    {jobTime}
                  </span>
                )}
                {jobRegion && (
                  <span className="flex items-center gap-1">
                    <MapPin className="size-3.5 shrink-0" aria-hidden="true" />
                    {jobRegion}
                  </span>
                )}
                {hourlyRate != null && hourlyRate > 0 && (
                  <span className="flex items-center gap-1">
                    <Coins className="size-3.5 shrink-0" aria-hidden="true" />
                    시급 {formatCurrency(hourlyRate)}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* --- Dismiss button --- */}
          <Button
            variant="ghost"
            size="lg"
            className="min-h-[48px] w-full max-w-md text-green-700 hover:bg-green-100 dark:text-green-300 dark:hover:bg-green-900/30"
            onClick={onClose}
            aria-label="확인하고 닫기"
          >
            확인
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
