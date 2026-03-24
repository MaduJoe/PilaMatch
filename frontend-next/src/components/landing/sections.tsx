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
  MapPin,
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
          긴급 대타 전문 · 30분 내 확정
        </Badge>

        <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight text-foreground">
          아침 9시 결원?
          <br />
          30분 내 확정.
        </h1>

        <p className="text-lg md:text-xl text-muted-foreground mt-6">
          반경 5km 내 검증된 대타 강사를 즉시 매칭합니다.
          <br />
          GPS 거리순 · 노쇼 방지 · 원탭 수락
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center mt-10">
          <Button size="lg" asChild>
            <Link href="/survey">
              30초 설문 참여하기
              <ArrowRight className="size-4" />
            </Link>
          </Button>
          <Button variant="outline" size="lg" asChild>
            <Link href="/survey">베타 테스트 신청</Link>
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
    title: '아침 9시, 강사 연락 두절',
    description:
      '수업 30분 전에 통보. 카톡방 돌려도 답 없고, 호호요가 올려도 언제 볼지 모름',
  },
  {
    icon: ScrollText,
    title: '호호요가? 게시판일 뿐',
    description:
      '글 올리고 → 댓글 기다리고 → 쪽지 보내고 → 전화 → 최소 수시간. 긴급엔 무력',
  },
  {
    icon: ClipboardX,
    title: '결국 수업 취소',
    description:
      '대타 못 구해서 원장님이 직접 뛰거나, 수업 취소. 회원 불만 → 매출 손실',
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
    title: '30초 긴급 등록',
    description:
      '종목·시간·급여 3가지만 입력. 30초면 공고 완료',
  },
  {
    num: '02',
    icon: Users,
    title: '즉시 푸시 알림',
    description:
      '반경 5km 내 검증 강사에게 자동 알림. GPS 거리순 매칭',
  },
  {
    num: '03',
    icon: PhoneCall,
    title: '원탭 수락 → 연결',
    description:
      '강사가 수락하면 즉시 연락처 공개. 직접 전화로 30분 내 확정',
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
    icon: MapPin,
    color: 'text-success',
    title: 'GPS 거리 매칭',
    description:
      '반경 5km 이내 강사만 매칭. "지금 출발하면 몇 분?"이 바로 보입니다',
  },
  {
    icon: Ban,
    color: 'text-urgent',
    title: '노쇼 = 14일 정지',
    description:
      '노쇼 시 즉시 정지 + Tier 강등. 게시판에 없는 강력한 패널티 시스템',
  },
  {
    icon: Shield,
    color: 'text-primary',
    title: '검증된 강사만',
    description:
      'SMS 인증 + 자격증 확인 + 실적 기반 Tier 등급. 모르는 강사도 믿고 맡깁니다',
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
          호호요가·카톡이 못 하는 것
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
              30분 내 검증된 대타 강사를 매칭해드립니다
            </p>
            <Button size="lg" className="mt-6 w-full" asChild>
              <Link href="/survey">30초 설문 참여하기</Link>
            </Button>
          </div>

          {/* Instructor card */}
          <div className="surface-elevated rounded-2xl p-8">
            <div className="inline-flex items-center justify-center bg-success/10 rounded-xl p-3 mb-4">
              <User className="size-12 text-success" />
            </div>
            <h3 className="font-display text-xl font-bold">
              프리랜서 강사님이세요?
            </h3>
            <p className="text-muted-foreground mt-2">
              내 위치 근처 긴급 대타만 푸시 알림으로 받으세요
            </p>
            <Button
              variant="outline"
              size="lg"
              className="mt-6 w-full"
              asChild
            >
              <Link href="/survey">베타 테스트 신청</Link>
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
