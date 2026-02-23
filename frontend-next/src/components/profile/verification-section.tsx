'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api-client';
import { APIError } from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, AlertCircle, Phone, Building2 } from 'lucide-react';

export function VerificationSection() {
  const { user, setUser } = useAuthStore();
  const queryClient = useQueryClient();
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [bizNumber, setBizNumber] = useState('');

  const requestOtp = useMutation({
    mutationFn: (phoneNum: string) => api.verification.requestPhone(phoneNum),
    onSuccess: (data: { message: string; _dev_otp?: string }) => {
      setOtpSent(true);
      if (data._dev_otp) {
        setDevOtp(data._dev_otp);
        toast.info(`인증번호가 발송되었습니다. (개발모드: ${data._dev_otp})`);
      } else {
        toast.success('인증번호가 발송되었습니다');
      }
    },
    onError: (error: Error) => {
      toast.error(error instanceof APIError ? error.message : '인증번호 발송 실패');
    },
  });

  const verifyOtp = useMutation({
    mutationFn: () => api.verification.verifyPhone(phone, otp),
    onSuccess: async () => {
      toast.success('휴대폰 인증 완료!');
      setOtpSent(false);
      setDevOtp(null);
      // Refresh user data
      const me = await api.auth.me();
      setUser(me.user, me.profile_id ?? null);
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
    },
    onError: (error: Error) => {
      toast.error(error instanceof APIError ? error.message : '인증 실패');
    },
  });

  const verifyBusiness = useMutation({
    mutationFn: (number: string) => api.verification.verifyBusiness(number),
    onSuccess: async () => {
      toast.success('사업자 인증 완료!');
      const me = await api.auth.me();
      setUser(me.user, me.profile_id ?? null);
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
    },
    onError: (error: Error) => {
      toast.error(error instanceof APIError ? error.message : '사업자 인증 실패');
    },
  });

  if (!user) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">본인인증</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Phone Verification */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Phone className="h-4 w-4" aria-hidden="true" />
            <span className="text-sm font-medium">휴대폰 인증</span>
            {user.phone_verified || user.identity_verified ? (
              <Badge variant="default" className="bg-green-100 text-green-800">
                <CheckCircle2 className="mr-1 h-3 w-3" aria-hidden="true" />
                완료
              </Badge>
            ) : (
              <Badge variant="destructive" className="bg-yellow-100 text-yellow-800">
                <AlertCircle className="mr-1 h-3 w-3" aria-hidden="true" />
                필요
              </Badge>
            )}
          </div>

          {!(user.phone_verified || user.identity_verified) && (
            <div className="space-y-3">
              {!otpSent ? (
                <div className="flex gap-2">
                  <Input
                    placeholder="01012345678"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    aria-label="휴대폰 번호"
                    className="min-h-[44px]"
                  />
                  <Button
                    onClick={() => requestOtp.mutate(phone)}
                    disabled={requestOtp.isPending || phone.length < 10}
                    size="sm"
                    className="min-h-[44px] min-w-[44px] shrink-0"
                  >
                    {requestOtp.isPending ? '발송 중...' : '인증번호 발송'}
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {devOtp && (
                    <p className="text-xs text-blue-600">
                      개발모드 인증번호: {devOtp}
                    </p>
                  )}
                  <div className="flex gap-2">
                    <Input
                      placeholder="인증번호 6자리"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value)}
                      maxLength={6}
                      aria-label="인증번호"
                      className="min-h-[44px]"
                    />
                    <Button
                      onClick={() => verifyOtp.mutate()}
                      disabled={verifyOtp.isPending || otp.length !== 6}
                      size="sm"
                      className="min-h-[44px] min-w-[44px] shrink-0"
                    >
                      {verifyOtp.isPending ? '확인 중...' : '확인'}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Business Verification (Studio only) */}
        {user.role === 'studio' && (
          <>
            <div className="border-t pt-4" />
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4" aria-hidden="true" />
                <span className="text-sm font-medium">사업자 인증</span>
                {user.business_verified ? (
                  <Badge variant="default" className="bg-green-100 text-green-800">
                    <CheckCircle2 className="mr-1 h-3 w-3" aria-hidden="true" />
                    완료
                  </Badge>
                ) : (
                  <Badge variant="destructive" className="bg-yellow-100 text-yellow-800">
                    <AlertCircle className="mr-1 h-3 w-3" aria-hidden="true" />
                    필요
                  </Badge>
                )}
              </div>

              {!user.business_verified && (
                <div className="flex gap-2">
                  <Input
                    placeholder="000-00-00000"
                    value={bizNumber}
                    onChange={(e) => setBizNumber(e.target.value)}
                    aria-label="사업자 등록번호"
                    className="min-h-[44px]"
                  />
                  <Button
                    onClick={() =>
                      verifyBusiness.mutate(bizNumber.replace(/-/g, ''))
                    }
                    disabled={
                      verifyBusiness.isPending ||
                      bizNumber.replace(/-/g, '').length !== 10
                    }
                    size="sm"
                    className="min-h-[44px] min-w-[44px] shrink-0"
                  >
                    {verifyBusiness.isPending ? '인증 중...' : '인증'}
                  </Button>
                </div>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
