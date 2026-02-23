'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import api, { APIError } from '@/lib/api-client';
import type { OfferResponse } from '@/lib/api-types';
import { formatCurrency } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface AcceptedOfferCardProps {
  offer: OfferResponse;
  onAction: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AcceptedOfferCard({ offer, onAction }: AcceptedOfferCardProps) {
  const router = useRouter();
  const queryClient = useQueryClient();

  // ---- Create contract mutation --------------------------------------------
  const createContractMutation = useMutation({
    mutationFn: () => api.contracts.createFromOffer(offer.id),
    onSuccess: () => {
      toast.success('계약이 생성되었습니다.');
      void queryClient.invalidateQueries({ queryKey: ['my-offers'] });
      void queryClient.invalidateQueries({ queryKey: ['my-contracts'] });
      onAction();
      router.push('/steps/contracts');
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        if (error.code === 'CONTRACT_EXISTS') {
          toast.warning('이미 계약이 생성된 오퍼입니다.');
        } else {
          toast.error(`계약 생성 실패: ${error.message}`);
        }
      } else {
        toast.error('계약 생성 중 오류가 발생했습니다.');
      }
    },
  });

  return (
    <Card className="flex flex-col justify-between border-green-200 bg-green-50/50 transition-shadow hover:shadow-md dark:border-green-900 dark:bg-green-950/20">
      <CardContent className="flex flex-col gap-3">
        {/* Studio + job info */}
        {(offer.studio_name || offer.job_title) && (
          <div className="flex flex-col gap-1">
            {offer.studio_name && (
              <p className="text-sm font-medium text-foreground">
                {offer.studio_name}
              </p>
            )}
            {offer.job_title && (
              <p className="text-sm text-muted-foreground">{offer.job_title}</p>
            )}
          </div>
        )}

        {/* Proposed rate */}
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-xs">
            제안 시급
          </Badge>
          <span className="text-base font-bold">
            {formatCurrency(offer.proposed_rate)} / 시간
          </span>
        </div>

        {/* Status caption */}
        <p className="text-sm font-medium text-green-700 dark:text-green-400">
          수락 완료 - 계약을 생성하세요
        </p>
      </CardContent>

      {/* Action button */}
      <div className="flex px-6 pb-6">
        <Button
          variant="default"
          size="sm"
          className="min-h-[44px] w-full"
          disabled={createContractMutation.isPending}
          onClick={() => createContractMutation.mutate()}
          aria-label="계약 생성"
        >
          {createContractMutation.isPending ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            '계약 생성'
          )}
        </Button>
      </div>
    </Card>
  );
}
