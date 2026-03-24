'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  Clock,
  MapPin,
  ShieldCheck,
  Ban,
  ChevronDown,
  CheckCircle2,
  ArrowRight,
  Phone,
  Building2,
  User,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Scroll animation hook (reuse landing pattern)
// ---------------------------------------------------------------------------

function useInView(threshold = 0.1) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    if (!ref.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setInView(true);
      },
      { threshold },
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [threshold]);
  return { ref, inView };
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Role = 'studio' | 'instructor' | '';

interface SurveyAnswers {
  q1_frequency: string;
  q2_method: string;
  q3_cancelled: string;
}

interface BetaSignup {
  name: string;
  phone: string;
  role: Role;
  region: string;
}

// ---------------------------------------------------------------------------
// 1. Impact Hero — "이 경험 있으시죠?"
// ---------------------------------------------------------------------------

function ImpactHero() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <section className="auth-gradient grain-overlay relative overflow-hidden min-h-[70vh] flex items-center justify-center">
      <div className="absolute -top-24 -right-24 size-96 rounded-full bg-urgent/[0.06] blur-3xl" />
      <div className="absolute -bottom-32 -left-32 size-[28rem] rounded-full bg-primary/[0.04] blur-3xl" />

      <div
        className={cn(
          'relative z-10 max-w-2xl mx-auto px-4 text-center',
          mounted ? 'animate-fade-up' : 'opacity-0',
        )}
      >
        <Badge variant="secondary" className="mb-6 text-urgent border-urgent/20">
          <AlertTriangle className="size-3 mr-1" />
          30초 설문
        </Badge>

        <h1 className="font-display text-3xl md:text-4xl lg:text-5xl font-extrabold tracking-tight text-foreground leading-tight">
          오전 9시,
          <br />
          강사가 연락 두절.
          <br />
          <span className="text-urgent">수업은 30분 후.</span>
        </h1>

        <p className="text-lg text-muted-foreground mt-6">
          카톡방 10개 돌리고, 호호요가에 글 올리고,
          <br />
          결국 원장님이 직접 수업하신 적 있으시죠?
        </p>

        <button
          onClick={() => {
            document.getElementById('solution')?.scrollIntoView({ behavior: 'smooth' });
          }}
          className="mt-8 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          해결책 보기
          <ChevronDown className="size-4 animate-bounce" />
        </button>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// 2. Solution Section — "이런 앱이 있다면?"
// ---------------------------------------------------------------------------

