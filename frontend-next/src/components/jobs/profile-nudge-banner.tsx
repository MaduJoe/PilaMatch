'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import api from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, ArrowRight, X } from 'lucide-react';

interface ProfileNudgeBannerProps {
  /** Whether the banner should be shown (e.g. after a failed apply attempt) */
  show: boolean;
  onDismiss: () => void;
}

export function ProfileNudgeBanner({ show, onDismiss }: ProfileNudgeBannerProps) {
  const { data } = useQuery({
    queryKey: ['profile', 'completeness'],
    queryFn: () => api.profileCompleteness.get(),
    enabled: show,
  });

  if (!show || !data || data.percentage >= 70) return null;

  const missingDisplay = data.missing_fields_display ?? {};
  const missingLabels = Object.values(missingDisplay);
  const percentage = data.percentage;

  return (
    <div
      role="alert"
      className="relative w-full rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm dark:border-amber-700 dark:bg-amber-950/30"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 size-5 shrink-0 text-amber-600" aria-hidden="true" />
        <div className="flex-1 space-y-2">
          <p className="text-sm font-medium text-amber-900 dark:text-amber-200">
            지원하려면 프로필을 조금 더 완성해주세요 ({percentage}% &rarr; 70%)
          </p>
          {missingLabels.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {missingLabels.map((label) => (
                <Badge
                  key={label}
                  variant="outline"
                  className="border-amber-400 text-xs text-amber-800 dark:text-amber-300"
                >
                  {label}
                </Badge>
              ))}
            </div>
          )}
          <Button
            size="sm"
            className="mt-1 min-h-[44px]"
            asChild
          >
            <Link href="/steps/profile">
              프로필 완성하기
              <ArrowRight className="ml-1 size-3.5" aria-hidden="true" />
            </Link>
          </Button>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="size-8 shrink-0 text-amber-600 hover:text-amber-800"
          onClick={onDismiss}
          aria-label="닫기"
        >
          <X className="size-3.5" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}
