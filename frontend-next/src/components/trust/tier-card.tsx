'use client';

import type { TierResponse } from '@/lib/api-types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';
import { HelpCircle, TrendingUp } from 'lucide-react';
import { TierBadge } from './tier-badge';

const TIER_BENEFITS = [
  { tier: 'Basic', daily: '2/day', region: 'Home + 1', urgent: '1 urgent' },
  { tier: 'Verified', daily: '3/day', region: 'Home + 2', urgent: '2 urgent' },
  { tier: 'Premium', daily: 'Unlimited', region: 'All', urgent: 'Unlimited' },
];

interface TierCardProps {
  data: TierResponse;
}

export function TierCard({ data }: TierCardProps) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="font-display text-lg tracking-tight">My Tier</CardTitle>
            <TierBadge tier={data.tier} label={data.tier_label} size="md" />
          </div>
          <Popover>
            <PopoverTrigger asChild>
              <button className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Tier benefits info">
                <HelpCircle className="size-4" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-72 p-4" side="bottom" align="end">
              <p className="font-display text-xs font-semibold mb-3 tracking-wide uppercase text-muted-foreground">Tier Benefits</p>
              <div className="space-y-3">
                {TIER_BENEFITS.map((b) => (
                  <div key={b.tier} className="space-y-1">
                    <p className="font-display text-xs font-semibold">{b.tier}</p>
                    <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-[11px] text-muted-foreground">
                      <span>Apply</span><span>{b.daily}</span>
                      <span>Region</span><span>{b.region}</span>
                      <span>Urgent</span><span>{b.urgent}</span>
                    </div>
                  </div>
                ))}
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {/* Stats grid */}
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-xl bg-muted/50 p-3 text-center">
            <p className="font-display text-xl font-bold">{data.completed_jobs_recent}</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">Completed</p>
          </div>
          <div className="rounded-xl bg-muted/50 p-3 text-center">
            <p className="font-display text-xl font-bold">{data.no_show_recent}</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">No-shows</p>
          </div>
          <div className="rounded-xl bg-muted/50 p-3 text-center">
            <p className={`font-display text-xl font-bold ${data.same_day_cancel_recent > 0 ? 'text-urgent' : ''}`}>
              {data.same_day_cancel_recent + data.late_recent}
            </p>
            <p className="text-[10px] text-muted-foreground mt-0.5">Issues</p>
          </div>
        </div>

        {/* Next tier progress */}
        {data.next_tier && data.missing_requirements.length > 0 && (
          <div className="rounded-xl border border-primary/15 bg-primary/[0.03] p-4">
            <p className="flex items-center gap-1.5 text-sm font-semibold text-primary mb-2">
              <TrendingUp className="size-4" />
              Next tier
            </p>
            <ul className="text-sm text-muted-foreground space-y-1.5">
              {data.missing_requirements.map((req, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary/40" />
                  {req}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
