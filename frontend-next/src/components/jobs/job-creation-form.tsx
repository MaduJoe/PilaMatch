'use client';

import { useCallback, useEffect, useState } from 'react';
import { useForm, type SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ChevronLeft, Lock, Plus, Trash2 } from 'lucide-react';
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
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

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type JobFormValues = JobPostCreate;

interface ScheduleRow {
  date: string;
  start_time: string;
  end_time: string;
}

interface JobCreationFormProps {
  onSuccess?: () => void;
}

// ---------------------------------------------------------------------------
// Template presets
// ---------------------------------------------------------------------------

const PRESETS = [
  {
    id: 'urgent',
    label: '긴급 대행',
    emoji: '🔥',
    desc: '오늘/내일 급한 대타 · 시급 3만원 기본',
    values: { is_urgent: true, job_type: 'substitute' as const, hourly_rate: 30000 },
  },
  {
    id: 'normal',
    label: '일반 공고',
    emoji: '📋',
    desc: '일반 채용 공고 · 시급 4만원 기본',
    values: { is_urgent: false, job_type: 'substitute' as const, hourly_rate: 40000 },
  },
] as const;

// ---------------------------------------------------------------------------
// Step field mapping for validation
// ---------------------------------------------------------------------------

const STEP_FIELDS: Record<number, string[]> = {
  1: ['category', 'job_type'],
  2: ['date', 'start_time', 'end_time', 'hourly_rate'],
  3: [
    'handoff_class_topic',
    'handoff_class_sequence_info',
    'handoff_atmosphere_preference',
    'handoff_member_notes',
    'handoff_equipment_notes',
  ],
};

const TOTAL_STEPS = 4;

