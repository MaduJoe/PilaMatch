'use client';

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MapPin, CheckCircle2, Circle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

import api, { APIError } from '@/lib/api-client';
import type { CheckinResponse, CompletionConfirmResponse } from '@/lib/api-types';
import { Button } from '@/components/ui/button';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface JobProgressTrackerProps {
  jobPostId: string;
  role: 'instructor' | 'studio';
}

type StepStatus = 'done' | 'active' | 'pending';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

function getGpsPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      reject(new Error('GPS_UNAVAILABLE'));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 15_000,
      maximumAge: 60_000,
    });
  });
}

// ---------------------------------------------------------------------------
// Step indicator (circle + connecting line)
// ---------------------------------------------------------------------------

function StepIndicator({
  status,
  isLast,
}: {
  status: StepStatus;
  isLast: boolean;
}) {
  const circleClass =
    status === 'done'
      ? 'bg-emerald-600 text-white'
      : status === 'active'
        ? 'border-2 border-amber-400 text-amber-600'
        : 'border-2 border-muted text-muted-foreground';

  return (
    <div className="flex flex-col items-center">
      <div
        className={`flex size-6 shrink-0 items-center justify-center rounded-full ${circleClass}`}
        aria-hidden="true"
      >
        {status === 'done' ? (
          <CheckCircle2 className="size-4" />
        ) : (
          <Circle className="size-3" />
        )}
      </div>
      {!isLast && (
        <div
          className={`w-0.5 grow min-h-6 ${
            status === 'done' ? 'bg-emerald-600' : 'bg-muted'
          }`}
          aria-hidden="true"
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Check-in step content
// ---------------------------------------------------------------------------

function CheckinContent({
  role,
  checkin,
  jobPostId,
}: {
  role: 'instructor' | 'studio';
  checkin: CheckinResponse | null;
  jobPostId: string;
}) {
  const queryClient = useQueryClient();
  const [gpsLoading, setGpsLoading] = useState(false);

  const checkinMutation = useMutation({
    mutationFn: (coords: { latitude: number; longitude: number }) =>
      api.checkin.checkIn(jobPostId, coords),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['checkin', jobPostId] });
      if (data.is_valid) {
        toast.success(`체크인 완료! (센터에서 ${data.distance_meters}m)`);
      } else {
        toast.warning(
          `위치 확인됨 (센터에서 ${data.distance_meters}m) -- 200m 이내에서 다시 시도해주세요`,
        );
      }
    },
    onError: (error) => {
      const message =
        error instanceof APIError
          ? error.message
          : '체크인에 실패했습니다.';
      toast.error(message);
    },
  });

  const handleCheckin = useCallback(async () => {
    setGpsLoading(true);
    try {
      const position = await getGpsPosition();
      checkinMutation.mutate({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      });
    } catch {
      toast.error('위치를 가져올 수 없습니다. 위치 권한을 확인해주세요');
    } finally {
      setGpsLoading(false);
    }
  }, [checkinMutation]);

  const isLoading = gpsLoading || checkinMutation.isPending;

  // --- Studio view ---
  if (role === 'studio') {
    if (!checkin) {
      return (
        <p className="text-sm text-muted-foreground">강사 체크인 대기 중</p>
      );
    }
    if (checkin.is_valid) {
      return (
        <div className="flex items-center gap-1.5">
          <CheckCircle2 className="size-4 text-emerald-600" aria-hidden="true" />
          <span className="text-sm text-emerald-600 font-medium">
            강사 도착 확인 ({checkin.distance_meters}m)
          </span>
          <span className="text-xs text-muted-foreground ml-auto">
            {formatTime(checkin.checked_in_at)}
          </span>
        </div>
      );
    }
    // checked in but invalid distance
    return (
      <div className="flex items-center gap-1.5">
        <MapPin className="size-4 text-amber-500" aria-hidden="true" />
        <span className="text-sm text-amber-600 font-medium">
          강사 위치 확인됨 ({checkin.distance_meters}m)
        </span>
        <span className="text-xs text-muted-foreground ml-auto">
          {formatTime(checkin.checked_in_at)}
        </span>
      </div>
    );
  }

  // --- Instructor view ---
  if (checkin && checkin.is_valid) {
    return (
      <div className="flex items-center gap-1.5">
        <CheckCircle2 className="size-4 text-emerald-600" aria-hidden="true" />
        <span className="text-sm text-emerald-600 font-medium">
          체크인 완료 ({checkin.distance_meters}m)
        </span>
        <span className="text-xs text-muted-foreground ml-auto">
          {formatTime(checkin.checked_in_at)}
        </span>
      </div>
    );
  }

  if (checkin && !checkin.is_valid) {
    return (
      <div className="space-y-1.5">
        <div className="flex items-center gap-1.5">
          <MapPin className="size-4 text-amber-500" aria-hidden="true" />
          <span className="text-sm text-amber-600">
            위치 확인됨 ({checkin.distance_meters}m) -- 200m 이내에서 다시 시도해주세요
          </span>
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={handleCheckin}
          disabled={isLoading}
          className="min-h-[44px]"
          aria-label="체크인 재시도"
        >
          {isLoading ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              위치 확인 중...
            </>
          ) : (
            <>
              <MapPin className="size-4" aria-hidden="true" />
              체크인 재시도
            </>
          )}
        </Button>
      </div>
    );
  }

  // Not checked in yet
  return (
    <Button
      size="sm"
      onClick={handleCheckin}
      disabled={isLoading}
      className="min-h-[44px]"
      aria-label="체크인"
    >
      {isLoading ? (
        <>
          <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          위치 확인 중...
        </>
      ) : (
        <>
          <MapPin className="size-4" aria-hidden="true" />
          체크인
        </>
      )}
    </Button>
  );
}

