'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
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
    formState: { errors, isDirty },
  } = useForm<InstructorProfileFormData>({
    resolver: zodResolver(instructorProfileSchema),
  });

  // Populate form when profile loads
  useEffect(() => {
    if (profile) {
      reset({
        display_name: profile.display_name || '',
        bio: profile.bio || '',
        categories: profile.categories || [],
        experience_years: profile.experience_years || 0,
        hourly_rate_min: profile.hourly_rate_min ?? undefined,
        hourly_rate_max: profile.hourly_rate_max ?? undefined,
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
        hourly_rate_min: data.hourly_rate_min,
        hourly_rate_max: data.hourly_rate_max,
        available_regions: data.available_regions,
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      queryClient.invalidateQueries({ queryKey: ['trustScore'] });
      if (user) {
        setUser({ ...user, display_name: variables.display_name }, useAuthStore.getState().profileId);
      }
      toast.success('프로필이 저장되었습니다');
    },
    onError: (error: Error) => {
      toast.error(`프로필 저장 실패: ${error.message}`);
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>기본 정보</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit((data) => updateProfile.mutate(data))} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="display_name">활동명 *</Label>
            <Input id="display_name" {...register('display_name')} />
            {errors.display_name && (
              <p className="text-sm text-red-500">{errors.display_name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="bio">자기소개</Label>
            <Textarea id="bio" rows={3} {...register('bio')} />
          </div>

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

          <div className="space-y-2">
            <Label>카테고리 *</Label>
            <div className="flex gap-4">
              {CATEGORIES.map((cat) => (
                <label key={cat.value} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    value={cat.value}
                    {...register('categories')}
                    defaultChecked={profile?.categories?.includes(cat.value)}
                  />
                  <span className="text-sm">{cat.label}</span>
                </label>
              ))}
            </div>
            {errors.categories && (
              <p className="text-sm text-red-500">{errors.categories.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label>활동 가능 지역 *</Label>
            <div className="flex flex-wrap gap-2">
              {REGION_NAMES.map((region) => (
                <label key={region} className="flex items-center gap-1">
                  <input
                    type="checkbox"
                    value={region}
                    {...register('available_regions')}
                    defaultChecked={profile?.available_regions?.includes(region)}
                  />
                  <span className="text-xs">{region}</span>
                </label>
              ))}
            </div>
            {errors.available_regions && (
              <p className="text-sm text-red-500">{errors.available_regions.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="hourly_rate_min">최소 희망시급</Label>
              <Input
                id="hourly_rate_min"
                type="number"
                step={5000}
                min={10000}
                {...register('hourly_rate_min', { valueAsNumber: true })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="hourly_rate_max">최대 희망시급</Label>
              <Input
                id="hourly_rate_max"
                type="number"
                step={5000}
                {...register('hourly_rate_max', { valueAsNumber: true })}
              />
            </div>
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
