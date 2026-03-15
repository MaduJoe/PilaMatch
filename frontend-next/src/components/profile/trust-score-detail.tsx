'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api-client';
import { TierCard } from '@/components/trust/tier-card';
import { Card, CardContent } from '@/components/ui/card';

/**
 * TrustScoreDetail -- now wraps the new TierCard component.
 * Kept as a named export so existing imports don't break.
 */
export function TrustScoreDetail() {
  const { data: tierData, isLoading } = useQuery({
    queryKey: ['my-tier'],
    queryFn: () => api.tier.getMyTier(),
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </CardContent>
      </Card>
    );
  }

  if (!tierData) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-sm text-muted-foreground">
          등급 정보를 불러올 수 없습니다
        </CardContent>
      </Card>
    );
  }

  return <TierCard data={tierData} />;
}
