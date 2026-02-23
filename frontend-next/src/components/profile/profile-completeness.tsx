'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api-client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

export function ProfileCompleteness() {
  const { data, isLoading } = useQuery({
    queryKey: ['profile', 'completeness'],
    queryFn: () => api.profileCompleteness.get(),
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="py-6 text-center text-sm text-muted-foreground">
          프로필 완성도를 불러올 수 없습니다.
        </CardContent>
      </Card>
    );
  }

  const { percentage, missing_fields: rawMissingFields, missing_fields_display } = data;
  const missing_fields = rawMissingFields ?? [];
  const displayMap = missing_fields_display ?? {};

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">프로필 완성도</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <span
            className={cn(
              'text-3xl font-bold',
              percentage < 70
                ? 'text-red-500'
                : percentage < 90
                  ? 'text-yellow-500'
                  : 'text-green-500',
            )}
            aria-label={`프로필 완성도 ${percentage}%`}
          >
            {percentage}%
          </span>
        </div>

        <Progress
          value={percentage}
          className={cn(
            'h-3',
            percentage < 70
              ? '[&>div]:bg-red-500'
              : percentage < 90
                ? '[&>div]:bg-yellow-500'
                : '[&>div]:bg-green-500',
          )}
          aria-label={`프로필 완성도 ${percentage}%`}
        />

        {percentage < 100 && (
          <p className="text-center text-xs text-muted-foreground">
            프로필을 완성하면 Trust Score가 올라갑니다
          </p>
        )}

        {missing_fields.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">
              미완성 항목
            </p>
            <div className="flex flex-wrap gap-1">
              {missing_fields.map((field) => (
                <span
                  key={field}
                  className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                >
                  {displayMap[field] ?? field}
                </span>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