// ---------------------------------------------------------------------------
// Completion step content
// ---------------------------------------------------------------------------

function CompletionContent({
  role,
  completion,
  jobPostId,
}: {
  role: 'instructor' | 'studio';
  completion: CompletionConfirmResponse | null;
  jobPostId: string;
}) {
  const queryClient = useQueryClient();

  const confirmMutation = useMutation({
    mutationFn: () => api.completion.confirm(jobPostId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['completion', jobPostId] });
      toast.success('수업 완료 확인!');
    },
    onError: (error) => {
      const message =
        error instanceof APIError
          ? error.message
          : '완료 확인에 실패했습니다.';
      toast.error(message);
    },
  });

  if (!completion) {
    // No completion record yet -- show confirm button
    return (
      <Button
        size="sm"
        onClick={() => confirmMutation.mutate()}
        disabled={confirmMutation.isPending}
        className="min-h-[44px]"
        aria-label="수업 완료 확인"
      >
        {confirmMutation.isPending ? (
          <>
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            확인 중...
          </>
        ) : (
          <>
            <CheckCircle2 className="size-4" aria-hidden="true" />
            수업 완료 확인
          </>
        )}
      </Button>
    );
  }

  const myConfirmed =
    role === 'instructor'
      ? completion.instructor_confirmed
      : completion.studio_confirmed;
  const otherConfirmed =
    role === 'instructor'
      ? completion.studio_confirmed
      : completion.instructor_confirmed;

  // Both confirmed
  if (completion.is_complete) {
    return (
      <div className="flex items-center gap-1.5">
        <CheckCircle2 className="size-4 text-emerald-600" aria-hidden="true" />
        <span className="text-sm text-emerald-600 font-semibold">
          수업 완료!
        </span>
      </div>
    );
  }

  // I confirmed, waiting for other
  if (myConfirmed && !otherConfirmed) {
    return (
      <div className="flex items-center gap-1.5">
        <CheckCircle2 className="size-4 text-emerald-600" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">
          내 확인 완료 -- 상대방 확인 대기 중...
        </span>
      </div>
    );
  }

  // Other confirmed, I haven't
  if (!myConfirmed && otherConfirmed) {
    return (
      <div className="space-y-1.5">
        <p className="text-sm text-amber-600 font-medium">
          상대방이 확인했습니다 -- 완료 확인을 눌러주세요
        </p>
        <Button
          size="sm"
          onClick={() => confirmMutation.mutate()}
          disabled={confirmMutation.isPending}
          className="min-h-[44px]"
          aria-label="수업 완료 확인"
        >
          {confirmMutation.isPending ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              확인 중...
            </>
          ) : (
            <>
              <CheckCircle2 className="size-4" aria-hidden="true" />
              완료 확인
            </>
          )}
        </Button>
      </div>
    );
  }

  // Neither confirmed (record exists but both false)
  return (
    <Button
      size="sm"
      onClick={() => confirmMutation.mutate()}
      disabled={confirmMutation.isPending}
      className="min-h-[44px]"
      aria-label="수업 완료 확인"
    >
      {confirmMutation.isPending ? (
        <>
          <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          확인 중...
        </>
      ) : (
        <>
          <CheckCircle2 className="size-4" aria-hidden="true" />
          수업 완료 확인
        </>
      )}
    </Button>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function JobProgressTracker({ jobPostId, role }: JobProgressTrackerProps) {
  // Fetch check-in status (404 = not checked in)
  const {
    data: checkin,
    isError: checkinError,
  } = useQuery<CheckinResponse | null>({
    queryKey: ['checkin', jobPostId],
    queryFn: async () => {
      try {
        return await api.checkin.getStatus(jobPostId);
      } catch (error) {
        if (error instanceof APIError && error.status === 404) {
          return null;
        }
        throw error;
      }
    },
  });

  // Fetch completion status (404 = not confirmed, poll every 30s)
  const {
    data: completion,
    isError: completionError,
  } = useQuery<CompletionConfirmResponse | null>({
    queryKey: ['completion', jobPostId],
    queryFn: async () => {
      try {
        return await api.completion.getStatus(jobPostId);
      } catch (error) {
        if (error instanceof APIError && error.status === 404) {
          return null;
        }
        throw error;
      }
    },
    refetchInterval: 30_000,
  });

  // Don't crash the parent if queries fail
  if (checkinError || completionError) {
    return null;
  }

  // Derive step statuses
  const checkinDone = checkin != null && checkin.is_valid;
  const completionDone = completion?.is_complete === true;

  const acceptStatus: StepStatus = 'done'; // always done (component only renders after acceptance)
  const checkinStatus: StepStatus = checkinDone
    ? 'done'
    : 'active';
  const completionStatus: StepStatus = completionDone
    ? 'done'
    : checkinDone
      ? 'active'
      : 'pending';

  const steps: {
    label: string;
    status: StepStatus;
    content: React.ReactNode;
  }[] = [
    {
      label: '수락 완료',
      status: acceptStatus,
      content: (
        <span className="text-sm text-emerald-600 font-medium">완료</span>
      ),
    },
    {
      label: '체크인',
      status: checkinStatus,
      content: (
        <CheckinContent
          role={role}
          checkin={checkin ?? null}
          jobPostId={jobPostId}
        />
      ),
    },
    {
      label: '수업 완료',
      status: completionStatus,
      content: (
        <CompletionContent
          role={role}
          completion={completion ?? null}
          jobPostId={jobPostId}
        />
      ),
    },
  ];

  return (
    <div className="mt-4 border-t pt-4" aria-label="수업 진행 상태">
      <div className="space-y-0">
        {steps.map((step, index) => (
          <div key={step.label} className="flex gap-3">
            <StepIndicator
              status={step.status}
              isLast={index === steps.length - 1}
            />
            <div className={`pb-4 ${index === steps.length - 1 ? 'pb-0' : ''} flex-1 min-w-0`}>
              <p className="text-xs font-medium text-muted-foreground mb-1">
                {step.label}
              </p>
              {step.content}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
