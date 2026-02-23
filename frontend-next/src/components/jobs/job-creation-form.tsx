'use client';

import { useForm, type SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api-client';
import { jobPostSchema } from '@/lib/validators';
import type { JobPostCreate } from '@/lib/api-types';
import {
  CATEGORIES,
  JOB_TYPES,
  RATE_PRESETS,
  REGION_NAMES,
} from '@/lib/constants';
import { formatCurrency } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<JobFormValues>({
    resolver: zodResolver(jobPostSchema) as any, // eslint-disable-line @typescript-eslint/no-explicit-any -- Zod v4 input/output type gap
    defaultValues: {
      category: undefined,
      job_type: undefined,
      region: '',
      hourly_rate: 0,
      date: '',
      start_time: '',
      end_time: '',
      description: '',
      total_sessions: 1,
      required_experience_years: 0,
      required_certifications: [],
    },
  });

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

  const createJob = useMutation({
    mutationFn: (data: JobFormValues) => {
      // Set the generated title before sending
      const payload: JobPostCreate = {
        ...data,
        title: titlePreview || data.title,
      };
      return api.jobPosts.create(payload);
    },
    onSuccess: () => {
      toast.success('공고가 등록되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['jobPosts'] });
      onSuccess?.();
    },
    onError: (error: Error) => {
      toast.error(`공고 등록 실패: ${error.message}`);
    },
  });

  const onSubmit: SubmitHandler<JobFormValues> = (data) => {
    createJob.mutate(data);
  };

  // Today's date as default min for the date input
  const today = new Date().toISOString().split('T')[0];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
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
                  className="min-h-[44px] flex-1 text-base"
                >
                  {t.label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
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
              onValueChange={(val) =>
                setValue('region', val, { shouldValidate: true })
              }
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
          {/* Step 4: Rate */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              4. 시급 <span className="text-destructive">*</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {RATE_PRESETS.map((preset) => (
                <Button
                  key={preset.value}
                  type="button"
                  variant={
                    hourlyRate === preset.value ? 'default' : 'outline'
                  }
                  size="sm"
                  className="min-h-[44px] min-w-[44px] text-base"
                  onClick={() =>
                    setValue('hourly_rate', preset.value, {
                      shouldValidate: true,
                    })
                  }
                >
                  {preset.label}
                </Button>
              ))}
            </div>
            {hourlyRate > 0 && (
              <p className="text-sm text-muted-foreground">
                선택: {formatCurrency(hourlyRate)}
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
              placeholder="예: 오전 수업 대행"
              className="min-h-[44px] text-base"
              {...register('description')}
            />
          </div>
        </div>
      </div>

      {/* Submit */}
      <Button
        type="submit"
        size="lg"
        disabled={createJob.isPending}
        className="min-h-[48px] w-full text-base font-semibold"
      >
        {createJob.isPending ? '등록 중...' : '공고 등록하기'}
      </Button>
    </form>
  );
}
