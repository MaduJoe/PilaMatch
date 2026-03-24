import type { Metadata } from 'next';
import { LandingPage } from '@/components/landing/sections';

export const metadata: Metadata = {
  title: 'PilaMatch — 필라테스 긴급 대타 30분 매칭',
  description:
    '아침 9시 결원? 30분 내 확정. 반경 5km 내 검증된 대타 강사를 즉시 매칭합니다. GPS 거리순 매칭, 노쇼 14일 정지, 원탭 수락.',
  keywords: [
    '필라테스 긴급 대타',
    '당일 대타 강사',
    '필라테스 급구',
    '대타 매칭 앱',
    '필라테스 대강',
    '강사 노쇼 방지',
    '필라테스 구인 즉시',
  ],
  openGraph: {
    title: 'PilaMatch — 필라테스 긴급 대타 30분 매칭',
    description: '아침 9시 결원? 30분 내 검증된 대타 강사 확정',
    type: 'website',
    locale: 'ko_KR',
    siteName: 'PilaMatch',
  },
};

export default function Home() {
  return <LandingPage />;
}
