'use client';

import { useEffect, useState, useCallback } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api-client';
import { instructorProfileSchema, type InstructorProfileFormData } from '@/lib/validators';
import { useAuthStore } from '@/stores/auth-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { REGION_NAMES, CATEGORIES } from '@/lib/constants';
import { Check } from 'lucide-react';

const BIO_SAMPLES = [
  '안녕하세요! 필라테스/요가 전문 강사입니다.\n체형 교정과 코어 강화에 특화되어 있으며,\n회원님의 컨디션에 맞춘 1:1 맞춤 수업을 진행합니다.',
  '안녕하세요! 다양한 스튜디오 경험을 바탕으로\n그룹 및 개인 레슨 모두 능숙하게 진행합니다.\n밝고 에너지 넘치는 수업 분위기를 만들어갑니다.',
] as const;

/** Group Seoul districts by area for easier selection */
const REGION_GROUPS: Record<string, string[]> = {
  '강남권': ['강남구', '서초구', '송파구', '강동구'],
  '마용성': ['마포구', '용산구', '성동구'],
  '동북권': ['광진구', '동대문구', '중랑구', '성북구', '강북구', '도봉구', '노원구'],
  '서북권': ['은평구', '서대문구', '종로구', '중구'],
  '서남권': ['영등포구', '동작구', '관악구', '금천구', '구로구', '양천구', '강서구'],
};

