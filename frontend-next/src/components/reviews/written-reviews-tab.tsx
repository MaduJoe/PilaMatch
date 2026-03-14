'use client';

import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Pencil, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import api, { APIError } from '@/lib/api-client';
import type { ReviewResponse } from '@/lib/api-types';
import { useAuthStore } from '@/stores/auth-store';
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
import { EditReviewDialog } from './edit-review-dialog';
import { CHECKLIST_LABELS_SHORT } from './review-constants';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function WrittenReviewsTab() {
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const userRole: 'instructor' | 'studio' = user?.role === 'studio' ? 'studio' : 'instructor';

  // ---- State ---------------------------------------------------------------
  const [selectedReviewId, setSelectedReviewId] = useState<string>('');
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editReview, setEditReview] = useState<ReviewResponse | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // ---- Query ---------------------------------------------------------------
  const writtenQuery = useQuery({
    queryKey: ['written-reviews'],
    queryFn: () => api.reviews.getWritten(),
  });

  // ---- Mutations -----------------------------------------------------------
  const deleteMutation = useMutation({
    mutationFn: (reviewId: string) => api.reviews.delete(reviewId),
    onSuccess: () => {
      toast.success('리뷰가 삭제되었습니다.');
      void queryClient.invalidateQueries({ queryKey: ['written-reviews'] });
      void queryClient.invalidateQueries({ queryKey: ['received-reviews'] });
      void queryClient.invalidateQueries({ queryKey: ['review-eligibility'] });
      setDeleteConfirmId(null);
      setSelectedReviewId('');
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(`삭제 실패: ${error.message}`);
      } else {
        toast.error('리뷰 삭제 중 오류가 발생했습니다.');
      }
      setDeleteConfirmId(null);
    },
  });

  // ---- Derived data --------------------------------------------------------
  const reviews = writtenQuery.data?.items ?? [];
  const selectedReview = useMemo(
    () => reviews.find((r) => r.id === selectedReviewId) ?? null,
    [reviews, selectedReviewId],
  );

  // ---- Helpers -------------------------------------------------------------
  function getPartnerName(review: ReviewResponse): string {
    return review.reviewee_name ?? (userRole === 'studio' ? '강사' : '스튜디오');
  }

  function handleDeleteClick(reviewId: string) {
    if (deleteConfirmId === reviewId) {
      deleteMutation.mutate(reviewId);
    } else {
      setDeleteConfirmId(reviewId);
    }
  }

  // ---- Render: loading state -----------------------------------------------
  if (writtenQuery.isLoading) {
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
  if (writtenQuery.isError) {
    return (
      <div
        className="flex flex-col items-center justify-center gap-3 py-20"
        role="alert"
      >
        <p className="text-sm text-destructive">
          데이터를 불러오는 데 실패했습니다.
        </p>
        <Button
          variant="outline"
          size="sm"
          className="min-h-[44px]"
          onClick={() => void writtenQuery.refetch()}
        >
          다시 시도
        </Button>
      </div>
    );
  }

  // ---- Render: empty state -------------------------------------------------
  if (reviews.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-20">
        <p className="text-sm text-muted-foreground">
          작성한 리뷰가 없습니다.
        </p>
      </div>
    );
  }

  // ---- Render --------------------------------------------------------------
  return (
    <div className="flex flex-col gap-8">
      {/* Metrics */}
      <Card>
        <CardContent className="flex flex-col items-center gap-1 py-4">
          <p className="text-xs text-muted-foreground">작성한 리뷰</p>
          <p className="text-lg font-bold">{reviews.length}건</p>
        </CardContent>
      </Card>

      {/* Review table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>상대방</TableHead>
              <TableHead>수업 날짜</TableHead>
              <TableHead>평점</TableHead>
              <TableHead className="hidden sm:table-cell">리뷰</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reviews.map((review) => (
              <TableRow
                key={review.id}
                className="cursor-pointer"
                onClick={() => setSelectedReviewId(review.id)}
                data-state={
                  selectedReviewId === review.id ? 'selected' : undefined
                }
              >
                <TableCell className="font-medium">
                  {getPartnerName(review)}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {review.job_date ? formatDate(review.job_date) : formatDate(review.created_at)}
                </TableCell>
                <TableCell>
                  <StarRating value={review.rating} readonly size="sm" />
                </TableCell>
                <TableCell className="hidden max-w-[200px] truncate sm:table-cell">
                  {review.comment ? (
                    <span className="text-sm text-muted-foreground">
                      {review.comment}
                    </span>
                  ) : (
                    <span className="text-sm text-muted-foreground">-</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Detail section */}
      {selectedReview && (
        <Card>
          <CardContent className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">{getPartnerName(selectedReview)}</p>
                <p className="text-sm text-muted-foreground">
                  {selectedReview.job_date
                    ? formatDate(selectedReview.job_date)
                    : formatDate(selectedReview.created_at)}
                </p>
              </div>
              <Badge variant="default">작성 완료</Badge>
            </div>

            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <StarRating
                  value={selectedReview.rating}
                  readonly
                  size="md"
                />
                <span className="text-sm text-muted-foreground">
                  ({selectedReview.rating}점)
                </span>
              </div>

              {/* Checklist display */}
              {(selectedReview.time_punctuality != null ||
                selectedReview.professionalism != null ||
                selectedReview.would_rehire != null) && (
                <div className="flex gap-2 flex-wrap">
                  {selectedReview.time_punctuality != null && (
                    <Badge variant={selectedReview.time_punctuality ? 'default' : 'outline'} className="text-xs">
                      {CHECKLIST_LABELS_SHORT[userRole].timePunctuality} {selectedReview.time_punctuality ? 'O' : 'X'}
                    </Badge>
                  )}
                  {selectedReview.professionalism != null && (
                    <Badge variant={selectedReview.professionalism ? 'default' : 'outline'} className="text-xs">
                      {CHECKLIST_LABELS_SHORT[userRole].professionalism} {selectedReview.professionalism ? 'O' : 'X'}
                    </Badge>
                  )}
                  {selectedReview.would_rehire != null && (
                    <Badge variant={selectedReview.would_rehire ? 'default' : 'outline'} className="text-xs">
                      {CHECKLIST_LABELS_SHORT[userRole].wouldRehire} {selectedReview.would_rehire ? 'O' : 'X'}
                    </Badge>
                  )}
                </div>
              )}

              {selectedReview.comment && (
                <p className="rounded-md bg-muted p-3 text-sm">
                  {selectedReview.comment}
                </p>
              )}

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="min-h-[44px] gap-1"
                  onClick={() => {
                    setEditReview(selectedReview);
                    setEditDialogOpen(true);
                  }}
                  aria-label="리뷰 수정"
                >
                  <Pencil className="size-4" aria-hidden="true" />
                  수정
                </Button>
                <Button
                  variant={
                    deleteConfirmId === selectedReview.id
                      ? 'destructive'
                      : 'outline'
                  }
                  size="sm"
                  className="min-h-[44px] gap-1"
                  onClick={() => handleDeleteClick(selectedReview.id)}
                  disabled={deleteMutation.isPending}
                  aria-label={
                    deleteConfirmId === selectedReview.id
                      ? '삭제 확인'
                      : '리뷰 삭제'
                  }
                >
                  {deleteMutation.isPending ? (
                    <Loader2
                      className="size-4 animate-spin"
                      aria-hidden="true"
                    />
                  ) : (
                    <Trash2 className="size-4" aria-hidden="true" />
                  )}
                  {deleteConfirmId === selectedReview.id
                    ? '정말 삭제하시겠습니까?'
                    : '삭제'}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Edit dialog */}
      <EditReviewDialog
        review={editReview}
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        onSuccess={() => {
          void queryClient.invalidateQueries({ queryKey: ['written-reviews'] });
          void queryClient.invalidateQueries({ queryKey: ['review-eligibility'] });
          setSelectedReviewId('');
        }}
      />
    </div>
  );
}
