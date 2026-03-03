'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { signupSchema, type SignupFormData } from '@/lib/validators';
import { useSignup } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { User, Building2 } from 'lucide-react';
import { cn } from '@/lib/utils';

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
      terms_agreed: false as unknown as true,
      privacy_agreed: false as unknown as true,
    },
  });

  const role = watch('role');
  const termsAgreed = watch('terms_agreed');
  const privacyAgreed = watch('privacy_agreed');
  const allAgreed = termsAgreed === true && privacyAgreed === true;

  const handleAllAgree = (checked: boolean) => {
    setValue('terms_agreed', checked as unknown as true, { shouldValidate: true });
    setValue('privacy_agreed', checked as unknown as true, { shouldValidate: true });
  };

  const onSubmit = (data: SignupFormData) => {
    signup.mutate(data);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-center text-xl font-bold">시작하기</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Step 1: Role selection - compact pill */}
        <div className="space-y-2">
          <Label className="text-sm font-medium text-muted-foreground">어떤 분이신가요?</Label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setValue('role', 'instructor')}
              className={cn(
                'flex items-center justify-center gap-2 rounded-xl border-2 p-3 transition-all',
                'hover:border-primary/50 hover:bg-primary/5',
                role === 'instructor'
                  ? 'border-primary bg-primary/10 shadow-sm'
                  : 'border-muted',
              )}
              aria-pressed={role === 'instructor'}
            >
              <div className={cn(
                'flex size-8 items-center justify-center rounded-full',
                role === 'instructor' ? 'bg-primary text-primary-foreground' : 'bg-muted',
              )}>
                <User className="size-4" aria-hidden="true" />
              </div>
              <span className={cn(
                'text-sm font-semibold',
                role === 'instructor' ? 'text-primary' : 'text-muted-foreground',
              )}>
                강사
              </span>
            </button>

            <button
              type="button"
              onClick={() => setValue('role', 'studio')}
              className={cn(
                'flex items-center justify-center gap-2 rounded-xl border-2 p-3 transition-all',
                'hover:border-primary/50 hover:bg-primary/5',
                role === 'studio'
                  ? 'border-primary bg-primary/10 shadow-sm'
                  : 'border-muted',
              )}
              aria-pressed={role === 'studio'}
            >
              <div className={cn(
                'flex size-8 items-center justify-center rounded-full',
                role === 'studio' ? 'bg-primary text-primary-foreground' : 'bg-muted',
              )}>
                <Building2 className="size-4" aria-hidden="true" />
              </div>
              <span className={cn(
                'text-sm font-semibold',
                role === 'studio' ? 'text-primary' : 'text-muted-foreground',
              )}>
                스튜디오
              </span>
            </button>
          </div>
          {errors.role && (
            <p className="text-sm text-destructive">{errors.role.message}</p>
          )}
        </div>

        {/* Step 2: Credentials */}
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="email" className="text-sm">이메일</Label>
            <Input
              id="email"
              type="email"
              placeholder="example@email.com"
              autoFocus
              className="min-h-[48px] rounded-xl"
              {...register('email')}
            />
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="password" className="text-sm">비밀번호</Label>
            <Input
              id="password"
              type="password"
              placeholder="8자 이상"
              className="min-h-[48px] rounded-xl"
              {...register('password')}
            />
            {errors.password && (
              <p className="text-xs text-destructive">{errors.password.message}</p>
            )}
          </div>

          {/* Name field - role-dependent */}
          <div className="space-y-1.5">
            <Label htmlFor={role === 'instructor' ? 'display_name' : 'business_name'} className="text-sm">
              {role === 'instructor' ? '이름' : '업체명'}
            </Label>
            {role === 'instructor' ? (
              <Input
                id="display_name"
                placeholder="홍길동"
                className="min-h-[48px] rounded-xl"
                {...register('display_name')}
              />
            ) : (
              <Input
                id="business_name"
                placeholder="OO필라테스"
                className="min-h-[48px] rounded-xl"
                {...register('business_name')}
              />
            )}
            {errors.display_name && (
              <p className="text-xs text-destructive">{errors.display_name.message}</p>
            )}
            {errors.business_name && (
              <p className="text-xs text-destructive">{errors.business_name.message}</p>
            )}
          </div>
        </div>

        {/* Step 3: Terms - simplified */}
        <div className="space-y-2.5 rounded-xl border bg-muted/30 p-3">
          <label className="flex cursor-pointer items-center gap-2.5">
            <Checkbox
              id="agree-all"
              checked={allAgreed}
              onCheckedChange={(checked) => handleAllAgree(checked === true)}
            />
            <span className="text-sm font-semibold">전체 동의하고 시작하기</span>
          </label>
          <div className="flex gap-3 pl-7 text-xs text-muted-foreground">
            <Link href="/terms" target="_blank" className="underline underline-offset-2 hover:text-foreground">
              이용약관
            </Link>
            <Link href="/privacy" target="_blank" className="underline underline-offset-2 hover:text-foreground">
              개인정보 처리방침
            </Link>
          </div>
        </div>

        <div className="flex flex-col gap-3 pt-1">
          <Button
            type="submit"
            className="w-full min-h-[48px] rounded-xl text-base font-bold"
            disabled={signup.isPending || !allAgreed}
          >
            {signup.isPending ? '가입 중...' : '가입하기'}
          </Button>
          <p className="text-center text-xs text-muted-foreground">
            이미 계정이 있으신가요?{' '}
            <Link href="/login" className="font-medium text-primary hover:underline">
              로그인
            </Link>
          </p>
        </div>
      </form>
    </div>
  );
}
