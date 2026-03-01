'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { UserPlus } from 'lucide-react';
import api from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';

interface BackupSuggestPromptProps {
  instructorId: string;
  instructorName: string;
}

export function BackupSuggestPrompt({ instructorId, instructorName }: BackupSuggestPromptProps) {
  const [dismissed, setDismissed] = useState(false);
  const [nickname, setNickname] = useState('');
  const queryClient = useQueryClient();

  const addMutation = useMutation({
    mutationFn: () =>
      api.backupInstructors.add({
        instructor_id: instructorId,
        nickname: nickname || undefined,
        priority: 2,
      }),
    onSuccess: () => {
      toast.success(`${instructorName}님이 백업 강사로 추가되었습니다`);
      queryClient.invalidateQueries({ queryKey: ['backup-instructors'] });
      setDismissed(true);
    },
    onError: () => setDismissed(true),
  });

  if (dismissed) return null;

  return (
    <Card className="border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/20">
      <CardContent className="p-4">
        <p className="text-sm font-medium mb-2">
          {instructorName}님을 백업 강사로 등록하시겠어요?
        </p>
        <p className="text-xs text-muted-foreground mb-3">
          다음에 급구 공고 시 우선 알림을 보낼 수 있습니다
        </p>
        <div className="flex gap-2">
          <Input
            placeholder="별칭 (선택)"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            className="min-h-[40px] flex-1 text-sm"
          />
          <Button
            size="sm"
            className="min-h-[40px] shrink-0"
            onClick={() => addMutation.mutate()}
            disabled={addMutation.isPending}
          >
            <UserPlus className="size-4 mr-1" />
            추가
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="min-h-[40px] shrink-0 text-muted-foreground"
            onClick={() => setDismissed(true)}
          >
            닫기
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
