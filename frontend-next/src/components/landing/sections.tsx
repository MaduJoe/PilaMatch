'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  UserX,
  ScrollText,
  ClipboardX,
  Megaphone,
  Users,
  PhoneCall,
  ChevronRight,
  ShieldCheck,
  FileText,
  Ban,
  Shield,
  CreditCard,
  Award,
  Building2,
  User,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Custom hook: IntersectionObserver scroll animation
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
// 1. LandingHeader
// ---------------------------------------------------------------------------

function LandingHeader() {
  return (
    <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border/40">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="font-display text-xl font-bold">
          <span className="text-primary">Pila</span>
          <span className="text-foreground">Match</span>
        </Link>
        <div className="flex items-center gap-2">
          <Button variant="ghost" asChild>
            <Link href="/login">로그인</Link>
          </Button>
          <Button asChild>
            <Link href="/signup">시작하기</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}

// ---------------------------------------------------------------------------
// 2. Hero
// ---------------------------------------------------------------------------

function Hero() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <section className="auth-gradient grain-overlay relative overflow-hidden min-h-[85vh] flex items-center justify-center">
      {/* Decorative blurred shapes */}
      <div className="absolute -top-24 -right-24 size-96 rounded-full bg-primary/[0.04] blur-3xl" />
      <div className="absolute -bottom-32 -left-32 size-[28rem] rounded-full bg-success/[0.04] blur-3xl" />
      <div className="absolute top-1/3 right-1/4 size-64 rounded-full bg-urgent/[0.03] blur-3xl" />

      <div
        className={cn(
          'relative z-10 max-w-3xl mx-auto px-4 text-center',
          mounted ? 'animate-fade-up' : 'opacity-0',
        )}
      >
        <Badge variant="secondary" className="mb-6">
          대강 · 대타 60분 내 확정
        </Badge>

        <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight text-foreground">
          오늘 결원,
          <br />
          오늘 확정.
        </h1>

        <p className="text-lg md:text-xl text-muted-foreground mt-6">
          검증된 강사를 60분 내에 매칭합니다.
          <br />
          노쇼 방지 · 인수인계 노트 · Tier 시스템
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center mt-10">
          <Button size="lg" asChild>
            <Link href="/signup">
              무료로 공고 등록하기
              <ArrowRight className="size-4" />
            </Link>
          </Button>
          <Button variant="outline" size="lg" asChild>
            <Link href="/signup">강사로 시작하기</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// 3. Pain Points
// ---------------------------------------------------------------------------

const PAIN_POINTS = [
  {
    icon: UserX,
    title: '오전 9시 결근 통보',
    description:
      '카톡방 10개 돌리고, 결국 못 구해서 원장님이 직접 수업',
  },
  {
    icon: ScrollText,
    title: '끝없는 게시판 스크롤',
    description:
      '검증 안 된 공고 수백 개에서 진짜를 찾느라 시간 낭비',
  },
  {
    icon: ClipboardX,
    title: '인수인계 없는 대타',
    description:
      '회원 이름도 모르고, 주의사항 없이 수업 시작',
  },
] as const;

function PainPoints() {
  const { ref, inView } = useInView();

  return (
    <section className="py-20 md:py-28 px-4">
      <div
        ref={ref}
        className={cn(
          'max-w-5xl mx-auto',
          inView ? 'animate-fade-up' : 'opacity-0',
        )}
      >
        <h2 className="font-display text-2xl md:text-3xl font-bold text-center mb-12">
          이런 경험 있으시죠?
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PAIN_POINTS.map((item) => (
            <div
              key={item.title}
              className="surface-elevated rounded-2xl p-6"
            >
              <item.icon className="size-10 text-urgent mb-4" />
              <h3 className="font-display text-lg font-bold mb-2">
                {item.title}
              </h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// 4. How It Works
// ---------------------------------------------------------------------------

const STEPS = [
  {
    num: '01',
    icon: Megaphone,
    title: '공고 등록',
    description:
      '시간·급여·구를 입력하면 검증 강사에게 즉시 알림',
  },
  {
    num: '02',
    icon: Users,
    title: '강사 매칭',
    description:
      '거리·경력·자격 기반 점수로 최적 강사 자동 추천',
  },
  {
    num: '03',
    icon: PhoneCall,
    title: '확정 & 연결',
    description:
      '수락 즉시 연락처 공개 — 직접 전화로 확정',
  },
] as const;

function HowItWorks() {
  const { ref, inView } = useInView();

  return (
    <section className="py-20 md:py-28 px-4 bg-muted/30">
      <div
        ref={ref}
        className={cn(
          'max-w-5xl mx-auto',
          inView ? 'animate-fade-up' : 'opacity-0',
        )}
      >
        <h2 className="font-display text-2xl md:text-3xl font-bold text-center mb-12">
          3단계면 끝
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-[1fr,auto,1fr,auto,1fr] gap-4 md:gap-2 items-start">
          {STEPS.map((step, idx) => (
            <div key={step.num} className="contents">
              <div className="text-center">
                <div className="inline-flex items-center justify-center bg-primary/10 p-3 rounded-xl mb-4">
                  <step.icon className="size-8 text-primary" />
                </div>
                <p className="text-xs font-bold text-muted-foreground mb-1 tracking-widest">
                  {step.num}
                </p>
                <h3 className="font-display text-lg font-bold mb-2">
                  {step.title}
                </h3>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {step.description}
                </p>
              </div>

              {idx < STEPS.length - 1 && (
                <div className="hidden md:flex items-center justify-center pt-6 text-muted-foreground/40">
                  <ChevronRight className="size-6" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// 5. Differentiators
// ---------------------------------------------------------------------------

const DIFFERENTIATORS = [
  {
    icon: ShieldCheck,
    color: 'text-success',
    title: '검증된 강사만',
    description:
      '신원 인증 + 자격증 확인을 거친 Tier 등급 강사만 매칭됩니다',
  },
  {
    icon: FileText,
    color: 'text-primary',
    title: '인수인계 노트',
    description:
      '수업 주제·진도·회원 주의사항까지 — 첫 대타도 단골처럼',
  },
  {
    icon: Ban,
    color: 'text-urgent',
    title: '노쇼 방지 시스템',
    description:
      '노쇼 시 14일 정지 + Tier 강등. 같은 실수는 반복되지 않습니다',
  },
] as const;

function Differentiators() {
  const { ref, inView } = useInView();

  return (
    <section className="py-20 md:py-28 px-4">
      <div
        ref={ref}
        className={cn(
          'max-w-5xl mx-auto',
          inView ? 'animate-fade-up' : 'opacity-0',
        )}
      >
        <h2 className="font-display text-2xl md:text-3xl font-bold text-center mb-12">
          왜 PilaMatch인가요?
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {DIFFERENTIATORS.map((item) => (
            <Card
              key={item.title}
              className="border-border/60 bg-card/80"
            >
              <CardContent className="pt-6">
                <item.icon className={cn('size-10 mb-4', item.color)} />
                <h3 className="font-display text-lg font-bold mb-2">
                  {item.title}
                </h3>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {item.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// 6. Trust Signals
// ---------------------------------------------------------------------------

const TRUST_ITEMS = [
  {
    icon: Shield,
    title: 'Tier 등급 시스템',
    description:
      '실적 기반 자동 등급 — Basic → Verified → Pro',
  },
  {
    icon: CreditCard,
    title: '직접 정산',
    description:
      '플랫폼이 돈을 건드리지 않습니다. 센터↔강사 직접 정산',
  },
  {
    icon: Award,
    title: '패널티 시스템',
    description:
      '노쇼·당일취소에 자동 제재 — 신뢰할 수 있는 환경',
  },
] as const;

function TrustSignals() {
  const { ref, inView } = useInView();

  return (
    <section className="py-20 md:py-28 px-4 bg-muted/30">
      <div
        ref={ref}
        className={cn(
          'max-w-5xl mx-auto',
          inView ? 'animate-fade-up' : 'opacity-0',
        )}
      >
        <h2 className="font-display text-2xl md:text-3xl font-bold text-center mb-12">
          신뢰를 시스템으로
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TRUST_ITEMS.map((item) => (
            <div key={item.title} className="text-center">
              <div className="inline-flex items-center justify-center bg-primary/10 p-2.5 rounded-xl mb-4">
                <item.icon className="size-10 text-primary" />
              </div>
              <h3 className="font-display text-lg font-bold mb-2">
                {item.title}
              </h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// 7. CTA (repeated)
// ---------------------------------------------------------------------------

function CtaSection() {
  const { ref, inView } = useInView();

  return (
    <section className="py-20 md:py-28 px-4">
      <div
        ref={ref}
        className={cn(
          'max-w-5xl mx-auto',
          inView ? 'animate-fade-up' : 'opacity-0',
        )}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Studio card */}
          <div className="surface-elevated rounded-2xl p-8">
            <div className="inline-flex items-center justify-center bg-primary/10 rounded-xl p-3 mb-4">
              <Building2 className="size-12 text-primary" />
            </div>
            <h3 className="font-display text-xl font-bold">
              스튜디오 원장님이세요?
            </h3>
            <p className="text-muted-foreground mt-2">
              오늘 결원 나면, 오늘 확정됩니다
            </p>
            <Button size="lg" className="mt-6 w-full" asChild>
              <Link href="/signup">무료로 공고 등록하기</Link>
            </Button>
          </div>

          {/* Instructor card */}
          <div className="surface-elevated rounded-2xl p-8">
            <div className="inline-flex items-center justify-center bg-success/10 rounded-xl p-3 mb-4">
              <User className="size-12 text-success" />
            </div>
            <h3 className="font-display text-xl font-bold">
              필라테스/요가 강사님이세요?
            </h3>
            <p className="text-muted-foreground mt-2">
              내 동선에 맞는 검증 공고만 받아보세요
            </p>
            <Button
              variant="outline"
              size="lg"
              className="mt-6 w-full"
              asChild
            >
              <Link href="/signup">무료로 시작하기</Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// 8. Footer
// ---------------------------------------------------------------------------

function LandingFooter() {
  return (
    <footer className="border-t border-border/40 py-8 px-4">
      <div className="max-w-5xl mx-auto flex flex-col items-center gap-4">
        <Link href="/" className="font-display text-lg font-bold">
          <span className="text-primary">Pila</span>
          <span className="text-foreground">Match</span>
        </Link>

        <nav className="flex items-center gap-4">
          <Link
            href="/terms"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            이용약관
          </Link>
          <Link
            href="/privacy"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            개인정보처리방침
          </Link>
          <Link
            href="/refund"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            환불정책
          </Link>
        </nav>

        <p className="text-xs text-muted-foreground/60">
          &copy; 2026 PilaMatch. All rights reserved.
        </p>
      </div>
    </footer>
  );
}

// ---------------------------------------------------------------------------
// Composed LandingPage
// ---------------------------------------------------------------------------

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <LandingHeader />
      <Hero />
      <PainPoints />
      <HowItWorks />
      <Differentiators />
      <TrustSignals />
      <CtaSection />
      <LandingFooter />
    </div>
  );
}
