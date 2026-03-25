'use client';

import { useQuery } from '@tanstack/react-query';
import {
  Radio,
  CheckCircle2,
  MapPin,
  Eye,
  Send,
} from 'lucide-react';

import { api } from '@/lib/api-client';
import type {
  DispatchStatusResponse,
  DispatchRecordResponse,
} from '@/lib/api-types';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DispatchStatusWidgetProps {
  jobPostId: string;
}

// ---------------------------------------------------------------------------
// Constants — wave → radius mapping (internal only, never shown as "Wave")
// ---------------------------------------------------------------------------

const WAVE_RADIUS_KM: Record<number, number> = { 1: 5, 2: 10, 3: 15 };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function countByStatus(records: DispatchRecordResponse[]) {
  let notified = 0;   // total dispatched (sent)
  let checking = 0;   // dispatched, not yet responded
  let responded = 0;  // accepted + declined + timeout

  for (const r of records) {
    notified++;
    if (r.status === 'dispatched') {
      checking++;
    } else {
      responded++;
    }
  }

  return { notified, checking, responded };
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Radius expansion bar — shows 5km → 10km → 15km instead of "Wave 1/2/3" */
function RadiusProgressBar({ currentWave }: { currentWave: number }) {
  const steps = [
    { wave: 1, label: '5km' },
    { wave: 2, label: '10km' },
    { wave: 3, label: '15km' },
  ];

  return (
    <div className="space-y-1">
      <div className="flex gap-1.5" role="progressbar" aria-label="탐색 반경 확장 중">
        {steps.map(({ wave }) => {
          const isCurrent = wave === currentWave;
          const isPast = wave < currentWave;

          let segmentClass =
            'h-1.5 flex-1 rounded-full transition-colors duration-300';

          if (isCurrent) {
            segmentClass += ' bg-urgent animate-pulse-soft';
          } else if (isPast) {
            segmentClass += ' bg-urgent/40';
          } else {
            segmentClass += ' border border-border bg-transparent';
          }

          return <div key={wave} className={segmentClass} />;
        })}
      </div>
      <div className="flex justify-between">
        {steps.map(({ wave, label }) => (
          <span
            key={wave}
            className={`text-[10px] ${
              wave <= currentWave
                ? 'text-foreground font-medium'
                : 'text-muted-foreground/60'
            }`}
          >
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

/** Summary line: "N명 확인 중 · N명 응답" */
function ResponseSummary({ records }: { records: DispatchRecordResponse[] }) {
  const { checking, responded } = countByStatus(records);

  return (
    <div className="flex items-center gap-3 text-xs text-muted-foreground">
      {checking > 0 && (
        <span className="flex items-center gap-1">
          <Eye className="size-3" aria-hidden="true" />
          {checking}명 확인 중
        </span>
      )}
      {responded > 0 && (
        <span className="flex items-center gap-1">
          <CheckCircle2 className="size-3" aria-hidden="true" />
          {responded}명 응답
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function DispatchSkeleton() {
  return (
    <div className="mt-3 rounded-lg border p-3 space-y-2.5 animate-pulse">
      <div className="flex gap-1.5">
        <div className="h-1.5 flex-1 rounded-full bg-muted" />
        <div className="h-1.5 flex-1 rounded-full bg-muted" />
        <div className="h-1.5 flex-1 rounded-full bg-muted" />
      </div>
      <div className="h-4 w-3/4 rounded bg-muted" />
      <div className="h-3 w-1/2 rounded bg-muted" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Matched state
// ---------------------------------------------------------------------------

function MatchedView({ records }: { records: DispatchRecordResponse[] }) {
  const acceptedRecord = records.find((r) => r.status === 'accepted');
  const distanceText = acceptedRecord?.distance_km != null
    ? `${acceptedRecord.distance_km.toFixed(1)}km`
    : null;

  return (
    <div className="mt-3 rounded-lg border border-success/30 bg-success/5 p-3 animate-fade-in">
      <div className="flex items-center gap-2">
        <CheckCircle2 className="size-5 text-success shrink-0" aria-hidden="true" />
        <span className="text-sm font-semibold text-success">
          매칭 완료!
        </span>
        {distanceText && (
          <span className="ml-auto flex items-center gap-1 text-xs text-muted-foreground">
            <MapPin className="size-3" aria-hidden="true" />
            {distanceText}
          </span>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dispatching state — studio-owner-friendly view
// ---------------------------------------------------------------------------

function DispatchingView({ data }: { data: DispatchStatusResponse }) {
  const { current_wave, records } = data;
  const radiusKm = WAVE_RADIUS_KM[current_wave] ?? current_wave * 5;
  const totalNotified = records.length;

  return (
    <div className="mt-3 rounded-lg border border-urgent/30 bg-urgent/5 p-3 space-y-2.5 animate-fade-in">
      <RadiusProgressBar currentWave={current_wave} />

      <div className="flex items-center gap-2">
        <Radio className="size-4 text-urgent animate-pulse-soft shrink-0" aria-hidden="true" />
        <p className="text-sm text-foreground">
          <span className="font-medium">{radiusKm}km 반경</span>
          <span className="text-muted-foreground"> 강사 </span>
          <span className="font-semibold">{totalNotified}명</span>
          <span className="text-muted-foreground">에게 알림을 보냈어요</span>
        </p>
      </div>

      <ResponseSummary records={records} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function DispatchStatusWidget({ jobPostId }: DispatchStatusWidgetProps) {
  const { data, isLoading, isError } = useQuery<DispatchStatusResponse>({
    queryKey: ['dispatch', 'status', jobPostId],
    queryFn: () => api.dispatch.getJobStatus(jobPostId),
    refetchInterval: 15000,
  });

  if (isError) return null;
  if (isLoading) return <DispatchSkeleton />;
  if (!data || data.dispatch_mode === 'manual') return null;

  if (data.matched) {
    return <MatchedView records={data.records} />;
  }

  return <DispatchingView data={data} />;
}
