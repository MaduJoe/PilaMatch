'use client';

import { useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { Loader2 } from 'lucide-react';
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
          <div className="flex flex-col items-center justify-center gap-4 py-20">
            <p className="text-sm text-muted-foreground">
              아직 받은 오퍼가 없습니다
            </p>
            <Button variant="outline" size="sm" className="min-h-[44px]" asChild>
              <Link href="/steps/jobs">일 찾기로 돌아가기</Link>
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
          <div className="flex flex-col items-center justify-center gap-2 py-20">
            <p className="text-sm text-muted-foreground">
              수락된 오퍼가 없습니다
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
