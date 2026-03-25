'use client';

import { useQuery } from '@tanstack/react-query';
import {
  Radio,
  CheckCircle2,
  Clock,
  Users,
  MapPin,
} from 'lucide-react';

import { api } from '@/lib/api-client';
import type {
  DispatchStatusResponse,
  DispatchRecordResponse,
} from '@/lib/api-types';
import { Badge } from '@/components/ui/badge';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DispatchStatusWidgetProps {
  jobPostId: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const WAVE_CONFIG: { wave: number; radiusKm: number }[] = [
  { wave: 1, radiusKm: 5 },
  { wave: 2, radiusKm: 10 },
  { wave: 3, radiusKm: 15 },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function countByStatus(records: DispatchRecordResponse[]) {
  let pending = 0;
  let accepted = 0;
  let declined = 0;
  let timeout = 0;

  for (const r of records) {
    switch (r.status) {
      case 'dispatched':
        pending++;
        break;
      case 'accepted':
        accepted++;
        break;
      case 'declined':
        declined++;
        break;
      case 'timeout':
        timeout++;
        break;
    }
  }

  return { pending, accepted, declined, timeout };
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function WaveProgressBar({ currentWave }: { currentWave: number }) {
  return (
    <div className="flex gap-1.5" role="progressbar" aria-label={`Wave ${currentWave} 진행 중`}>
      {WAVE_CONFIG.map(({ wave }) => {
        const isCurrent = wave === currentWave;
        const isPast = wave < currentWave;

        let segmentClass =
          'h-1.5 flex-1 rounded-full transition-colors duration-300';

        if (isCurrent) {
          segmentClass += ' bg-urgent animate-pulse-soft';
        } else if (isPast) {
          segmentClass += ' bg-muted-foreground/30';
        } else {
          segmentClass += ' border border-border bg-transparent';
        }

        return <div key={wave} className={segmentClass} />;
      })}
    </div>
  );
}

function StatusCounts({ records }: { records: DispatchRecordResponse[] }) {
  const { pending, accepted, declined, timeout } = countByStatus(records);

  const items: { label: string; count: number; color: string }[] = [];

  if (pending > 0) items.push({ label: '대기', count: pending, color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' });
  if (accepted > 0) items.push({ label: '수락', count: accepted, color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' });
  if (declined > 0) items.push({ label: '거절', count: declined, color: 'bg-muted text-muted-foreground' });
  if (timeout > 0) items.push({ label: '타임아웃', count: timeout, color: 'bg-muted text-muted-foreground' });

  if (items.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map(({ label, count, color }) => (
        <Badge
          key={label}
          variant="outline"
          className={`border-transparent text-[11px] font-medium ${color}`}
        >
          {label} {count}
        </Badge>
      ))}
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
      <div className="flex gap-1.5">
        <div className="h-5 w-12 rounded-full bg-muted" />
        <div className="h-5 w-12 rounded-full bg-muted" />
      </div>
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
// Dispatching state
// ---------------------------------------------------------------------------

function DispatchingView({ data }: { data: DispatchStatusResponse }) {
  const { current_wave, records } = data;
  const waveConfig = WAVE_CONFIG.find((w) => w.wave === current_wave);
  const radiusKm = waveConfig?.radiusKm ?? current_wave * 5;
  const waveRecords = records.filter((r) => r.wave_number === current_wave);
  const waveCount = waveRecords.length;

  return (
    <div className="mt-3 rounded-lg border border-urgent/30 bg-urgent/5 p-3 space-y-2.5 animate-fade-in">
      <WaveProgressBar currentWave={current_wave} />

      <div className="flex items-center gap-2">
        <Radio className="size-4 text-urgent animate-pulse-soft shrink-0" aria-hidden="true" />
        <p className="text-sm text-foreground">
          <span className="font-semibold">Wave {current_wave}</span>
          <span className="text-muted-foreground">
            {' '}&mdash; {radiusKm}km 반경{' '}
          </span>
          <span className="font-medium">
            {waveCount}명
          </span>
          <span className="text-muted-foreground">에게 요청 중</span>
        </p>
      </div>

      <StatusCounts records={records} />
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

  // Error state: fail silently — don't crash the parent card
  if (isError) return null;

  // Loading state
  if (isLoading) return <DispatchSkeleton />;

  // No dispatch data (manual mode or not started)
  if (!data || data.dispatch_mode === 'manual') return null;

  // Matched state
  if (data.matched) {
    return <MatchedView records={data.records} />;
  }

  // Dispatching in progress
  return <DispatchingView data={data} />;
}
