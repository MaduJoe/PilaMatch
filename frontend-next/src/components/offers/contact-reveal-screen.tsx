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
  jobTitle?: string;
  jobDate?: string;
  jobTime?: string;
  jobRegion?: string;
  hourlyRate?: number;
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
  const partnerName =
    viewerRole === 'studio'
      ? contactData.instructor_name
      : contactData.studio_name;

  const partnerPhone =
    viewerRole === 'studio'
      ? contactData.instructor_phone
      : contactData.studio_phone;

  const partnerLabel = viewerRole === 'studio' ? 'Instructor' : 'Studio';
  const studioAddress = contactData.studio_address;
  const hasJobContext = jobTitle || jobDate || jobTime || jobRegion || hourlyRate;

  return (
    <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose(); }}>
      <DialogContent
        showCloseButton={false}
        className="fixed inset-0 z-50 flex h-dvh max-h-dvh w-full max-w-full translate-x-0 translate-y-0 top-0 left-0 flex-col items-center justify-center rounded-none border-none p-6 sm:max-w-full data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95"
        style={{
          background: 'radial-gradient(ellipse 100% 80% at 50% 30%, oklch(0.55 0.16 155 / 12%) 0%, transparent 60%), var(--background)',
        }}
      >
        <DialogTitle className="sr-only">Match Complete</DialogTitle>
        <DialogDescription className="sr-only">
          {partnerLabel} {partnerName} matched. Contact revealed.
        </DialogDescription>

        <div className="flex w-full max-w-md flex-col items-center gap-6 overflow-y-auto py-4">
          {/* Success icon */}
          <div className="flex flex-col items-center gap-4 animate-slide-up">
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-success/20 blur-xl scale-150" />
              <div className="relative flex items-center justify-center rounded-full bg-success/10 p-5 ring-2 ring-success/20">
                <CheckCircle2 className="size-14 text-success" strokeWidth={1.5} />
              </div>
            </div>
            <h2 className="font-display text-3xl font-extrabold tracking-tight text-foreground">
              Match!
            </h2>
            <p className="text-center text-sm text-muted-foreground leading-relaxed">
              Connected with <span className="font-semibold text-foreground">{partnerName}</span>
              <br />
              Reach out directly via phone or text.
            </p>
          </div>

          {/* Contact card */}
          <Card className="w-full border-success/20 shadow-xl shadow-success/[0.06] animate-fade-up" style={{ animationDelay: '150ms' }}>
            <CardContent className="flex flex-col gap-4 p-6">
              <div className="text-center">
                <p className="font-display text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">{partnerLabel}</p>
                <p className="font-display text-xl font-bold mt-1">{partnerName}</p>
              </div>

              <div className="flex items-center justify-center gap-2">
                <Phone className="size-5 text-success" aria-hidden="true" />
                <span
                  className="font-display text-2xl font-bold tracking-wide"
                  aria-label={`Phone ${partnerPhone}`}
                >
                  {partnerPhone}
                </span>
              </div>

              {viewerRole === 'instructor' && studioAddress && (
                <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                  <MapPin className="size-4 shrink-0" aria-hidden="true" />
                  <span>{studioAddress}</span>
                </div>
              )}

              <Separator />

              <div className="flex flex-col gap-3">
                <Button
                  asChild
                  size="lg"
                  className="min-h-[48px] w-full bg-success text-success-foreground hover:bg-success/90 font-display font-semibold"
                >
                  <a href={`tel:${partnerPhone}`} aria-label={`Call ${partnerName}`}>
                    <Phone className="size-5" aria-hidden="true" />
                    Call
                  </a>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="min-h-[48px] w-full border-success/30 text-success hover:bg-success/5 font-display font-semibold"
                >
                  <a href={`sms:${partnerPhone}`} aria-label={`Text ${partnerName}`}>
                    <MessageSquare className="size-5" aria-hidden="true" />
                    Text
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Job context */}
          {hasJobContext && (
            <div className="flex w-full flex-col gap-2 rounded-xl bg-muted/40 p-4 animate-fade-up" style={{ animationDelay: '300ms' }}>
              {jobTitle && (
                <p className="text-sm font-semibold">{jobTitle}</p>
              )}
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
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
                    {formatCurrency(hourlyRate)}/hr
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Dismiss */}
          <Button
            variant="ghost"
            size="lg"
            className="min-h-[48px] w-full max-w-md font-display"
            onClick={onClose}
            aria-label="Dismiss"
          >
            Done
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
