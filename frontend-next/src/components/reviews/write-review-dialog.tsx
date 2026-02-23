'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import api, { APIError } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { StarRating } from './star-rating';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface WriteReviewDialogProps {
  contractId: string | null;
  partnerName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function WriteReviewDialog({
  contractId,
  partnerName,
  open,
  onOpenChange,
  onSuccess,
}: WriteReviewDialogProps) {
  const queryClient = useQueryClient();
  const [rating, setRating] = useState<number>(0);
  const [comment, setComment] = useState<string>('');

  // ---- Mutation ------------------------------------------------------------
  const createMutation = useMutation({
    mutationFn: () => {
      if (!contractId) throw new Error('계약 ID가 없습니다.');
      return api.reviews.create(contractId, {
        rating,
        comment: comment.trim() || undefined,
      });
    },
    onSuccess: () => {
      toast.success('리뷰가 작성되었습니다.');
      void queryClient.invalidateQueries({ queryKey: ['my-contracts'] });
      void queryClient.invalidateQueries({ queryKey: ['written-reviews'] });
      void queryClient.invalidateQueries({ queryKey: ['received-reviews'] });
      setRating(0);
      setComment('');
      onOpenChange(false);
      onSuccess();
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(`리뷰 작성 실패: ${error.message}`);
      } else {
        toast.error('리뷰 작성 중 오류가 발생했습니다.');
      }
    },
  });

  // ---- Handlers ------------------------------------------------------------
  function handleSubmit() {
    if (rating === 0) {
      toast.error('별점을 선택해주세요.');
      return;
    }
    createMutation.mutate();
  }

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) {
      setRating(0);
      setComment('');
    }
    onOpenChange(nextOpen);
  }

  // ---- Render --------------------------------------------------------------
  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>리뷰 작성</DialogTitle>
          <DialogDescription>
            {partnerName}님에 대한 리뷰를 작성해주세요.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-2">
          {/* Star rating */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium">
              평점 <span className="text-destructive">*</span>
            </label>
            <StarRating value={rating} onChange={setRating} size="lg" />
            {rating > 0 && (
              <p className="text-sm text-muted-foreground">
                {rating}점을 선택했습니다
              </p>
            )}
          </div>

          {/* Comment */}
          <div className="flex flex-col gap-2">
            <label htmlFor="review-comment" className="text-sm font-medium">
              리뷰 내용 (선택사항)
            </label>
            <Textarea
              id="review-comment"
              placeholder="수업은 어떠셨나요? 경험을 공유해주세요."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={4}
              maxLength={500}
              aria-label="리뷰 내용"
            />
            <p className="text-xs text-muted-foreground text-right">
              {comment.length}/500
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            className="min-h-[44px]"
            onClick={() => handleOpenChange(false)}
            disabled={createMutation.isPending}
          >
            취소
          </Button>
          <Button
            className="min-h-[44px]"
            onClick={handleSubmit}
            disabled={createMutation.isPending || rating === 0}
            aria-label="리뷰 작성"
          >
            {createMutation.isPending ? (
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            ) : (
              '리뷰 작성'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
