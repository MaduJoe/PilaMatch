'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api-client';
import { studioProfileSchema, type StudioProfileFormData } from '@/lib/validators';
import { useAuthStore } from '@/stores/auth-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CATEGORIES, REGION_NAMES } from '@/lib/constants';

export function StudioProfileForm() {
  const queryClient = useQueryClient();
  const { user, setUser } = useAuthStore();

  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile', 'studio'],
    queryFn: () => api.studios.getMyProfile(),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<StudioProfileFormData>({
    resolver: zodResolver(studioProfileSchema),
  });

  useEffect(() => {
    if (profile) {
      reset({
        business_name: profile.business_name || '',
        description: profile.description || '',
        phone: profile.phone || '',
        address: profile.address || '',
        region: profile.region || '',
        categories: profile.categories || [],
      });
    }
  }, [profile, reset]);

  const updateProfile = useMutation({
    mutationFn: (data: StudioProfileFormData) =>
      api.studios.updateMyProfile({
        business_name: data.business_name,
        description: data.description,
        phone: data.phone,
        address: data.address,
        region: data.region,
        categories: data.categories,
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      queryClient.invalidateQueries({ queryKey: ['tier'] });
      if (user) {
        setUser({ ...user, business_name: variables.business_name }, useAuthStore.getState().profileId);
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
            <Label htmlFor="business_name">스튜디오명 *</Label>
            <Input id="business_name" {...register('business_name')} />
            {errors.business_name && (
              <p className="text-sm text-red-500">{errors.business_name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">소개</Label>
            <Textarea id="description" rows={3} {...register('description')} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">전화번호</Label>
            <Input id="phone" {...register('phone')} placeholder="02-1234-5678" />
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
            <Label htmlFor="region">지역</Label>
            <select
              id="region"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              {...register('region')}
            >
              <option value="">지역 선택</option>
              {REGION_NAMES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="address">주소</Label>
            <Input id="address" {...register('address')} placeholder="서울시 강남구..." />
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