const STEP_LABELS = ['기본 설정', '날짜·급여', '상세·인수인계', '확인·등록'];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function JobCreationForm({ onSuccess }: JobCreationFormProps) {
  const queryClient = useQueryClient();
  const today = new Date().toISOString().split('T')[0];

  // Dialog state
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(1);

  // Rate range state
  const [rateMin, setRateMin] = useState<number>(0);
  const [rateMax, setRateMax] = useState<number>(0);

  // Multi-schedule rows for "regular" type
  const [schedules, setSchedules] = useState<ScheduleRow[]>([
    { date: today, start_time: '', end_time: '' },
  ]);

  const form = useForm<JobFormValues>({
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

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    trigger,
    reset,
    formState: { errors },
  } = form;

  const isUrgent = watch('is_urgent');
  const category = watch('category');
  const jobType = watch('job_type');
  const region = watch('region');
  const description = watch('description');
  const isMultiSchedule = jobType === 'regular';

  // ---- Derived values ----
  const jobTypeLabel = JOB_TYPES.find((t) => t.value === jobType)?.label ?? '';
  const categoryLabel = CATEGORIES.find((c) => c.value === category)?.label ?? '';
  const titlePreview = [
    jobTypeLabel ? `[${jobTypeLabel}]` : '',
    region || '',
    categoryLabel ? `${categoryLabel} 강사` : '',
    description ? `- ${description}` : '',
  ]
    .filter(Boolean)
    .join(' ');

  const rateRangeText =
    rateMin > 0 && rateMax > 0
      ? rateMin === rateMax
        ? formatCurrency(rateMin)
        : `${formatCurrency(rateMin)}~${formatCurrency(rateMax)}`
      : '';

  // ---- Schedule helpers ----
  const addScheduleRow = useCallback(() => {
    setSchedules((prev) => [...prev, { date: '', start_time: '', end_time: '' }]);
  }, []);

  const removeScheduleRow = useCallback((index: number) => {
    setSchedules((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const updateScheduleRow = useCallback(
    (index: number, field: keyof ScheduleRow, value: string) => {
      setSchedules((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], [field]: value };
        if (index === 0) {
          if (field === 'date') setValue('date', value, { shouldValidate: true });
          if (field === 'start_time') setValue('start_time', value, { shouldValidate: true });
          if (field === 'end_time') setValue('end_time', value, { shouldValidate: true });
        }
        setValue('total_sessions', next.length, { shouldValidate: false });
        return next;
      });
    },
    [setValue],
  );

  // When job type changes, reset schedules if switching away from regular
  useEffect(() => {
    if (jobType !== 'regular' && schedules.length > 1) {
      setSchedules([schedules[0]]);
      setValue('total_sessions', 1);
    }
  }, [jobType]); // eslint-disable-line react-hooks/exhaustive-deps

  // ---- Template apply ----
  const [activePreset, setActivePreset] = useState<string | null>(null);

  const applyPreset = useCallback(
    (presetId: string) => {
      const preset = PRESETS.find((p) => p.id === presetId);
      if (!preset) return;
      setActivePreset(presetId);
      setValue('is_urgent', preset.values.is_urgent);
      setValue('job_type', preset.values.job_type, { shouldValidate: true });
      setValue('hourly_rate', preset.values.hourly_rate, { shouldValidate: true });
      setRateMin(preset.values.hourly_rate);
      setRateMax(preset.values.hourly_rate);
      if (preset.values.is_urgent) {
        updateScheduleRow(0, 'date', today);
      }
    },
    [setValue, today, updateScheduleRow],
  );

  // ---- Reset on close ----
  const handleOpenChange = useCallback(
    (nextOpen: boolean) => {
      setOpen(nextOpen);
      if (!nextOpen) {
        setStep(1);
        reset();
        setRateMin(0);
        setRateMax(0);
        setActivePreset(null);
        setSchedules([{ date: today, start_time: '', end_time: '' }]);
      }
    },
    [reset, today],
  );

  // ---- Step navigation ----
  const goNext = useCallback(async () => {
    const fields = STEP_FIELDS[step];
    if (fields) {
      const valid = await trigger(fields as any); // eslint-disable-line @typescript-eslint/no-explicit-any
      if (!valid) return;
    }
    setStep((s) => Math.min(s + 1, TOTAL_STEPS));
  }, [step, trigger]);

  const goBack = useCallback(() => {
    setStep((s) => Math.max(s - 1, 1));
  }, []);

  // ---- Submit ----
  const createJob = useMutation({
    mutationFn: (data: JobFormValues) => {
      let desc = data.description ?? '';
      if (rateMax > rateMin && rateMin > 0) {
        desc = desc ? `${desc} [시급 ${rateRangeText}]` : `시급 ${rateRangeText}`;
      }
      if (isMultiSchedule && schedules.length > 1) {
        const scheduleText = schedules
          .map((s, i) => `${i + 1}회: ${s.date} ${s.start_time}~${s.end_time}`)
          .join(' / ');
        desc = desc ? `${desc}\n[일정] ${scheduleText}` : `[일정] ${scheduleText}`;
      }
      const payload: JobPostCreate = {
        ...data,
        title: titlePreview || data.title,
        description: desc,
        total_sessions: schedules.length,
      };
      return api.jobPosts.create(payload);
    },
    onSuccess: () => {
      toast.success('공고가 등록되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['studio-job-posts'] });
      handleOpenChange(false);
      onSuccess?.();
    },
    onError: (error: Error) => {
      toast.error(`공고 등록 실패: ${error.message}`);
    },
  });

  const onSubmit: SubmitHandler<JobFormValues> = (data) => {
    createJob.mutate(data);
  };

  // ---- Progress bar ----
  const ProgressBar = () => (
    <div className="flex gap-1.5">
      {Array.from({ length: TOTAL_STEPS }, (_, i) => (
        <div
          key={i}
          className={cn(
            'h-1.5 flex-1 rounded-full transition-colors duration-200',
            i < step ? 'bg-primary' : 'bg-muted',
          )}
        />
      ))}
    </div>
  );

  // =========================================================================
  // Step 1: 긴급 대행 프리셋 + 종목 + 유형 + 지역
  // =========================================================================
  const renderStep1 = () => (
    <div className="space-y-5">
      {/* 공고 유형 (긴급 대행 / 일반 공고) */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          공고 유형 <span className="text-destructive">*</span>
        </label>
        <div className="grid grid-cols-2 gap-2">
          {PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              className={cn(
                'flex items-center gap-3 rounded-xl border p-3 text-left transition-all',
                activePreset === preset.id
                  ? preset.id === 'urgent'
                    ? 'border-urgent/40 bg-urgent/10 ring-1 ring-urgent/30'
                    : 'border-primary/40 bg-primary/10 ring-1 ring-primary/30'
                  : 'border-border hover:border-primary/30 hover:bg-muted/50',
              )}
              onClick={() => applyPreset(preset.id)}
            >
              <span className="text-xl" aria-hidden="true">{preset.emoji}</span>
              <div>
                <p className="text-sm font-semibold">{preset.label}</p>
                <p className="text-[10px] text-muted-foreground leading-tight">{preset.desc}</p>
              </div>
            </button>
          ))}
        </div>
        {isUrgent && (
          <p className="text-xs text-urgent">강사들에게 우선 노출됩니다.</p>
        )}
      </div>

      {/* 종목 */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          종목 <span className="text-destructive">*</span>
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
            {errors.category.message ?? '종목을 선택해주세요'}
          </p>
        )}
      </div>

      {/* 회수 */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          회수 <span className="text-destructive">*</span>
        </label>
        <ToggleGroup
          type="single"
          value={jobType ?? ''}
          onValueChange={(val) => {
            if (val)
              setValue('job_type', val as 'substitute' | 'regular' | 'contract', {
                shouldValidate: true,
              });
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
            {errors.job_type.message ?? '회수를 선택해주세요'}
          </p>
        )}
      </div>

      {/* 지역 (선택) */}
      <div className="space-y-2">
        <label className="text-sm font-medium">지역</label>
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
      </div>
    </div>
  );

  // =========================================================================
  // Step 2: 날짜 + 시간 + 시급
  // =========================================================================
  const renderStep2 = () => (
    <div className="space-y-5">
      {/* 긴급 표시 */}
      {isUrgent && (
        <p className="rounded-lg bg-urgent/10 px-3 py-2 text-sm font-medium text-urgent">
          긴급 대타 — 급하게 강사가 필요할 때 사용하세요
        </p>
      )}

      {/* 날짜/시간 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">
            날짜 및 시간 <span className="text-destructive">*</span>
          </label>
          {isMultiSchedule && (
            <span className="text-xs text-muted-foreground">{schedules.length}회</span>
          )}
        </div>
        <div className="space-y-2">
          {schedules.map((row, index) => (
            <div key={index} className="flex items-end gap-2">
              {isMultiSchedule && schedules.length > 1 && (
                <span className="mb-2.5 w-5 shrink-0 text-xs font-medium tabular-nums text-muted-foreground">
                  {index + 1}.
                </span>
              )}
              <div className="grid flex-1 grid-cols-3 gap-2">
                <div>
                  {index === 0 && (
                    <label className="mb-1 block text-xs text-muted-foreground">날짜</label>
                  )}
                  <Input
                    type="date"
                    min={today}
                    className="min-h-[44px] text-base"
                    value={row.date}
                    onChange={(e) => updateScheduleRow(index, 'date', e.target.value)}
                  />
                </div>
                <div>
                  {index === 0 && (
                    <label className="mb-1 block text-xs text-muted-foreground">시작</label>
                  )}
                  <Input
                    type="time"
                    step={300}
                    className="min-h-[44px] text-base"
                    value={row.start_time}
                    onChange={(e) => updateScheduleRow(index, 'start_time', e.target.value)}
                  />
                </div>
                <div>
                  {index === 0 && (
                    <label className="mb-1 block text-xs text-muted-foreground">종료</label>
                  )}
                  <Input
                    type="time"
                    step={300}
                    className="min-h-[44px] text-base"
                    value={row.end_time}
                    onChange={(e) => updateScheduleRow(index, 'end_time', e.target.value)}
                  />
                </div>
              </div>
              {isMultiSchedule && schedules.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="mb-0.5 size-9 shrink-0 text-muted-foreground hover:text-destructive"
                  onClick={() => removeScheduleRow(index)}
                  aria-label={`${index + 1}회차 삭제`}
                >
                  <Trash2 className="size-4" />
                </Button>
              )}
            </div>
          ))}
        </div>

        {isMultiSchedule && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-full border-dashed border-primary/40 text-primary hover:bg-primary/5"
            onClick={addScheduleRow}
          >
            <Plus className="mr-1.5 size-4" />
            일정 추가
          </Button>
        )}

        {/* Hidden inputs for react-hook-form sync */}
        <input type="hidden" {...register('date')} />
        <input type="hidden" {...register('start_time')} />
        <input type="hidden" {...register('end_time')} />

        {(errors.date || errors.start_time || errors.end_time) && (
          <p className="text-sm text-destructive">
            {errors.date?.message ||
              errors.start_time?.message ||
              errors.end_time?.message ||
              '날짜와 시간을 입력해주세요'}
          </p>
        )}
      </div>

      {/* 시급 범위 */}
      <div className="space-y-3">
        <label className="text-sm font-medium">
          시급 범위 <span className="text-destructive">*</span>
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
                  onClick={() => setRateMax(opt.value)}
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
            {errors.hourly_rate.message ?? '시급을 선택해주세요'}
          </p>
        )}
      </div>
    </div>
  );

  // =========================================================================
  // Step 3: 상세 + 인수인계
  // =========================================================================
  const renderStep3 = () => (
    <div className="space-y-5">
      {/* 세부 안내 */}
      <div className="space-y-2">
        <label htmlFor="wizard-description" className="text-sm font-medium">
          세부 안내
        </label>
        <Input
          id="wizard-description"
          placeholder="예: 오전 그룹 리포머 6명, 초급반"
          className="min-h-[44px] text-base"
          {...register('description')}
        />
        <p className="text-[11px] text-muted-foreground">
          공고 제목에 표시되는 추가 설명입니다
        </p>
      </div>

      {/* 인수인계 노트 */}
      <div className="space-y-4 rounded-xl border-2 border-primary/30 bg-primary/5 p-4">
        <div>
          <label className="text-sm font-semibold">
            인수인계 노트 <span className="text-destructive">*</span>
          </label>
          <p className="mt-0.5 text-xs text-muted-foreground">
            회원과의 신뢰를 위해 필수 작성 항목입니다.
          </p>
        </div>

        <div className="space-y-3">
          {/* 수업 주제 */}
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

          {/* 수업 진도 */}
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
              <p className="mt-1 text-sm text-destructive">
                {errors.handoff_class_sequence_info.message}
              </p>
            )}
          </div>

          {/* 수업 분위기 */}
          <div>
            <label className="text-sm font-medium">
              수업 분위기 <span className="text-destructive">*</span>
            </label>
            <div className="mt-1.5 flex flex-wrap gap-2">
              {ATMOSPHERE_OPTIONS.map((opt) => {
                const selected = watch('handoff_atmosphere_preference') === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    className={cn(
                      'min-h-[40px] rounded-lg border px-4 py-2 text-sm font-medium transition-all',
                      selected
                        ? 'border-primary bg-primary text-primary-foreground shadow-sm'
                        : 'border-border bg-background text-muted-foreground hover:border-primary/40 hover:text-foreground',
                    )}
                    onClick={() =>
                      setValue('handoff_atmosphere_preference', opt.value, {
                        shouldValidate: true,
                      })
                    }
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
            {errors.handoff_atmosphere_preference && (
              <p className="mt-1 text-sm text-destructive">
                {errors.handoff_atmosphere_preference.message}
              </p>
            )}
          </div>
        </div>

        {/* 민감 정보 (수락 후 공개) */}
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
              <p className="mt-1 text-sm text-destructive">
                {errors.handoff_equipment_notes.message}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  // =========================================================================
  // Step 4: 확인 + 등록
  // =========================================================================
  const renderStep4 = () => {
    const handoffAtmosphere = watch('handoff_atmosphere_preference');
    const handoffTopic = watch('handoff_class_topic');
    const handoffSequence = watch('handoff_class_sequence_info');
    const handoffMembers = watch('handoff_member_notes');
    const handoffEquipment = watch('handoff_equipment_notes');
    const date = watch('date');
    const startTime = watch('start_time');
    const endTime = watch('end_time');

    return (
      <div className="space-y-4">
        {/* 제목 미리보기 */}
        {titlePreview && (
          <Card className="border-primary/30 bg-primary/5">
            <CardContent className="px-4 py-3">
              <p className="text-xs font-medium text-muted-foreground">공고 제목 미리보기</p>
              <p className="mt-1 text-base font-semibold">{titlePreview}</p>
            </CardContent>
          </Card>
        )}

        {/* 요약 섹션 */}
        <div className="space-y-3">
          {/* 기본 설정 */}
          <div className="rounded-xl border border-border/60 bg-muted/10 p-3">
            <p className="mb-2 text-xs font-semibold text-muted-foreground">기본 설정</p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <span className="text-muted-foreground">종목</span>
              <span className="font-medium">{categoryLabel || '-'}</span>
              <span className="text-muted-foreground">유형</span>
              <span className="font-medium">
                {jobTypeLabel || '-'}
                {isUrgent && <span className="ml-1.5 text-xs text-urgent">(긴급)</span>}
              </span>
              <span className="text-muted-foreground">지역</span>
              <span className="font-medium">{region || '-'}</span>
            </div>
          </div>

          {/* 날짜·급여 */}
          <div className="rounded-xl border border-border/60 bg-muted/10 p-3">
            <p className="mb-2 text-xs font-semibold text-muted-foreground">날짜 및 급여</p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <span className="text-muted-foreground">날짜</span>
              <span className="font-medium">{date || '-'}</span>
              <span className="text-muted-foreground">시간</span>
              <span className="font-medium">
                {startTime && endTime ? `${startTime} ~ ${endTime}` : '-'}
              </span>
              {isMultiSchedule && schedules.length > 1 && (
                <>
                  <span className="text-muted-foreground">총 회차</span>
                  <span className="font-medium">{schedules.length}회</span>
                </>
              )}
              <span className="text-muted-foreground">시급</span>
              <span className="font-medium">
                {rateRangeText || (rateMin > 0 ? formatCurrency(rateMin) : '-')}
              </span>
            </div>
            {isMultiSchedule && schedules.length > 1 && (
              <div className="mt-2 space-y-0.5 border-t border-border/40 pt-2">
                {schedules.map((s, i) => (
                  <p key={i} className="text-xs text-muted-foreground">
                    {i + 1}회: {s.date} {s.start_time}~{s.end_time}
                  </p>
                ))}
              </div>
            )}
          </div>

          {/* 상세·인수인계 */}
          <div className="rounded-xl border border-border/60 bg-muted/10 p-3">
            <p className="mb-2 text-xs font-semibold text-muted-foreground">상세 및 인수인계</p>
            <div className="space-y-1.5 text-sm">
              {description && (
                <div className="grid grid-cols-[4rem_1fr] gap-x-2">
                  <span className="text-muted-foreground">세부 안내</span>
                  <span className="font-medium">{description}</span>
                </div>
              )}
              <div className="grid grid-cols-[4rem_1fr] gap-x-2">
                <span className="text-muted-foreground">주제</span>
                <span className="font-medium">{handoffTopic || '-'}</span>
              </div>
              <div className="grid grid-cols-[4rem_1fr] gap-x-2">
                <span className="text-muted-foreground">진도</span>
                <span className="font-medium line-clamp-2">{handoffSequence || '-'}</span>
              </div>
              <div className="grid grid-cols-[4rem_1fr] gap-x-2">
                <span className="text-muted-foreground">분위기</span>
                <span className="font-medium">{handoffAtmosphere || '-'}</span>
              </div>
              <div className="grid grid-cols-[4rem_1fr] gap-x-2">
                <span className="flex items-center gap-1 text-muted-foreground">
                  <Lock className="size-3" />
                  회원
                </span>
                <span className="font-medium line-clamp-2">{handoffMembers || '-'}</span>
              </div>
              <div className="grid grid-cols-[4rem_1fr] gap-x-2">
                <span className="flex items-center gap-1 text-muted-foreground">
                  <Lock className="size-3" />
                  기구
                </span>
                <span className="font-medium line-clamp-2">{handoffEquipment || '-'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // =========================================================================
  // Render
  // =========================================================================

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button
          size="lg"
          className="min-h-[48px] w-full text-base font-semibold"
        >
          <Plus className="mr-1.5 size-5" />
          공고 등록하기
        </Button>
      </DialogTrigger>

      <DialogContent
        showCloseButton={false}
        className={cn(
          'flex flex-col gap-0 p-0',
          'h-[100dvh] w-full max-w-full rounded-none border-0',
          'sm:h-auto sm:max-h-[85vh] sm:max-w-lg sm:rounded-lg sm:border',
        )}
      >
        {/* Header */}
        <DialogHeader className="shrink-0 border-b px-4 py-3">
          <div className="flex items-center justify-between">
            {step > 1 ? (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="min-h-[44px] gap-1 px-2 text-sm"
                onClick={goBack}
              >
                <ChevronLeft className="size-4" />
                이전
              </Button>
            ) : (
              <div />
            )}
            <DialogTitle className="font-display text-base">
              {STEP_LABELS[step - 1]}
              <span className="ml-1.5 text-xs font-normal text-muted-foreground">
                {step}/{TOTAL_STEPS}
              </span>
            </DialogTitle>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="min-h-[44px] px-2 text-sm text-muted-foreground"
              onClick={() => handleOpenChange(false)}
            >
              닫기
            </Button>
          </div>
          <ProgressBar />
        </DialogHeader>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          <form id="job-creation-form" onSubmit={handleSubmit(onSubmit)}>
            {step === 1 && renderStep1()}
            {step === 2 && renderStep2()}
            {step === 3 && renderStep3()}
            {step === 4 && renderStep4()}
          </form>
        </div>

        {/* Footer */}
        <div className="shrink-0 border-t px-4 py-3">
          {step < TOTAL_STEPS ? (
            <Button
              type="button"
              size="lg"
              className="min-h-[48px] w-full text-base font-semibold"
              onClick={goNext}
            >
              다음
            </Button>
          ) : (
            <Button
              type="submit"
              form="job-creation-form"
              size="lg"
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
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
