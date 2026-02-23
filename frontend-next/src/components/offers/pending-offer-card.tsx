'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import api, { APIError } from '@/lib/api-client';
import type { OfferResponse } from '@/lib/api-types';
import { formatCurrency, formatDate } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface PendingOfferCardProps {
  offer: OfferResponse;
  onAction: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function PendingOfferCard({ offer, onAction }: PendingOfferCardProps) {
  const queryClient = useQueryClient();

  // ---- Accept mutation ----------------------------------------------------
  const acceptMutation = useMutation({
    mutationFn: () => api.offers.accept(offer.id),
    onSuccess: () => {
      toast.success('오퍼를 수락했습니다.');
      void queryClient.invalidateQueries({ queryKey: ['my-offers'] });
      void queryClient.invalidateQueries({ queryKey: ['my-contracts'] });
      onAction();
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(`수락 실패: ${error.message}`);
      } else {
        toast.error('오퍼 수락 중 오류가 발생했습니다.');
      }
    },
  });

  // ---- Reject mutation ----------------------------------------------------
  const rejectMutation = useMutation({
    mutationFn: () => api.offers.reject(offer.id),
    onSuccess: () => {
      toast.success('오퍼를 거절했습니다.');
      void queryClient.invalidateQueries({ queryKey: ['my-offers'] });
      onAction();
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(`거절 실패: ${error.message}`);
      } else {
        toast.error('오퍼 거절 중 오류가 발생했습니다.');
      }
    },
  });

  const isLoading = acceptMutation.isPending || rejectMutation.isPending;

  return (
    <Card className="flex flex-col justify-between transition-shadow hover:shadow-md">
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

        {/* Message */}
        {offer.message && (
          <p className="text-sm text-muted-foreground rounded-md bg-muted p-3">
            {offer.message}
          </p>
        )}

        {/* Expiry info */}
        {offer.expires_at && (
          <p className="text-xs text-muted-foreground">
            만료일: {formatDate(offer.expires_at)}
          </p>
        )}
      </CardContent>

      {/* Action buttons */}
      <div className="flex gap-2 px-6 pb-6">
        <Button
          variant="default"
          size="sm"
          className="min-h-[44px] flex-1"
          disabled={isLoading}
          onClick={() => acceptMutation.mutate()}
          aria-label="오퍼 수락"
        >
          {acceptMutation.isPending ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            '수락'
          )}
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="min-h-[44px] flex-1"
          disabled={isLoading}
          onClick={() => rejectMutation.mutate()}
          aria-label="오퍼 거절"
        >
          {rejectMutation.isPending ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            '거절'
          )}
        </Button>
      </div>
    </Card>
  );
}