function SolutionSection() {
  const { ref, inView } = useInView();

  return (
    <section id="solution" className="py-20 md:py-28 px-4">
      <div
        ref={ref}
        className={cn(
          'max-w-3xl mx-auto',
          inView ? 'animate-fade-up' : 'opacity-0',
        )}
      >
        <h2 className="font-display text-2xl md:text-3xl font-bold text-center mb-4">
          30분 내 검증된 대타 확정.
          <br />
          <span className="text-primary">그런 앱이 있다면?</span>
        </h2>
        <p className="text-center text-muted-foreground mb-12">
          PilaMatch는 호호요가 게시판이 아닙니다. 실시간 긴급 매칭 시스템입니다.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-border/60 bg-card/80">
            <CardContent className="pt-6 text-center">
              <div className="inline-flex items-center justify-center bg-primary/10 p-3 rounded-xl mb-4">
                <Clock className="size-8 text-primary" />
              </div>
              <h3 className="font-display font-bold mb-2">30초 등록</h3>
              <p className="text-sm text-muted-foreground">
                종목 · 시간 · 급여<br />3가지만 입력
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/80">
            <CardContent className="pt-6 text-center">
              <div className="inline-flex items-center justify-center bg-success/10 p-3 rounded-xl mb-4">
                <MapPin className="size-8 text-success" />
              </div>
              <h3 className="font-display font-bold mb-2">반경 5km 푸시</h3>
              <p className="text-sm text-muted-foreground">
                가까운 검증 강사에게<br />즉시 알림
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/80">
            <CardContent className="pt-6 text-center">
              <div className="inline-flex items-center justify-center bg-urgent/10 p-3 rounded-xl mb-4">
                <Phone className="size-8 text-urgent" />
              </div>
              <h3 className="font-display font-bold mb-2">원탭 수락</h3>
              <p className="text-sm text-muted-foreground">
                수락 즉시 연락처 공개<br />30분 내 확정
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center gap-3 p-3 rounded-xl bg-muted/50">
            <ShieldCheck className="size-5 text-success shrink-0" />
            <span className="text-sm">SMS 인증 + 자격증 확인 강사만</span>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-xl bg-muted/50">
            <Ban className="size-5 text-urgent shrink-0" />
            <span className="text-sm">노쇼 시 14일 정지 + Tier 강등</span>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-xl bg-muted/50">
            <MapPin className="size-5 text-primary shrink-0" />
            <span className="text-sm">GPS 거리순 자동 매칭</span>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// 3. Survey + Beta Signup — 핵심
// ---------------------------------------------------------------------------

const FREQUENCY_OPTIONS = [
  '주 1회 이상',
  '월 2-3회',
  '월 1회',
  '분기 1회 미만',
  '거의 없음',
] as const;

const METHOD_OPTIONS = [
  '카카오톡 오픈채팅',
  '호호요가 게시판',
  '지인 네트워크',
  '직접 해결 (원장이 수업)',
  '기타',
] as const;

const CANCELLED_OPTIONS = [
  '여러 번 있다',
  '1-2번 있다',
  '없다 (항상 해결)',
] as const;

const REGION_OPTIONS = [
  '서울 강남/서초/송파',
  '서울 마포/용산/종로',
  '서울 강동/성동/광진',
  '서울 기타',
  '경기 (분당/판교/수원 등)',
  '기타 지역',
] as const;

function SurveySection() {
  const { ref, inView } = useInView();
  const [step, setStep] = useState<'survey' | 'signup' | 'done'>('survey');
  const [answers, setAnswers] = useState<SurveyAnswers>({
    q1_frequency: '',
    q2_method: '',
    q3_cancelled: '',
  });
  const [signup, setSignup] = useState<BetaSignup>({
    name: '',
    phone: '',
    role: '',
    region: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const canProceedSurvey = answers.q1_frequency && answers.q2_method && answers.q3_cancelled;
  const canSubmitSignup = signup.name && signup.phone && signup.role && signup.region;

  async function handleSubmit() {
    setSubmitting(true);
    try {
      const payload = { ...answers, ...signup, submitted_at: new Date().toISOString() };
      // For now, store in localStorage until backend endpoint exists
      const existing = JSON.parse(localStorage.getItem('pilamatch_surveys') || '[]');
      existing.push(payload);
      localStorage.setItem('pilamatch_surveys', JSON.stringify(existing));
      setStep('done');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section id="survey" className="py-20 md:py-28 px-4 bg-muted/30">
      <div
        ref={ref}
        className={cn(
          'max-w-2xl mx-auto',
          inView ? 'animate-fade-up' : 'opacity-0',
        )}
      >
        {step === 'survey' && (
          <>
            <h2 className="font-display text-2xl md:text-3xl font-bold text-center mb-2">
              30초 설문
            </h2>
            <p className="text-center text-muted-foreground mb-10">
              3개 질문에 답하시면 베타 초대를 보내드립니다
            </p>

            <div className="space-y-8">
              {/* Q1 */}
              <div className="space-y-3">
                <Label className="text-base font-bold">
                  1. 당일 긴급 대타가 얼마나 자주 필요한가요?
                </Label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {FREQUENCY_OPTIONS.map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => setAnswers((a) => ({ ...a, q1_frequency: opt }))}
                      className={cn(
                        'px-4 py-3 rounded-xl text-sm text-left transition-all border',
                        answers.q1_frequency === opt
                          ? 'border-primary bg-primary/10 text-foreground font-medium'
                          : 'border-border bg-card hover:border-primary/40',
                      )}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>

              {/* Q2 */}
              <div className="space-y-3">
                <Label className="text-base font-bold">
                  2. 지금은 대타를 어떻게 구하세요?
                </Label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {METHOD_OPTIONS.map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => setAnswers((a) => ({ ...a, q2_method: opt }))}
                      className={cn(
                        'px-4 py-3 rounded-xl text-sm text-left transition-all border',
                        answers.q2_method === opt
                          ? 'border-primary bg-primary/10 text-foreground font-medium'
                          : 'border-border bg-card hover:border-primary/40',
                      )}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>

              {/* Q3 */}
              <div className="space-y-3">
                <Label className="text-base font-bold">
                  3. 대타를 못 구해서 수업을 취소한 적 있나요?
                </Label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {CANCELLED_OPTIONS.map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => setAnswers((a) => ({ ...a, q3_cancelled: opt }))}
                      className={cn(
                        'px-4 py-3 rounded-xl text-sm text-left transition-all border',
                        answers.q3_cancelled === opt
                          ? 'border-primary bg-primary/10 text-foreground font-medium'
                          : 'border-border bg-card hover:border-primary/40',
                      )}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <Button
              size="lg"
              className="w-full mt-10"
              disabled={!canProceedSurvey}
              onClick={() => {
                setStep('signup');
                setTimeout(() => {
                  document.getElementById('signup-form')?.scrollIntoView({ behavior: 'smooth' });
                }, 100);
              }}
            >
              다음: 베타 신청하기
              <ArrowRight className="size-4" />
            </Button>
          </>
        )}

        {step === 'signup' && (
          <div id="signup-form">
            <h2 className="font-display text-2xl md:text-3xl font-bold text-center mb-2">
              베타 테스트 신청
            </h2>
            <p className="text-center text-muted-foreground mb-10">
              출시 시 가장 먼저 초대해드립니다
            </p>

            <div className="space-y-6">
              {/* Role */}
              <div className="space-y-3">
                <Label className="text-base font-bold">어떤 분이세요?</Label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setSignup((s) => ({ ...s, role: 'studio' }))}
                    className={cn(
                      'flex flex-col items-center gap-3 p-6 rounded-2xl border transition-all',
                      signup.role === 'studio'
                        ? 'border-primary bg-primary/10'
                        : 'border-border bg-card hover:border-primary/40',
                    )}
                  >
                    <Building2
                      className={cn(
                        'size-10',
                        signup.role === 'studio' ? 'text-primary' : 'text-muted-foreground',
                      )}
                    />
                    <span className="font-bold">센터 원장</span>
                    <span className="text-xs text-muted-foreground">대타 강사를 구합니다</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSignup((s) => ({ ...s, role: 'instructor' }))}
                    className={cn(
                      'flex flex-col items-center gap-3 p-6 rounded-2xl border transition-all',
                      signup.role === 'instructor'
                        ? 'border-primary bg-primary/10'
                        : 'border-border bg-card hover:border-primary/40',
                    )}
                  >
                    <User
                      className={cn(
                        'size-10',
                        signup.role === 'instructor' ? 'text-primary' : 'text-muted-foreground',
                      )}
                    />
                    <span className="font-bold">프리랜서 강사</span>
                    <span className="text-xs text-muted-foreground">대타 알림을 받고 싶습니다</span>
                  </button>
                </div>
              </div>

              {/* Name */}
              <div className="space-y-2">
                <Label htmlFor="name" className="text-base font-bold">
                  이름 (또는 닉네임)
                </Label>
                <Input
                  id="name"
                  placeholder="홍길동"
                  value={signup.name}
                  onChange={(e) => setSignup((s) => ({ ...s, name: e.target.value }))}
                />
              </div>

              {/* Phone */}
              <div className="space-y-2">
                <Label htmlFor="phone" className="text-base font-bold">
                  연락처
                </Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="010-1234-5678"
                  value={signup.phone}
                  onChange={(e) => setSignup((s) => ({ ...s, phone: e.target.value }))}
                />
                <p className="text-xs text-muted-foreground">
                  베타 초대 알림 전송용으로만 사용됩니다
                </p>
              </div>

              {/* Region */}
              <div className="space-y-3">
                <Label className="text-base font-bold">주로 활동하는 지역</Label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {REGION_OPTIONS.map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => setSignup((s) => ({ ...s, region: opt }))}
                      className={cn(
                        'px-4 py-3 rounded-xl text-sm text-left transition-all border',
                        signup.region === opt
                          ? 'border-primary bg-primary/10 text-foreground font-medium'
                          : 'border-border bg-card hover:border-primary/40',
                      )}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-10">
              <Button
                variant="outline"
                size="lg"
                className="flex-1"
                onClick={() => setStep('survey')}
              >
                이전
              </Button>
              <Button
                size="lg"
                className="flex-1"
                disabled={!canSubmitSignup || submitting}
                onClick={handleSubmit}
              >
                {submitting ? '제출 중...' : '베타 신청 완료'}
                {!submitting && <CheckCircle2 className="size-4" />}
              </Button>
            </div>
          </div>
        )}

        {step === 'done' && (
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center bg-success/10 p-4 rounded-full mb-6">
              <CheckCircle2 className="size-12 text-success" />
            </div>
            <h2 className="font-display text-2xl md:text-3xl font-bold mb-4">
              감사합니다!
            </h2>
            <p className="text-muted-foreground mb-2">
              베타 출시 시 가장 먼저 연락드리겠습니다.
            </p>
            <p className="text-sm text-muted-foreground mb-8">
              주변에 같은 고민을 가진 원장님이나 강사님이 계시다면<br />
              이 페이지를 공유해주세요!
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button variant="outline" asChild>
                <Link href="/">PilaMatch 더 알아보기</Link>
              </Button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// 4. Mini Footer
// ---------------------------------------------------------------------------

function SurveyFooter() {
  return (
    <footer className="border-t border-border/40 py-6 px-4">
      <div className="max-w-2xl mx-auto flex flex-col items-center gap-3">
        <Link href="/" className="font-display text-lg font-bold">
          <span className="text-primary">Pila</span>
          <span className="text-foreground">Match</span>
        </Link>
        <p className="text-xs text-muted-foreground/60">
          &copy; 2026 PilaMatch. All rights reserved.
        </p>
      </div>
    </footer>
  );
}

// ---------------------------------------------------------------------------
// Composed Survey Page
// ---------------------------------------------------------------------------

export function SurveyPage() {
  return (
    <div className="min-h-screen bg-background">
      <ImpactHero />
      <SolutionSection />
      <SurveySection />
      <SurveyFooter />
    </div>
  );
}
