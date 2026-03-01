'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api-client';
import { APIError } from '@/lib/api-client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { RefreshCw, Lightbulb } from 'lucide-react';

const LEVEL_BADGES: Record<string, string> = {
  bronze: '\uD83E\uDD49',
  silver: '\uD83E\uDD48',
  gold: '\uD83E\uDD47',
  platinum: '\uD83C\uDFC6',
};

const FACTOR_ORDER = [
  'identity_verification',
  'contract_history',
  'profile_completeness',
  'review_average',
  'certifications',
  'response_rate',
  'account_age',
  'no_show_penalty',
];

export function TrustScoreDetail() {
  const queryClient = useQueryClient();

  const { data: trustData, isLoading } = useQuery({
    queryKey: ['trustScore'],
    queryFn: () => api.trustScore.get(),
  });

  const refresh = useMutation({
    mutationFn: () => api.trustScore.refresh(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['trustScore'] });
      toast.success(`Trust Score가 ${data.score}점으로 갱신되었습니다`);
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(error.message);
      } else {
        toast.error('1시간에 한 번만 새로고침 가능합니다');
      }
    },
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

  if (!trustData) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-sm text-muted-foreground">
          Trust Score를 불러올 수 없습니다
        </CardContent>
      </Card>
    );
  }

  const {
    score,
    level,
    level_color,
    breakdown,
    recommendations,
    points_to_next_level,
    factor_labels,
    level_thresholds,
    completed_contracts_count,
    experience_badge,
  } = trustData;

  const badge = LEVEL_BADGES[level_color] || LEVEL_BADGES.bronze;

  // Calculate level progress within current tier
  const currentThreshold = level_thresholds?.find(
    (t) => t.min <= score && score <= t.max,
  );
  const currentIndex = currentThreshold
    ? level_thresholds?.indexOf(currentThreshold) ?? -1
    : -1;
  const nextThreshold =
    currentIndex >= 0 && currentIndex < (level_thresholds?.length ?? 0) - 1
      ? level_thresholds[currentIndex + 1]
      : null;
  const levelProgress = currentThreshold
    ? ((score - currentThreshold.min) /
        (currentThreshold.max - currentThreshold.min + 1)) *
      100
    : 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base">Trust Score</CardTitle>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => refresh.mutate()}
          disabled={refresh.isPending}
          aria-label="Trust Score 새로고침"
          className="min-h-[44px] min-w-[44px]"
        >
          <RefreshCw
            className={`h-4 w-4 ${refresh.isPending ? 'animate-spin' : ''}`}
            aria-hidden="true"
          />
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Score Header */}
        <div className="text-center">
          <div className="text-3xl font-bold" aria-label={`Trust Score ${score}점`}>
            {badge} {score}
            <span className="text-lg text-muted-foreground">/100</span>
          </div>
          <p className="text-sm text-muted-foreground">{level} 등급</p>
          {experience_badge && (
            <p className="mt-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
              {experience_badge.label}
            </p>
          )}
          {!experience_badge && completed_contracts_count != null && (
            <p className="mt-1 text-xs text-muted-foreground">
              완료 {completed_contracts_count}건
            </p>
          )}
        </div>

        {/* Level Progress */}
        <Progress
          value={Math.min(100, levelProgress)}
          className="h-2"
          aria-label={`현재 등급 진행도 ${Math.round(levelProgress)}%`}
        />
        {points_to_next_level > 0 && nextThreshold && (
          <p className="text-center text-xs text-muted-foreground">
            <strong>{points_to_next_level}점</strong>만 더 올리면{' '}
            <strong>{nextThreshold.level}</strong> 등급!
          </p>
        )}
        {score >= 80 && (
          <p className="text-center text-xs text-muted-foreground">
            최고 등급을 유지하고 있습니다!
          </p>
        )}

        {/* Factor Breakdown — always visible for transparency */}
        <div className="space-y-3">
          <p className="text-xs font-medium text-muted-foreground">
            점수 상세 (순수 활동 기반)
          </p>
          {FACTOR_ORDER.map((factorKey) => {
                const current = breakdown?.[factorKey] ?? 0;
                const labelInfo = factor_labels?.[factorKey];
                const name = labelInfo?.name || factorKey;
                const maxPts = labelInfo?.max || 0;

                // Skip no_show_penalty if no penalty applied
                if (factorKey === 'no_show_penalty' && current === 0) {
                  return null;
                }

                // Penalty display (negative score)
                if (factorKey === 'no_show_penalty') {
                  return (
                    <div key={factorKey} className="text-sm">
                      <span className="font-medium text-red-600">
                        {name}: {current}점
                      </span>
                      <p className="text-xs text-muted-foreground">
                        노쇼 기록 시 건당 -20점
                      </p>
                    </div>
                  );
                }

                const progress =
                  maxPts > 0
                    ? Math.max(0, Math.min(100, (current / maxPts) * 100))
                    : 0;

                return (
                  <div key={factorKey} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium">{name}</span>
                      <span className="tabular-nums text-muted-foreground">
                        {current}/{maxPts}
                      </span>
                    </div>
                    <Progress
                      value={progress}
                      className="h-1.5"
                      aria-label={`${name} ${current}/${maxPts}점`}
                    />
                  </div>
                );
          })}
        </div>

        {/* Recommendations & Level Guide in accordion */}
        <Accordion type="single" collapsible>
          {/* Recommendations */}
          {recommendations && recommendations.length > 0 && (
            <AccordionItem value="recommendations">
              <AccordionTrigger className="text-sm">
                점수 올리기
              </AccordionTrigger>
              <AccordionContent className="space-y-2">
                {recommendations.map((rec, i) => (
                  <div
                    key={i}
                    className="flex gap-2 rounded-md bg-blue-50 p-2 text-xs text-blue-700 dark:bg-blue-950 dark:text-blue-300"
                  >
                    <Lightbulb
                      className="mt-0.5 h-3 w-3 shrink-0"
                      aria-hidden="true"
                    />
                    {rec}
                  </div>
                ))}
              </AccordionContent>
            </AccordionItem>
          )}

          {/* Level Guide */}
          <AccordionItem value="levels">
            <AccordionTrigger className="text-sm">등급 안내</AccordionTrigger>
            <AccordionContent className="space-y-1">
              {level_thresholds?.map((t) => {
                const tBadge = LEVEL_BADGES[t.color] || '';
                const isCurrent = t.min <= score && score <= t.max;
                return (
                  <div
                    key={t.level}
                    className={`flex items-center gap-1 text-xs ${
                      isCurrent
                        ? 'font-bold text-primary'
                        : 'text-muted-foreground'
                    }`}
                  >
                    <span aria-hidden="true">{tBadge}</span>
                    <span>{t.level}</span>
                    <span>
                      ({t.min}~{t.max}점)
                    </span>
                    {isCurrent && (
                      <span className="text-primary" aria-label="현재 등급">
                        -- 현재
                      </span>
                    )}
                  </div>
                );
              })}
              <p className="mt-2 text-xs text-muted-foreground">
                Trust Score가 높을수록 매칭 우선순위가 올라갑니다.
              </p>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  );
}
