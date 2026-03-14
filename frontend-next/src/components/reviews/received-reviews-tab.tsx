'use client';

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';
import api from '@/lib/api-client';
import { formatDate } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { StarRating } from './star-rating';

// ---------------------------------------------------------------------------
// Quality badge helper
// ---------------------------------------------------------------------------

function getQualityBadge(avg: number): { label: string; variant: 'default' | 'secondary' | 'outline' | 'destructive' } {
  if (avg >= 4.5) return { label: '우수', variant: 'default' };
  if (avg >= 3.5) return { label: '양호', variant: 'secondary' };
  if (avg >= 2.5) return { label: '보통', variant: 'outline' };
  return { label: '개선 필요', variant: 'destructive' };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ReceivedReviewsTab() {
  // ---- Query ---------------------------------------------------------------
  const receivedQuery = useQuery({
    queryKey: ['received-reviews'],
    queryFn: () => api.reviews.getReceived(),
  });

  // ---- Derived data --------------------------------------------------------
  const { sortedItems, averageRating, totalCount } = useMemo(() => {
    const data = receivedQuery.data;
    const items = data?.items ?? [];
    const sorted = [...items].sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    return {
      sortedItems: sorted,
      averageRating: data?.average_rating ?? null,
      totalCount: data?.total ?? 0,
    };
  }, [receivedQuery.data]);

  const qualityBadge =
    averageRating !== null ? getQualityBadge(averageRating) : null;

  // ---- Render: loading state -----------------------------------------------
  if (receivedQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-20" role="status">
        <Loader2 className="mr-2 size-6 animate-spin" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">
          리뷰를 불러오는 중...
        </span>
      </div>
    );
  }

  // ---- Render: error state -------------------------------------------------
  if (receivedQuery.isError) {
    return (
      <div
        className="flex flex-col items-center justify-center gap-3 py-20"
        role="alert"
      >
        <p className="text-sm text-destructive">
          리뷰를 불러오는 데 실패했습니다.
        </p>
        <Button
          variant="outline"
          size="sm"
          className="min-h-[44px]"
          onClick={() => void receivedQuery.refetch()}
        >
          다시 시도
        </Button>
      </div>
    );
  }

  // ---- Render: empty state -------------------------------------------------
  if (sortedItems.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-20">
        <p className="text-sm text-muted-foreground">
          아직 받은 리뷰가 없습니다.
        </p>
        <p className="text-xs text-muted-foreground">
          수업을 완료하면 상대방이 리뷰를 남길 수 있습니다.
        </p>
      </div>
    );
  }

  // ---- Render --------------------------------------------------------------
  return (
    <div className="flex flex-col gap-8">
      {/* Average rating summary */}
      <Card>
        <CardContent className="flex flex-col items-center gap-3 py-6">
          {averageRating !== null && (
            <>
              <p className="text-4xl font-bold">
                {averageRating.toFixed(1)}
              </p>
              <StarRating value={Math.round(averageRating)} readonly size="lg" />
              {qualityBadge && (
                <Badge variant={qualityBadge.variant} className="text-sm">
                  {qualityBadge.label}
                </Badge>
              )}
            </>
          )}
          <p className="text-sm text-muted-foreground">
            총 {totalCount}개의 리뷰
          </p>
        </CardContent>
      </Card>

      {/* Reviews table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>날짜</TableHead>
              <TableHead>작성자</TableHead>
              <TableHead>평점</TableHead>
              <TableHead className="hidden sm:table-cell">리뷰 내용</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedItems.map((review) => (
              <TableRow key={review.id}>
                <TableCell className="text-sm text-muted-foreground">
                  {formatDate(review.created_at)}
                </TableCell>
                <TableCell className="font-medium">
                  {review.reviewer_name ?? '익명'}
                </TableCell>
                <TableCell>
                  <StarRating value={review.rating} readonly size="sm" />
                </TableCell>
                <TableCell className="hidden max-w-[300px] sm:table-cell">
                  {review.comment ? (
                    <p className="truncate text-sm text-muted-foreground">
                      {review.comment}
                    </p>
                  ) : (
                    <span className="text-sm text-muted-foreground">-</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile review cards (for content hidden in table) */}
      <div className="flex flex-col gap-3 sm:hidden">
        {sortedItems
          .filter((r) => r.comment)
          .map((review) => (
            <Card key={`mobile-${review.id}`}>
              <CardContent className="flex flex-col gap-2 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">
                    {review.reviewer_name ?? '익명'}
                  </span>
                  <StarRating value={review.rating} readonly size="sm" />
                </div>
                <p className="text-sm text-muted-foreground">
                  {review.comment}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatDate(review.created_at)}
                </p>
              </CardContent>
            </Card>
          ))}
      </div>
    </div>
  );
}
