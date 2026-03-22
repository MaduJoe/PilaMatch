import type { Metadata } from 'next';
import { LandingPage } from '@/components/landing/sections';

export const metadata: Metadata = {
  title: 'PilaMatch — 필라테스 대타 60분 매칭',
  description:
    '오늘 결원, 오늘 확정. 검증된 강사를 60분 내에 매칭합니다. 노쇼 방지, 인수인계 노트, Tier 시스템으로 신뢰 기반 매칭.',
  keywords: [
    '필라테스 대타',
    '요가 대타',
    '강사 매칭',
    '필라테스 구인',
    '대타 강사',
    '급구',
    '필라테스 대강',
  ],
  openGraph: {
    title: 'PilaMatch — 필라테스 대타 60분 매칭',
    description: '오늘 결원, 오늘 확정. 검증된 강사 매칭 플랫폼',
    type: 'website',
    locale: 'ko_KR',
    siteName: 'PilaMatch',
  },
};

export default function Home() {
  return <LandingPage />;
}
