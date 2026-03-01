'use client';

import { useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { Clock, Loader2 } from 'lucide-react';
import api from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PendingOfferCard } from './pending-offer-card';
import { AcceptedOfferCard } from './accepted-offer-card';
import { OfferHistoryTable } from './offer-history-table';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function OfferList() {
  const queryClient = useQueryClient();

  // ---- Queries ------------------------------------------------------------
  const offersQuery = useQuery({
    queryKey: ['my-offers'],
    queryFn: () => api.offers.getMyOffers(),
  });

  const contractsQuery = useQuery({
    queryKey: ['my-contracts'],
    queryFn: () => api.contracts.getMyContracts(),
  });

  // ---- Derived data -------------------------------------------------------
  const contractOfferIds = useMemo(() => {
    const items = contractsQuery.data?.items;
    if (!items) return new Set<string>();
    return new Set(items.map((c) => c.offer_id));
  }, [contractsQuery.data]);

  const { pending, accepted, others } = useMemo(() => {
    const all = offersQuery.data?.items ?? [];

    const pendingOffers = all.filter(
      (o) => o.status === 'pending' && !contractOfferIds.has(o.id),
    );
    const acceptedOffers = all.filter(
      (o) => o.status === 'accepted' && !contractOfferIds.has(o.id),
    );
    const otherOffers = all.filter(
      (o) =>
        (o.status !== 'pending' && o.status !== 'accepted') ||
        contractOfferIds.has(o.id),
    );

    return {
      pending: pendingOffers,
      accepted: acceptedOffers,
      others: otherOffers,
    };
  }, [offersQuery.data, contractOfferIds]);

  // ---- Handlers -----------------------------------------------------------
  function handleAction() {
    void queryClient.invalidateQueries({ queryKey: ['my-offers'] });
    void queryClient.invalidateQueries({ queryKey: ['my-contracts'] });
  }

  // ---- Render: loading state ----------------------------------------------
  if (offersQuery.isLoading || contractsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-20" role="status">
        <Loader2 className="mr-2 size-6 animate-spin" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">
          오퍼를 불러오는 중...
        </span>
      </div>
    );
  }

  // ---- Render: error state ------------------------------------------------
  if (offersQuery.isError || contractsQuery.isError) {
    return (
      <div
        className="flex flex-col items-center justify-center gap-3 py-20"
        role="alert"
      >
        <p className="text-sm text-destructive">
          오퍼를 불러오는 데 실패했습니다.
        </p>
        <Button
          variant="outline"
          size="sm"
          className="min-h-[44px]"
          onClick={() => {
            void offersQuery.refetch();
            void contractsQuery.refetch();
          }}
        >
          다시 시도
        </Button>
      </div>
    );
  }

  // ---- Render -------------------------------------------------------------
  return (
    <Tabs defaultValue="pending" className="flex flex-col gap-4">
      <TabsList className="w-full">
        <TabsTrigger value="pending" className="min-h-[44px]">
          대기 중 ({pending.length})
        </TabsTrigger>
        <TabsTrigger value="accepted" className="min-h-[44px]">
          수락됨 ({accepted.length})
        </TabsTrigger>
        <TabsTrigger value="history" className="min-h-[44px]">
          처리 내역 ({others.length})
        </TabsTrigger>
      </TabsList>

      {/* Pending tab */}
      <TabsContent value="pending">
        {pending.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16">
            <div className="flex size-14 items-center justify-center rounded-full bg-muted">
              <Clock className="size-6 text-muted-foreground" aria-hidden="true" />
            </div>
            <p className="text-sm font-medium">아직 수락된 매칭이 없습니다</p>
            <p className="text-center text-xs text-muted-foreground max-w-[260px]">
              더 많은 공고에 지원할수록 매칭 확률이 높아집니다. 긴급 공고는 보통 30분 내에 결정됩니다.
            </p>
            <Button variant="default" size="sm" className="mt-1 min-h-[44px]" asChild>
              <Link href="/steps/jobs">공고 더 찾아보기</Link>
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {pending.map((offer) => (
              <PendingOfferCard
                key={offer.id}
                offer={offer}
                onAction={handleAction}
              />
            ))}
          </div>
        )}
      </TabsContent>

      {/* Accepted tab */}
      <TabsContent value="accepted">
        {accepted.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-16">
            <p className="text-sm text-muted-foreground">수락된 매칭이 없습니다</p>
            <p className="text-xs text-muted-foreground">
              스튜디오가 지원을 수락하면 여기에 표시됩니다
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {accepted.map((offer) => (
              <AcceptedOfferCard
                key={offer.id}
                offer={offer}
                onAction={handleAction}
              />
            ))}
          </div>
        )}
      </TabsContent>

      {/* History tab */}
      <TabsContent value="history">
        <OfferHistoryTable
          offers={others}
          contractOfferIds={contractOfferIds}
        />
      </TabsContent>
    </Tabs>
  );
}
