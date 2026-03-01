'use client';

import type { TierResponse } from '@/lib/api-types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TierBadge } from './tier-badge';

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
