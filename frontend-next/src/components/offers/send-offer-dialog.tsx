'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Loader2, Send } from 'lucide-react';
import api, { APIError } from '@/lib/api-client';
import type { ApplicationWithInstructorResponse } from '@/lib/api-types';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface SendOfferDialogProps {
  application: ApplicationWithInstructorResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SendOfferDialog({
  application,
  open,
  onOpenChange,
  onSuccess,
}: SendOfferDialogProps) {
  const [proposedRate, setProposedRate] = useState(50000);
  const [message, setMessage] = useState('');

  const instructorName = application?.instructor_name ?? '강사';

  const createOfferMutation = useMutation({
    mutationFn: () => {
      if (!application) throw new Error('No application selected');
      return api.offers.create({
        application_id: application.id,
        proposed_rate: proposedRate,
        message: message || undefined,
      });
    },
    onSuccess: () => {
      toast.success(`${instructorName} 강사에게 오퍼를 전송했습니다!`);
      // Reset form
      setProposedRate(50000);
      setMessage('');
      onOpenChange(false);
      onSuccess();
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(`오류: ${error.message}`);
      } else {
        toast.error('오퍼 전송 중 오류가 발생했습니다.');
      }
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    createOfferMutation.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>오퍼 보내기</DialogTitle>
            <DialogDescription>
              <strong>{instructorName}</strong> 강사에게 오퍼를 보냅니다.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4 py-4">
            {/* Proposed rate */}
            <div className="flex flex-col gap-2">
              <Label htmlFor="proposed-rate">제안 시급 (원)</Label>
              <Input
                id="proposed-rate"
                type="number"
                min={0}
                step={5000}
                value={proposedRate}
                onChange={(e) => setProposedRate(Number(e.target.value))}
                className="min-h-[44px]"
                required
                aria-label="제안 시급"
              />
            </div>

            {/* Message */}
            <div className="flex flex-col gap-2">
              <Label htmlFor="offer-message">메시지 (선택)</Label>
              <Textarea
                id="offer-message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="근무 조건을 자유롭게 작성하세요."
                rows={3}
                aria-label="오퍼 메시지"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              className="min-h-[44px]"
              onClick={() => onOpenChange(false)}
              disabled={createOfferMutation.isPending}
            >
              취소
            </Button>
            <Button
              type="submit"
              className="min-h-[44px]"
              disabled={createOfferMutation.isPending || proposedRate <= 0}
            >
              {createOfferMutation.isPending ? (
                <>
                  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                  전송 중...
                </>
              ) : (
                <>
                  <Send className="size-4" aria-hidden="true" />
                  오퍼 전송
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
