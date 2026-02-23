'use client';

import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Pencil, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import api, { APIError } from '@/lib/api-client';
import type { ContractResponse, ReviewResponse } from '@/lib/api-types';
import { useAuthStore } from '@/stores/auth-store';
import { formatDate } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
import { WriteReviewDialog } from './write-review-dialog';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function WrittenReviewsTab() {
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const userRole = user?.role ?? 'instructor';

  // ---- State ---------------------------------------------------------------
  const [selectedContractId, setSelectedContractId] = useState<string>('');
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editReview, setEditReview] = useState<ReviewResponse | null>(null);
  const [writeDialogOpen, setWriteDialogOpen] = useState(false);
  const [writeContractId, setWriteContractId] = useState<string | null>(null);
  const [writePartnerName, setWritePartnerName] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // ---- Inline review form state -------------------------------------------
  const [inlineRating, setInlineRating] = useState<number>(0);
  const [inlineComment, setInlineComment] = useState<string>('');

  // ---- Queries -------------------------------------------------------------
  const contractsQuery = useQuery({
    queryKey: ['my-contracts'],
    queryFn: () => api.contracts.getMyContracts(),
  });

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
      setDeleteConfirmId(null);
      setSelectedContractId('');
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

  const inlineCreateMutation = useMutation({
    mutationFn: (contractId: string) =>
      api.reviews.create(contractId, {
        rating: inlineRating,
        comment: inlineComment.trim() || undefined,
      }),
    onSuccess: () => {
      toast.success('리뷰가 작성되었습니다.');
      void queryClient.invalidateQueries({ queryKey: ['written-reviews'] });
      void queryClient.invalidateQueries({ queryKey: ['received-reviews'] });
      setInlineRating(0);
      setInlineComment('');
      setSelectedContractId('');
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(`리뷰 작성 실패: ${error.message}`);
      } else {
        toast.error('리뷰 작성 중 오류가 발생했습니다.');
      }
    },
  });

  // ---- Derived data --------------------------------------------------------
  const { completedContracts, reviewMap, writtenCount, unwrittenCount } =
    useMemo(() => {
      const allContracts = contractsQuery.data?.items ?? [];
      const done = allContracts.filter((c) => c.status === 'completed');
      const reviews = writtenQuery.data?.items ?? [];

      const map = new Map<string, ReviewResponse>();
      for (const r of reviews) {
        map.set(r.contract_id, r);
      }

      const written = done.filter((c) => map.has(c.id)).length;
      const unwritten = done.length - written;

      return {
        completedContracts: done,
        reviewMap: map,
        writtenCount: written,
        unwrittenCount: unwritten,
      };
    }, [contractsQuery.data, writtenQuery.data]);

  const selectedContract = completedContracts.find(
    (c) => c.id === selectedContractId,
  );
  const selectedReview = selectedContractId
    ? reviewMap.get(selectedContractId) ?? null
    : null;

  // ---- Helpers -------------------------------------------------------------
  function getPartnerName(contract: ContractResponse): string {
    return userRole === 'studio'
      ? contract.instructor_name ?? '강사'
      : contract.studio_name ?? '스튜디오';
  }

  function handleDeleteClick(reviewId: string) {
    if (deleteConfirmId === reviewId) {
      deleteMutation.mutate(reviewId);
    } else {
      setDeleteConfirmId(reviewId);
    }
  }

  // ---- Render: loading state -----------------------------------------------
  if (contractsQuery.isLoading || writtenQuery.isLoading) {
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
  if (contractsQuery.isError || writtenQuery.isError) {
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
          onClick={() => {
            void contractsQuery.refetch();
            void writtenQuery.refetch();
          }}
        >
          다시 시도
        </Button>
      </div>
    );
  }

  // ---- Render: empty state -------------------------------------------------
  if (completedContracts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-20">
        <p className="text-sm text-muted-foreground">
          아직 완료된 수업이 없어 리뷰를 작성할 수 없습니다.
        </p>
      </div>
    );
  }

  // ---- Render --------------------------------------------------------------
  return (
    <div className="flex flex-col gap-6">
      {/* Metrics */}
      <div className="flex gap-3">
        <Card className="flex-1">
          <CardContent className="flex flex-col items-center gap-1 py-4">
            <p className="text-xs text-muted-foreground">작성 완료</p>
            <p className="text-lg font-bold">{writtenCount}건</p>
          </CardContent>
        </Card>
        <Card className="flex-1">
          <CardContent className="flex flex-col items-center gap-1 py-4">
            <p className="text-xs text-muted-foreground">미작성</p>
            <p className="text-lg font-bold text-destructive">
              {unwrittenCount}건
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Contract table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>상태</TableHead>
              <TableHead>상대방</TableHead>
              <TableHead>날짜</TableHead>
              <TableHead>평점</TableHead>
              <TableHead className="hidden sm:table-cell">리뷰</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {completedContracts.map((contract) => {
              const review = reviewMap.get(contract.id);
              const hasReview = !!review;
              return (
                <TableRow
                  key={contract.id}
                  className="cursor-pointer"
                  onClick={() => setSelectedContractId(contract.id)}
                  data-state={
                    selectedContractId === contract.id ? 'selected' : undefined
                  }
                >
                  <TableCell>
                    <Badge
                      variant={hasReview ? 'default' : 'outline'}
                      className="text-xs"
                    >
                      {hasReview ? '작성' : '미작성'}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-medium">
                    {getPartnerName(contract)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDate(contract.date)}
                  </TableCell>
                  <TableCell>
                    {hasReview ? (
                      <StarRating
                        value={review.rating}
                        readonly
                        size="sm"
                      />
                    ) : (
                      <span className="text-sm text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell className="hidden max-w-[200px] truncate sm:table-cell">
                    {hasReview && review.comment ? (
                      <span className="text-sm text-muted-foreground">
                        {review.comment}
                      </span>
                    ) : (
                      <span className="text-sm text-muted-foreground">-</span>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* Contract selector for mobile */}
      <div className="sm:hidden">
        <Select
          value={selectedContractId}
          onValueChange={setSelectedContractId}
        >
          <SelectTrigger className="min-h-[44px] w-full" aria-label="계약 선택">
            <SelectValue placeholder="리뷰할 수업을 선택하세요" />
          </SelectTrigger>
          <SelectContent>
            {completedContracts.map((contract) => {
              const hasReview = reviewMap.has(contract.id);
              return (
                <SelectItem key={contract.id} value={contract.id}>
                  {hasReview ? '[작성] ' : '[미작성] '}
                  {getPartnerName(contract)} - {formatDate(contract.date)}
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
      </div>

      {/* Detail section */}
      {selectedContract && (
        <Card>
          <CardContent className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">{getPartnerName(selectedContract)}</p>
                <p className="text-sm text-muted-foreground">
                  {formatDate(selectedContract.date)}
                </p>
              </div>
              <Badge variant={selectedReview ? 'default' : 'outline'}>
                {selectedReview ? '작성 완료' : '미작성'}
              </Badge>
            </div>

            {selectedReview ? (
              /* Existing review: show + edit/delete buttons */
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
            ) : (
              /* No review: inline form */
              <div className="flex flex-col gap-3">
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium">평점</label>
                  <StarRating
                    value={inlineRating}
                    onChange={setInlineRating}
                    size="lg"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label
                    htmlFor="inline-review-comment"
                    className="text-sm font-medium"
                  >
                    리뷰 내용 (선택사항)
                  </label>
                  <Textarea
                    id="inline-review-comment"
                    placeholder="수업은 어떠셨나요?"
                    value={inlineComment}
                    onChange={(e) => setInlineComment(e.target.value)}
                    rows={3}
                    maxLength={500}
                    aria-label="리뷰 내용"
                  />
                </div>
                <Button
                  className="min-h-[44px]"
                  onClick={() =>
                    inlineCreateMutation.mutate(selectedContractId)
                  }
                  disabled={
                    inlineCreateMutation.isPending || inlineRating === 0
                  }
                  aria-label="리뷰 작성"
                >
                  {inlineCreateMutation.isPending ? (
                    <Loader2
                      className="size-4 animate-spin"
                      aria-hidden="true"
                    />
                  ) : (
                    '리뷰 작성'
                  )}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Dialogs */}
      <EditReviewDialog
        review={editReview}
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        onSuccess={() => {
          void queryClient.invalidateQueries({ queryKey: ['written-reviews'] });
          setSelectedContractId('');
        }}
      />

      <WriteReviewDialog
        contractId={writeContractId}
        partnerName={writePartnerName}
        open={writeDialogOpen}
        onOpenChange={setWriteDialogOpen}
        onSuccess={() => {
          void queryClient.invalidateQueries({ queryKey: ['written-reviews'] });
        }}
      />
    </div>
  );
}