export function InstructorProfileForm() {
  const queryClient = useQueryClient();
  const { user, setUser } = useAuthStore();

  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile', 'instructor'],
    queryFn: () => api.instructors.getMyProfile(),
  });

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    control,
    formState: { errors, isDirty },
  } = useForm<InstructorProfileFormData>({
    resolver: zodResolver(instructorProfileSchema),
  });

  const selectedRegions = useWatch({ control, name: 'available_regions' }) ?? [];

  // Populate form when profile loads
  useEffect(() => {
    if (profile) {
      reset({
        display_name: profile.display_name || '',
        bio: profile.bio || '',
        categories: profile.categories || [],
        experience_years: profile.experience_years || 0,
        available_regions: profile.available_regions || [],
      });
    }
  }, [profile, reset]);

  const updateProfile = useMutation({
    mutationFn: (data: InstructorProfileFormData) => {
      return api.instructors.updateMyProfile({
        display_name: data.display_name,
        bio: data.bio,
        categories: data.categories,
        experience_years: data.experience_years,
        available_regions: data.available_regions,
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      queryClient.invalidateQueries({ queryKey: ['tier'] });
      if (user) {
        setUser({ ...user, display_name: variables.display_name }, useAuthStore.getState().profileId);
      }
      toast.success('프로필이 저장되었습니다');
    },
    onError: (error: Error) => {
      toast.error(`프로필 저장 실패: ${error.message}`);
    },
  });

  const allSelected = REGION_NAMES.every((r) => selectedRegions.includes(r));

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      setValue('available_regions', [], { shouldDirty: true });
    } else {
      setValue('available_regions', [...REGION_NAMES], { shouldDirty: true });
    }
  }, [allSelected, setValue]);

  const handleGroupToggle = useCallback(
    (groupRegions: string[]) => {
      const allGroupSelected = groupRegions.every((r) => selectedRegions.includes(r));
      if (allGroupSelected) {
        setValue(
          'available_regions',
          selectedRegions.filter((r) => !groupRegions.includes(r)),
          { shouldDirty: true },
        );
      } else {
        const merged = Array.from(new Set([...selectedRegions, ...groupRegions]));
        setValue('available_regions', merged, { shouldDirty: true });
      }
    },
    [selectedRegions, setValue],
  );

  const handleRegionToggle = useCallback(
    (region: string) => {
      if (selectedRegions.includes(region)) {
        setValue(
          'available_regions',
          selectedRegions.filter((r) => r !== region),
          { shouldDirty: true },
        );
      } else {
        setValue('available_regions', [...selectedRegions, region], { shouldDirty: true });
      }
    },
    [selectedRegions, setValue],
  );

  const [bioExpanded, setBioExpanded] = useState(false);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>기본 정보</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit((data) => updateProfile.mutate(data))} className="space-y-5">
          {/* 활동명 */}
          <div className="space-y-2">
            <Label htmlFor="display_name">
              활동명 <span className="text-red-500">*</span>
            </Label>
            <Input
              id="display_name"
              placeholder="수업에서 사용할 이름을 입력하세요"
              {...register('display_name')}
            />
            {errors.display_name && (
              <p className="text-sm text-red-500">{errors.display_name.message}</p>
            )}
          </div>

          {/* 자기소개 */}
          <div className="space-y-2">
            <Label htmlFor="bio">
              자기소개 <span className="text-red-500">*</span>
              <span className="ml-1 text-xs font-normal text-muted-foreground">(최소 3줄)</span>
            </Label>
            <Textarea
              id="bio"
              rows={5}
              placeholder="강사님을 소개해주세요 (최소 3줄 이상)"
              {...register('bio')}
            />
            {errors.bio && (
              <p className="text-sm text-red-500">{errors.bio.message}</p>
            )}

            {/* Bio sample buttons */}
            {!bioExpanded ? (
              <button
                type="button"
                className="text-xs text-primary hover:underline underline-offset-2"
                onClick={() => setBioExpanded(true)}
              >
                샘플 문구 보기 ↓
              </button>
            ) : (
              <div className="space-y-2 rounded-xl border border-border/60 bg-muted/30 p-3">
                <p className="text-xs font-medium text-muted-foreground mb-2">샘플 문구 (클릭하면 자동 입력)</p>
                {BIO_SAMPLES.map((sample, i) => (
                  <button
                    key={i}
                    type="button"
                    className="block w-full rounded-lg border border-border/40 bg-background p-2.5 text-left text-xs leading-relaxed text-muted-foreground transition-colors hover:border-primary/40 hover:bg-primary/5"
                    onClick={() => {
                      setValue('bio', sample, { shouldDirty: true });
                      setBioExpanded(false);
                    }}
                  >
                    {sample}
                  </button>
                ))}
                <button
                  type="button"
                  className="text-xs text-muted-foreground hover:underline underline-offset-2"
                  onClick={() => setBioExpanded(false)}
                >
                  닫기 ↑
                </button>
              </div>
            )}
          </div>

          {/* 경력 */}
          <div className="space-y-2">
            <Label htmlFor="experience_years">경력 (년)</Label>
            <Input
              id="experience_years"
              type="number"
              min={0}
              {...register('experience_years', { valueAsNumber: true })}
            />
            {errors.experience_years && (
              <p className="text-sm text-red-500">{errors.experience_years.message}</p>
            )}
          </div>

          {/* 카테고리 */}
          <div className="space-y-2">
            <Label>
              카테고리 <span className="text-red-500">*</span>
            </Label>
            <div className="flex gap-3">
              {CATEGORIES.map((cat) => (
                <label key={cat.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    value={cat.value}
                    {...register('categories')}
                    defaultChecked={profile?.categories?.includes(cat.value)}
                    className="accent-primary"
                  />
                  <span className="text-sm">{cat.label}</span>
                </label>
              ))}
            </div>
            {errors.categories && (
              <p className="text-sm text-red-500">{errors.categories.message}</p>
            )}
          </div>

          {/* 활동 가능 지역 */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>
                활동 가능 지역 <span className="text-red-500">*</span>
              </Label>
              <span className="text-xs text-muted-foreground">
                {selectedRegions.length}개 선택
              </span>
            </div>

            {/* 서울전체 toggle */}
            <Button
              type="button"
              variant={allSelected ? 'default' : 'outline'}
              size="sm"
              className="w-full"
              onClick={handleSelectAll}
            >
              {allSelected ? (
                <>
                  <Check className="mr-1.5 size-4" />
                  서울 전체 선택됨
                </>
              ) : (
                '서울 전체 선택'
              )}
            </Button>

            {/* Grouped regions */}
            <div className="space-y-3 rounded-xl border border-border/60 bg-muted/20 p-3">
              {Object.entries(REGION_GROUPS).map(([groupName, groupRegions]) => {
                const groupAllSelected = groupRegions.every((r) => selectedRegions.includes(r));
                const groupSomeSelected = groupRegions.some((r) => selectedRegions.includes(r));
                return (
                  <div key={groupName}>
                    <button
                      type="button"
                      className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-foreground/80 hover:text-primary transition-colors"
                      onClick={() => handleGroupToggle(groupRegions)}
                    >
                      <span
                        className={`flex size-4 items-center justify-center rounded border text-[10px] transition-colors ${
                          groupAllSelected
                            ? 'border-primary bg-primary text-primary-foreground'
                            : groupSomeSelected
                              ? 'border-primary/50 bg-primary/10'
                              : 'border-border'
                        }`}
                      >
                        {groupAllSelected && '✓'}
                      </span>
                      {groupName}
                    </button>
                    <div className="flex flex-wrap gap-1.5 pl-5">
                      {groupRegions.map((region) => {
                        const isSelected = selectedRegions.includes(region);
                        return (
                          <button
                            key={region}
                            type="button"
                            className={`rounded-lg px-2.5 py-1 text-xs transition-all ${
                              isSelected
                                ? 'bg-primary text-primary-foreground shadow-sm'
                                : 'bg-background border border-border/60 text-muted-foreground hover:border-primary/40'
                            }`}
                            onClick={() => handleRegionToggle(region)}
                          >
                            {region}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* hidden inputs for react-hook-form */}
            <input type="hidden" {...register('available_regions')} />
            {errors.available_regions && (
              <p className="text-sm text-red-500">{errors.available_regions.message}</p>
            )}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={updateProfile.isPending || !isDirty}
          >
            {updateProfile.isPending ? '저장 중...' : '저장'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
