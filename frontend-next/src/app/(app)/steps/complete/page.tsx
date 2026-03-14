'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CompletionTab } from '@/components/reviews/completion-tab';
import { WrittenReviewsTab } from '@/components/reviews/written-reviews-tab';
import { ReceivedReviewsTab } from '@/components/reviews/received-reviews-tab';

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function CompletePage() {
  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-6 font-display text-2xl font-bold tracking-tight">5단계: 완료 & 리뷰</h1>

      <Tabs defaultValue="completion" className="flex flex-col gap-4">
        <TabsList className="w-full">
          <TabsTrigger value="completion" className="min-h-[44px]">
            완료 확인
          </TabsTrigger>
          <TabsTrigger value="written" className="min-h-[44px]">
            내가 쓴 리뷰
          </TabsTrigger>
          <TabsTrigger value="received" className="min-h-[44px]">
            받은 리뷰
          </TabsTrigger>
        </TabsList>

        <TabsContent value="completion">
          <CompletionTab />
        </TabsContent>

        <TabsContent value="written">
          <WrittenReviewsTab />
        </TabsContent>

        <TabsContent value="received">
          <ReceivedReviewsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
