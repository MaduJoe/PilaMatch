'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ChevronDown, ChevronUp, Lock, FileText } from 'lucide-react';
import api from '@/lib/api-client';
import { handoffNoteSchema, type HandoffNoteFormData } from '@/lib/validators';
import { ATMOSPHERE_OPTIONS } from '@/lib/constants';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface HandoffNoteFormProps {
  jobPostId: string;
  isUrgentSubstitute?: boolean;
}

export function HandoffNoteForm({ jobPostId, isUrgentSubstitute }: HandoffNoteFormProps) {
  const [expanded, setExpanded] = useState(isUrgentSubstitute ?? false);
  const queryClient = useQueryClient();

  const noteQuery = useQuery({
    queryKey: ['handoff-note', jobPostId],
    queryFn: () => api.handoffNotes.get(jobPostId),
    enabled: !!jobPostId && expanded,
    retry: false,
  });

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isDirty },
  } = useForm<HandoffNoteFormData>({
    resolver: zodResolver(handoffNoteSchema) as any,
    values: noteQuery.data ? {
      class_topic: noteQuery.data.class_topic ?? '',
      class_sequence_info: noteQuery.data.class_sequence_info ?? '',
      atmosphere_preference: noteQuery.data.atmosphere_preference ?? '',
      additional_notes: noteQuery.data.additional_notes ?? '',
      member_notes: (noteQuery.data as any).member_notes ?? '',
      equipment_notes: (noteQuery.data as any).equipment_notes ?? '',
    } : undefined,
  });

  const saveMutation = useMutation({
    mutationFn: (data: HandoffNoteFormData) =>
      api.handoffNotes.upsert(jobPostId, data),
    onSuccess: () => {
      toast.success('인수인계 노트가 저장되었습니다');
      queryClient.invalidateQueries({ queryKey: ['handoff-note', jobPostId] });
    },
    onError: () => toast.error('저장 실패'),
  });

  return (
    <Card className="border-dashed">
      <CardHeader
        className="cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <CardTitle className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2">
            <FileText className="size-4" />
            인수인계 노트
          </span>
          {expanded ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
        </CardTitle>
        {!expanded && isUrgentSubstitute && (
          <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
            인수인계 노트를 남기면 회원이 눈치 못 채는 수업이 가능합니다
          </p>
        )}
      </CardHeader>

      {expanded && (
        <CardContent>
          <form onSubmit={handleSubmit((d) => saveMutation.mutate(d))} className="space-y-4">
            {/* Public fields */}
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium">수업 주제</label>
                <Input
                  placeholder="예: 허리 재활 시퀀스 3주차"
                  className="min-h-[44px]"
                  {...register('class_topic')}
                />
              </div>

              <div>
                <label className="text-sm font-medium">수업 진도 / 내용</label>
                <Textarea
                  placeholder="이전 수업에서 다룬 내용, 다음에 이어갈 내용"
                  rows={3}
                  {...register('class_sequence_info')}
                />
              </div>

              <div>
                <label className="text-sm font-medium">수업 분위기</label>
                <Select
                  value={watch('atmosphere_preference') ?? ''}
                  onValueChange={(val) => setValue('atmosphere_preference', val)}
                >
                  <SelectTrigger className="min-h-[44px]">
                    <SelectValue placeholder="분위기 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    {ATMOSPHERE_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium">기타 안내사항</label>
                <Textarea
                  placeholder="대타 강사에게 미리 알려줄 내용"
                  rows={2}
                  {...register('additional_notes')}
                />
              </div>
            </div>

            {/* Sensitive fields */}
            <div className="space-y-3 rounded-lg border border-dashed border-amber-300 bg-amber-50/50 p-4 dark:border-amber-700 dark:bg-amber-950/20">
              <p className="flex items-center gap-1.5 text-xs font-medium text-amber-700 dark:text-amber-300">
                <Lock className="size-3.5" />
                아래 정보는 수락 후에만 대타 강사에게 공개됩니다
              </p>

              <div>
                <label className="text-sm font-medium">회원 주의사항</label>
                <Textarea
                  placeholder="특정 회원 특이사항, 주의할 점"
                  rows={2}
                  {...register('member_notes')}
                />
              </div>

              <div>
                <label className="text-sm font-medium">기구 세팅</label>
                <Textarea
                  placeholder="리포머/캐딜락 세팅, 소도구 위치 등"
                  rows={2}
                  {...register('equipment_notes')}
                />
              </div>
            </div>

            <Button
              type="submit"
              size="sm"
              className="min-h-[44px] w-full"
              disabled={saveMutation.isPending || !isDirty}
            >
              {saveMutation.isPending ? '저장 중...' : '인수인계 노트 저장'}
            </Button>
          </form>
        </CardContent>
      )}
    </Card>
  );
}
