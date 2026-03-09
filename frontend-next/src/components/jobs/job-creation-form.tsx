'use client';

import { useState } from 'react';
import { useForm, type SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api-client';
import { jobPostSchema } from '@/lib/validators';
import type { JobPostCreate } from '@/lib/api-types';
import {
  ATMOSPHERE_OPTIONS,
  CATEGORIES,
  JOB_TYPES,
  RATE_OPTIONS,
  REGION_NAMES,
  SEOUL_REGIONS,
} from '@/lib/constants';
import { cn, formatCurrency } from '@/lib/utils';
import { HelpCircle, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { KakaoMap } from '@/components/jobs/kakao-map';
import { TeachingStyleSelector } from '@/components/profile/teaching-style-selector';

/**
 * Form input type: matches what users fill in before Zod applies defaults.
 * We use JobPostCreate (the API type) directly so the form output aligns
 * with both Zod validation output and the API call payload.
 */
type JobFormValues = JobPostCreate;

interface JobCreationFormProps {
  onSuccess?: () => void;
}

export function JobCreationForm({ onSuccess }: JobCreationFormProps) {
  const queryClient = useQueryClient();

  // Today's date as default for urgent posts
  const today = new Date().toISOString().split('T')[0];

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<JobFormValues>({
    resolver: zodResolver(jobPostSchema) as any, // eslint-disable-line @typescript-eslint/no-explicit-any -- Zod v4 input/output type gap
    defaultValues: {
      is_urgent: false,
      category: undefined,
      job_type: undefined,
      region: '',
      hourly_rate: 0,
      date: today,
      start_time: '',
      end_time: '',
      description: '',
      total_sessions: 1,
      required_experience_years: 0,
      required_certifications: [],
      payment_method: 'bank_transfer',
      terms_agreed: true,
      latitude: null,
      longitude: null,
      handoff_class_topic: '',
      handoff_class_sequence_info: '',
      handoff_atmosphere_preference: '',
      handoff_member_notes: '',
      handoff_equipment_notes: '',
    },
  });

  // Rate range state (min/max)
  const [rateMin, setRateMin] = useState<number>(0);
  const [rateMax, setRateMax] = useState<number>(0);

  // Preferred teaching style
  const [preferredStyle, setPreferredStyle] = useState<Record<string, string>>({});

  const isUrgent = watch('is_urgent');
  const category = watch('category');
  const jobType = watch('job_type');
  const region = watch('region');
  const hourlyRate = watch('hourly_rate');
  const description = watch('description');

  // Build real-time title preview
  const jobTypeLabel =
    JOB_TYPES.find((t) => t.value === jobType)?.label ?? '';
  const categoryLabel =
    CATEGORIES.find((c) => c.value === category)?.label ?? '';
  const titlePreview = [
    jobTypeLabel ? `[${jobTypeLabel}]` : '',
    region || '',
    categoryLabel ? `${categoryLabel} 강사` : '',
    description ? `- ${description}` : '',
  ]
    .filter(Boolean)
    .join(' ');

  // Build rate range text for title/description
  const rateRangeText =
    rateMin > 0 && rateMax > 0
      ? rateMin === rateMax
        ? formatCurrency(rateMin)
        : `${formatCurrency(rateMin)}~${formatCurrency(rateMax)}`
      : '';

  const createJob = useMutation({
    mutationFn: (data: JobFormValues) => {
      // Append rate range to description if a range was selected
      let desc = data.description ?? '';
      if (rateMax > rateMin && rateMin > 0) {
        desc = desc ? `${desc} [시급 ${rateRangeText}]` : `시급 ${rateRangeText}`;
      }
      const payload: JobPostCreate = {
        ...data,
        title: titlePreview || data.title,
        description: desc,
        preferred_style: Object.keys(preferredStyle).length > 0 ? preferredStyle : undefined,
      };
      return api.jobPosts.create(payload);
    },
    onSuccess: () => {
      toast.success('공고가 등록되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['studio-job-posts'] });
      onSuccess?.();
    },
    onError: (error: Error) => {
      toast.error(`공고 등록 실패: ${error.message}`);
    },
  });

  const onSubmit: SubmitHandler<JobFormValues> = (data) => {
    createJob.mutate(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Urgency toggle */}
      <div className="space-y-2">
        <label className="text-sm font-medium">공고 유형</label>
        <ToggleGroup
          type="single"
          value={isUrgent ? 'urgent' : 'normal'}
          onValueChange={(val) => {
            if (!val) return;
            const urgent = val === 'urgent';
            setValue('is_urgent', urgent);
            if (urgent) {
              setValue('date', today);
            }
          }}
          className="w-full"
        >
          <ToggleGroupItem
            value="urgent"
            aria-label="긴급 대타"
            className={`min-h-[44px] flex-1 text-base font-semibold ${
              isUrgent
                ? 'border-urgent/40 bg-urgent/10 text-urgent data-[state=on]:!bg-urgent data-[state=on]:!text-urgent-foreground dark:border-urgent/50 dark:bg-urgent/20 dark:text-urgent dark:data-[state=on]:!bg-urgent'
                : ''
            }`}
          >
            긴급 대타
          </ToggleGroupItem>
          <ToggleGroupItem
            value="normal"
            aria-label="일반 공고"
            className="min-h-[44px] flex-1 text-base font-semibold"
          >
            일반 공고
          </ToggleGroupItem>
        </ToggleGroup>
        {isUrgent && (
          <p className="text-sm text-urgent dark:text-urgent">
            급하게 강사가 필요할 때 사용하세요. 강사들에게 우선 노출됩니다.
          </p>
        )}
      </div>

      {/* Title preview */}
      {titlePreview && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="px-4 py-3">
            <p className="text-xs font-medium text-muted-foreground">
              미리보기
            </p>
            <p className="mt-1 text-base font-semibold">{titlePreview}</p>
          </CardContent>
        </Card>
      )}

      {/* Two-column layout */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Left column: Steps 1-3 */}
        <div className="space-y-5">
          {/* Step 1: Category */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              1. 종목 <span className="text-destructive">*</span>
            </label>
            <ToggleGroup
              type="single"
              value={category ?? ''}
              onValueChange={(val) => {
                if (val) setValue('category', val as 'pilates' | 'yoga', { shouldValidate: true });
              }}
              className="w-full"
            >
              {CATEGORIES.map((c) => (
                <ToggleGroupItem
                  key={c.value}
                  value={c.value}
                  aria-label={c.label}
                  className="min-h-[44px] flex-1 text-base"
                >
                  {c.label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
            {errors.category && (
              <p className="text-sm text-destructive">
                {errors.category.message}
              </p>
            )}
          </div>

          {/* Step 2: Job Type */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              2. 유형 <span className="text-destructive">*</span>
            </label>
            <ToggleGroup
              type="single"
              value={jobType ?? ''}
              onValueChange={(val) => {
                if (val) setValue('job_type', val as 'substitute' | 'regular' | 'contract', { shouldValidate: true });
              }}
              className="w-full"
            >
              {JOB_TYPES.map((t) => (
                <ToggleGroupItem
                  key={t.value}
                  value={t.value}
                  aria-label={t.label}
                  className="min-h-[44px] flex-1 text-base relative group"
                >
                  <span>{t.label}</span>
                  {t.value === 'regular' && (
                    <span className="relative ml-1 inline-flex">
                      <HelpCircle className="size-3.5 text-muted-foreground" aria-hidden="true" />
                      <span className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-foreground px-2.5 py-1.5 text-xs text-background opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
                        {t.description}
                      </span>
                    </span>
                  )}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
            {jobType === 'regular' && (
              <p className="text-xs text-muted-foreground">
                여러 날짜에 대타가 필요할 때 선택하세요 (예: 3/10, 3/11 총 2회)
              </p>
            )}
            {errors.job_type && (
              <p className="text-sm text-destructive">
                {errors.job_type.message}
              </p>
            )}
          </div>

          {/* Step 3: Region + Map */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              3. 지역 <span className="text-destructive">*</span>
            </label>
            <Select
              value={region ?? ''}
              onValueChange={(val) => {
                setValue('region', val, { shouldValidate: true });
                const coords = SEOUL_REGIONS[val];
                if (coords) {
                  setValue('latitude', coords.lat);
                  setValue('longitude', coords.lng);
                }
              }}
            >
              <SelectTrigger className="min-h-[44px] w-full text-base">
                <SelectValue placeholder="지역을 선택하세요" />
              </SelectTrigger>
              <SelectContent>
                {REGION_NAMES.map((name) => (
                  <SelectItem key={name} value={name}>
                    {name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.region && (
              <p className="text-sm text-destructive">
                {errors.region.message}
              </p>
            )}
            {region && <KakaoMap region={region} height={200} />}
          </div>
        </div>

        {/* Right column: Steps 4-6 */}
        <div className="space-y-5">
          {/* Step 4: Rate Range */}
          <div className="space-y-3">
            <label className="text-sm font-medium">
              4. 시급 범위 <span className="text-destructive">*</span>
            </label>
            <div className="space-y-2">
              <div>
                <span className="mb-1 block text-xs text-muted-foreground">최소</span>
                <div className="flex flex-wrap gap-1.5">
                  {RATE_OPTIONS.map((opt) => (
                    <Button
                      key={opt.value}
                      type="button"
                      variant={rateMin === opt.value ? 'default' : 'outline'}
                      size="sm"
                      className="min-h-[40px] min-w-[40px] text-sm"
                      onClick={() => {
                        setRateMin(opt.value);
                        setValue('hourly_rate', opt.value, { shouldValidate: true });
                        // Auto-set max if not set or less than min
                        if (rateMax < opt.value) setRateMax(opt.value);
                      }}
                    >
                      {opt.label}
                    </Button>
                  ))}
                </div>
              </div>
              <div>
                <span className="mb-1 block text-xs text-muted-foreground">최대</span>
                <div className="flex flex-wrap gap-1.5">
                  {RATE_OPTIONS.map((opt) => (
                    <Button
                      key={opt.value}
                      type="button"
                      variant={rateMax === opt.value ? 'default' : 'outline'}
                      size="sm"
                      className="min-h-[40px] min-w-[40px] text-sm"
                      disabled={rateMin > 0 && opt.value < rateMin}
                      onClick={() => {
                        setRateMax(opt.value);
                      }}
                    >
                      {opt.label}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
            {rateMin > 0 && rateMax > 0 && (
              <p className="text-sm font-medium text-foreground">
                {rateMin === rateMax
                  ? formatCurrency(rateMin)
                  : `${formatCurrency(rateMin)} ~ ${formatCurrency(rateMax)}`}
                <span className="ml-1.5 text-xs font-normal text-muted-foreground">
                  구체적인 금액은 연락 후 조율
                </span>
              </p>
            )}
            {errors.hourly_rate && (
              <p className="text-sm text-destructive">
                {errors.hourly_rate.message}
              </p>
            )}
          </div>

          {/* Step 5: When */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              5. 언제 <span className="text-destructive">*</span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label
                  htmlFor="job-date"
                  className="mb-1 block text-xs text-muted-foreground"
                >
                  날짜
                </label>
                <Input
                  id="job-date"
                  type="date"
                  min={today}
                  className="min-h-[44px] text-base"
                  {...register('date')}
                />
              </div>
              <div>
                <label
                  htmlFor="job-start-time"
                  className="mb-1 block text-xs text-muted-foreground"
                >
                  시작
                </label>
                <Input
                  id="job-start-time"
                  type="time"
                  step={300}
                  className="min-h-[44px] text-base"
                  {...register('start_time')}
                />
              </div>
              <div>
                <label
                  htmlFor="job-end-time"
                  className="mb-1 block text-xs text-muted-foreground"
                >
                  종료
                </label>
                <Input
                  id="job-end-time"
                  type="time"
                  step={300}
                  className="min-h-[44px] text-base"
                  {...register('end_time')}
                />
              </div>
            </div>
            {(errors.date || errors.start_time || errors.end_time) && (
              <p className="text-sm text-destructive">
                {errors.date?.message ||
                  errors.start_time?.message ||
                  errors.end_time?.message}
              </p>
            )}
          </div>

          {/* Step 6: Memo */}
          <div className="space-y-2">
            <label htmlFor="job-memo" className="text-sm font-medium">
              6. 한 줄 메모
            </label>
            <Input
              id="job-memo"
              placeholder="예: 오전 수업 대타"
              className="min-h-[44px] text-base"
              {...register('description')}
            />
          </div>
        </div>
      </div>

      {/* Step 7: Handoff Note (required) */}
      <div className="space-y-4 rounded-xl border-2 border-primary/30 bg-primary/5 p-5">
        <div>
          <label className="text-sm font-semibold">
            7. 인수인계 노트 <span className="text-destructive">*</span>
          </label>
          <p className="mt-0.5 text-xs text-muted-foreground">
            회원과의 신뢰를 위해 필수 작성 항목입니다.
          </p>
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium">
              수업 주제 <span className="text-destructive">*</span>
            </label>
            <Input
              placeholder="예: 허리 재활 시퀀스 3주차"
              className="min-h-[44px]"
              {...register('handoff_class_topic')}
            />
            {errors.handoff_class_topic && (
              <p className="mt-1 text-sm text-destructive">{errors.handoff_class_topic.message}</p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium">
              수업 진도 / 내용 <span className="text-destructive">*</span>
            </label>
            <Textarea
              placeholder="이전 수업에서 다룬 내용, 다음에 이어갈 내용"
              rows={3}
              {...register('handoff_class_sequence_info')}
            />
            {errors.handoff_class_sequence_info && (
              <p className="mt-1 text-sm text-destructive">{errors.handoff_class_sequence_info.message}</p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium">
              수업 분위기 <span className="text-destructive">*</span>
            </label>
            <Select
              value={watch('handoff_atmosphere_preference') ?? ''}
              onValueChange={(val) => setValue('handoff_atmosphere_preference', val, { shouldValidate: true })}
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
            {errors.handoff_atmosphere_preference && (
              <p className="mt-1 text-sm text-destructive">{errors.handoff_atmosphere_preference.message}</p>
            )}
          </div>
        </div>

        {/* Sensitive fields */}
        <div className="space-y-3 rounded-lg border border-dashed border-amber-300 bg-amber-50/50 p-4 dark:border-amber-700 dark:bg-amber-950/20">
          <p className="flex items-center gap-1.5 text-xs font-medium text-amber-700 dark:text-amber-300">
            <Lock className="size-3.5" />
            아래 정보는 수락 후에만 대타 강사에게 공개됩니다
          </p>

          <div>
            <label className="text-sm font-medium">
              회원 주의사항 <span className="text-destructive">*</span>
            </label>
            <Textarea
              placeholder="특정 회원 특이사항, 주의할 점"
              rows={2}
              {...register('handoff_member_notes')}
            />
            {errors.handoff_member_notes && (
              <p className="mt-1 text-sm text-destructive">{errors.handoff_member_notes.message}</p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium">
              기구 세팅 <span className="text-destructive">*</span>
            </label>
            <Textarea
              placeholder="리포머/캐딜락 세팅, 소도구 위치 등"
              rows={2}
              {...register('handoff_equipment_notes')}
            />
            {errors.handoff_equipment_notes && (
              <p className="mt-1 text-sm text-destructive">{errors.handoff_equipment_notes.message}</p>
            )}
          </div>
        </div>
      </div>

      {/* Step 8: Preferred Style (optional) */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          8. 원하는 수업 스타일 <span className="text-xs text-muted-foreground">(선택)</span>
        </label>
        <TeachingStyleSelector
          value={preferredStyle}
          onChange={(style) => setPreferredStyle(style)}
          keys={['correction_style', 'class_atmosphere', 'intensity_level']}
        />
      </div>

      {/* Submit */}
      <Button
        type="submit"
        size="lg"
        variant={isUrgent ? 'default' : 'default'}
        disabled={createJob.isPending}
        className={cn(
          'min-h-[48px] w-full text-base font-semibold',
          isUrgent && 'bg-urgent text-urgent-foreground hover:bg-urgent/90',
        )}
      >
        {createJob.isPending
          ? '등록 중...'
          : isUrgent
            ? '긴급 공고 등록하기'
            : '공고 등록하기'}
      </Button>
    </form>
  );
}
