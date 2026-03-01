'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Loader2, UserPlus, Trash2 } from 'lucide-react';
import api, { APIError } from '@/lib/api-client';
import type { BackupInstructorResponse } from '@/lib/api-types';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const PRIORITY_LABELS: Record<number, { label: string; color: string }> = {
  1: { label: '주력', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' },
  2: { label: '보조', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' },
  3: { label: '일반', color: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' },
};

function BackupCard({
  backup,
  onRemove,
}: {
  backup: BackupInstructorResponse;
  onRemove: () => void;
}) {
  const priorityInfo = PRIORITY_LABELS[backup.priority] ?? PRIORITY_LABELS[3];

  return (
    <Card>
      <CardContent className="flex items-center justify-between gap-3 p-4">
        <div className="flex flex-col gap-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold truncate">
              {backup.nickname ?? backup.instructor_name ?? '강사'}
            </span>
            <Badge className={`text-xs ${priorityInfo.color}`}>
              {priorityInfo.label}
            </Badge>
          </div>
          {backup.instructor_categories && backup.instructor_categories.length > 0 && (
            <p className="text-xs text-muted-foreground">
              {backup.instructor_categories.join(', ')}
            </p>
          )}
          {backup.note && (
            <p className="text-xs text-muted-foreground truncate">{backup.note}</p>
          )}
          <p className="text-xs text-muted-foreground">
            완료 {backup.total_completed}건
            {backup.instructor_rating ? ` | ${backup.instructor_rating.toFixed(1)}점` : ''}
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="shrink-0 text-destructive"
          onClick={onRemove}
          aria-label="백업 강사 삭제"
        >
          <Trash2 className="size-4" />
        </Button>
      </CardContent>
    </Card>
  );
}

export function BackupInstructorList() {
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);

  const query = useQuery({
    queryKey: ['backup-instructors'],
    queryFn: () => api.backupInstructors.list(),
  });

  const removeMutation = useMutation({
    mutationFn: (instructorId: string) => api.backupInstructors.remove(instructorId),
    onSuccess: () => {
      toast.success('백업 강사가 삭제되었습니다');
      queryClient.invalidateQueries({ queryKey: ['backup-instructors'] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  if (query.isLoading) {
    return (
      <div className="flex items-center justify-center py-12" role="status">
        <Loader2 className="size-6 animate-spin mr-2" />
        <span className="text-sm text-muted-foreground">로딩 중...</span>
      </div>
    );
  }

  const items = query.data?.items ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">백업 강사 ({items.length})</h2>
        <Button size="sm" className="min-h-[44px]" onClick={() => setShowAdd(true)}>
          <UserPlus className="size-4 mr-1" />
          추가
        </Button>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-12 text-sm text-muted-foreground">
          <p>아직 등록된 백업 강사가 없습니다</p>
          <p className="mt-1">자주 함께 일하는 강사를 추가하세요</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {items.map((backup) => (
            <BackupCard
              key={backup.id}
              backup={backup}
              onRemove={() => removeMutation.mutate(backup.instructor_id)}
            />
          ))}
        </div>
      )}

      <AddBackupDialog open={showAdd} onOpenChange={setShowAdd} />
    </div>
  );
}

function AddBackupDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const queryClient = useQueryClient();
  const [instructorId, setInstructorId] = useState('');
  const [nickname, setNickname] = useState('');
  const [note, setNote] = useState('');
  const [priority, setPriority] = useState(3);

  const addMutation = useMutation({
    mutationFn: () =>
      api.backupInstructors.add({
        instructor_id: instructorId,
        nickname: nickname || undefined,
        note: note || undefined,
        priority,
      }),
    onSuccess: () => {
      toast.success('백업 강사가 추가되었습니다');
      queryClient.invalidateQueries({ queryKey: ['backup-instructors'] });
      onOpenChange(false);
      setInstructorId('');
      setNickname('');
      setNote('');
      setPriority(3);
    },
    onError: (err: Error) => {
      if (err instanceof APIError) {
        if (err.code === 'ALREADY_IN_BACKUP') {
          toast.warning('이미 백업 강사로 등록되어 있습니다');
        } else {
          toast.error(err.message);
        }
      } else {
        toast.error('추가 실패');
      }
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>백업 강사 추가</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">강사 ID</label>
            <Input
              placeholder="수락한 강사의 ID"
              value={instructorId}
              onChange={(e) => setInstructorId(e.target.value)}
              className="min-h-[44px]"
            />
            <p className="text-xs text-muted-foreground mt-1">
              매칭 완료 후 자동으로 제안됩니다
            </p>
          </div>
          <div>
            <label className="text-sm font-medium">별칭</label>
            <Input
              placeholder="예: 김쌤 (월수금 오전)"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              className="min-h-[44px]"
            />
          </div>
          <div>
            <label className="text-sm font-medium">메모</label>
            <Input
              placeholder="예: 허리재활 전문, 월수금 오전 가능"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="min-h-[44px]"
            />
          </div>
          <div>
            <label className="text-sm font-medium">우선순위</label>
            <div className="flex gap-2 mt-1">
              {[1, 2, 3].map((p) => (
                <Button
                  key={p}
                  type="button"
                  variant={priority === p ? 'default' : 'outline'}
                  size="sm"
                  className="min-h-[40px] flex-1"
                  onClick={() => setPriority(p)}
                >
                  {PRIORITY_LABELS[p].label}
                </Button>
              ))}
            </div>
          </div>
          <Button
            className="min-h-[44px] w-full"
            disabled={!instructorId || addMutation.isPending}
            onClick={() => addMutation.mutate()}
          >
            {addMutation.isPending ? '추가 중...' : '추가하기'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
