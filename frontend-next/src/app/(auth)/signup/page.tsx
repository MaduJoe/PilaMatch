'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { signupSchema, type SignupFormData } from '@/lib/validators';
import { useSignup } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  ToggleGroup,
  ToggleGroupItem,
} from '@/components/ui/toggle-group';

export default function SignupPage() {
  const signup = useSignup();
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      role: 'instructor',
    },
  });

  const role = watch('role');

  const onSubmit = (data: SignupFormData) => {
    signup.mutate(data);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>회원가입</CardTitle>
        <CardDescription>StudioBridge에 가입하고 시작하세요</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">이메일</Label>
            <Input
              id="email"
              type="email"
              placeholder="example@email.com"
              {...register('email')}
            />
            {errors.email && (
              <p className="text-sm text-red-500">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">비밀번호</Label>
            <Input
              id="password"
              type="password"
              placeholder="8자 이상"
              {...register('password')}
            />
            {errors.password && (
              <p className="text-sm text-red-500">{errors.password.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label>역할</Label>
            <ToggleGroup
              type="single"
              value={role}
              onValueChange={(value) => {
                if (value) setValue('role', value as 'instructor' | 'studio');
              }}
              className="justify-start"
            >
              <ToggleGroupItem value="instructor" className="flex-1">
                강사
              </ToggleGroupItem>
              <ToggleGroupItem value="studio" className="flex-1">
                스튜디오
              </ToggleGroupItem>
            </ToggleGroup>
            {errors.role && (
              <p className="text-sm text-red-500">{errors.role.message}</p>
            )}
          </div>

          {role === 'instructor' && (
            <div className="space-y-2">
              <Label htmlFor="display_name">이름</Label>
              <Input
                id="display_name"
                placeholder="홍길동"
                {...register('display_name')}
              />
              {errors.display_name && (
                <p className="text-sm text-red-500">{errors.display_name.message}</p>
              )}
            </div>
          )}

          {role === 'studio' && (
            <div className="space-y-2">
              <Label htmlFor="business_name">업체명</Label>
              <Input
                id="business_name"
                placeholder="OO필라테스"
                {...register('business_name')}
              />
              {errors.business_name && (
                <p className="text-sm text-red-500">{errors.business_name.message}</p>
              )}
            </div>
          )}
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button
            type="submit"
            className="w-full"
            disabled={signup.isPending}
          >
            {signup.isPending ? '가입 중...' : '회원가입'}
          </Button>
          <p className="text-center text-sm text-gray-500">
            이미 계정이 있으신가요?{' '}
            <Link href="/login" className="font-medium text-primary hover:underline">
              로그인
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
