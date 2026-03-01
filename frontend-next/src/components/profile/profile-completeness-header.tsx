'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import api from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Loader2 } from 'lucide-react';

export function ProfileCompletenessHeader() {
  const user = useAuthStore((s) => s.user);
  const isInstructor = user?.role === 'instructor';

  const { data, isLoading } = useQuery({
    queryKey: ['profile', 'completeness'],
    queryFn: () => api.profileCompleteness.get(),
  });

  const percentage = data?.percentage ?? 0;

  const colorClass =
    percentage >= 90
      ? 'text-green-600'
      : percentage >= 70
        ? 'text-yellow-600'
        : 'text-red-600';

  const progressColor =
    percentage >= 90
      ? '[&>div]:bg-green-500'
      : percentage >= 70
        ? '[&>div]:bg-yellow-500'
        : '[&>div]:bg-red-500';

  if (isLoading) {
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-semibold">내 프로필</h2>
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        </div>
        <Progress value={0} className="h-2" />
      </div>
    );
  }

  const missingFields = data?.missing_fields ?? [];

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">내 프로필</h2>
        <span className={`text-lg font-bold ${colorClass}`}>{percentage}%</span>
      </div>
      <Progress value={percentage} className={`h-2 ${progressColor}`} />
      {missingFields.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {missingFields.map((field: string) => (
            <Badge key={field} variant="outline" className="text-xs text-muted-foreground">
              {field}
            </Badge>
          ))}
        </div>
      )}
      {/* Next action hint */}
      {percentage >= 70 ? (
        <p className="text-xs text-green-600 dark:text-green-400 pt-1">
          프로필 준비 완료!{' '}
          <Link href="/steps/jobs" className="font-medium underline underline-offset-2">
            {isInstructor ? '공고 찾아보기' : '공고 등록하기'}
          </Link>
        </p>
      ) : percentage > 0 ? (
        <p className="text-xs text-muted-foreground pt-1">
          {Math.ceil(70 - percentage)}% 더 채우면 {isInstructor ? '지원' : '공고 등록'}이 가능합니다
        </p>
      ) : null}
    </div>
  );
}
