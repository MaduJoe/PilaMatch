'use client';

import type { OfferResponse } from '@/lib/api-types';
import { formatCurrency, getOfferStatusDisplay } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function statusBadgeVariant(
  status: string,
): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'accepted':
      return 'default';
    case 'rejected':
      return 'destructive';
    case 'expired':
    case 'cancelled':
      return 'outline';
    default:
      return 'secondary';
  }
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface OfferHistoryTableProps {
  offers: OfferResponse[];
  contractOfferIds: Set<string>;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function OfferHistoryTable({
  offers,
  contractOfferIds,
}: OfferHistoryTableProps) {
  if (offers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-20">
        <p className="text-sm text-muted-foreground">
          처리된 오퍼 내역이 없습니다
        </p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>상태</TableHead>
          <TableHead>시급</TableHead>
          <TableHead>계약</TableHead>
          <TableHead>메시지</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {offers.map((offer) => {
          const statusDisplay = getOfferStatusDisplay(offer.status);
          const hasContract = contractOfferIds.has(offer.id);
          const message = offer.message ?? '';
          const truncatedMessage =
            message.length > 50 ? message.slice(0, 50) + '...' : message;

          return (
            <TableRow key={offer.id}>
              <TableCell>
                <Badge variant={statusBadgeVariant(offer.status)}>
                  {statusDisplay.label}
                </Badge>
              </TableCell>
              <TableCell className="font-medium">
                {formatCurrency(offer.proposed_rate)}
              </TableCell>
              <TableCell aria-label={hasContract ? '계약 있음' : '계약 없음'}>
                {hasContract ? (
                  <span className="text-green-600 dark:text-green-400">
                    계약완료
                  </span>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </TableCell>
              <TableCell
                className="max-w-[200px] truncate text-muted-foreground"
                title={message}
              >
                {truncatedMessage || '-'}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
