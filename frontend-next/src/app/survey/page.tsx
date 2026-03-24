import type { Metadata } from 'next';
import { SurveyPage } from '@/components/survey/survey-page';

export const metadata: Metadata = {
  title: 'PilaMatch — 필라테스 긴급 대타, 아직도 카톡으로 구하세요?',
  description:
    '30초 설문 참여하고 베타 테스트에 초대받으세요. 아침 9시 결원, 30분 내 검증 대타 확정.',
  openGraph: {
    title: 'PilaMatch — 필라테스 긴급 대타, 아직도 카톡으로 구하세요?',
    description: '30초 설문 참여하고 베타 테스트에 초대받으세요',
    type: 'website',
    locale: 'ko_KR',
    siteName: 'PilaMatch',
  },
};

export default function Survey() {
  return <SurveyPage />;
}
