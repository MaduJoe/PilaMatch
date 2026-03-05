'use client';

import type { TierResponse } from '@/lib/api-types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';
import { HelpCircle } from 'lucide-react';
import { TierBadge } from './tier-badge';

const TIER_BENEFITS = [
  { tier: 'Basic', daily: '하루 2회', region: '내 위치 + 1개 지역', urgent: '긴급 1건' },
  { tier: 'Verified', daily: '하루 3회', region: '내 위치 + 2개 지역', urgent: '긴급 2건' },
  { tier: 'Pro', daily: '무제한', region: '모든 지역', urgent: '긴급 무제한' },
];

interface TierCardProps {
  data: TierResponse;
}

export function TierCard({ data }: TierCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <CardTitle className="text-lg">내 등급</CardTitle>
          <TierBadge tier={data.tier} label={data.tier_label} size="md" />
          <Popover>
            <PopoverTrigger asChild>
              <button className="text-muted-foreground hover:text-foreground" aria-label="등급별 혜택 보기">
                <HelpCircle className="size-4" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-72 p-3" side="bottom" align="start">
              <p className="text-xs font-semibold mb-2.5">등급별 혜택</p>
              <div className="space-y-3">
                {TIER_BENEFITS.map((b) => (
                  <div key={b.tier} className="space-y-1">
                    <p className="text-xs font-semibold">{b.tier}</p>
                    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 text-[11px] text-muted-foreground">
                      <span>지원</span><span>{b.daily}</span>
                      <span>지역</span><span>{b.region}</span>
                      <span>긴급</span><span>{b.urgent}</span>
                    </div>
                  </div>
                ))}
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-muted-foreground">최근 30일 완료</div>
          <div className="font-medium">{data.completed_jobs_recent}건</div>
          <div className="text-muted-foreground">노쇼</div>
          <div className="font-medium">{data.no_show_recent}회</div>
          {data.same_day_cancel_recent > 0 && (
            <>
              <div className="text-muted-foreground">당일취소</div>
              <div className="font-medium text-red-600">{data.same_day_cancel_recent}회</div>
            </>
          )}
          {data.late_recent > 0 && (
            <>
              <div className="text-muted-foreground">지각</div>
              <div className="font-medium text-orange-600">{data.late_recent}회</div>
            </>
          )}
        </div>

        {/* Next tier */}
        {data.next_tier && data.missing_requirements.length > 0 && (
          <div className="mt-2 rounded-lg bg-muted/50 p-3">
            <p className="text-sm font-medium mb-1">
              다음 등급까지
            </p>
            <ul className="text-sm text-muted-foreground space-y-1">
              {data.missing_requirements.map((req, i) => (
                <li key={i}>- {req}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
