import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Home, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 text-center">
      <p className="mb-2 text-6xl font-bold text-muted-foreground">404</p>
      <h2 className="mb-2 text-2xl font-bold">페이지를 찾을 수 없습니다</h2>
      <p className="mb-6 max-w-md text-muted-foreground">
        요청하신 페이지가 존재하지 않거나 이동되었을 수 있습니다.
      </p>
      <div className="flex gap-3">
        <Button variant="outline" asChild>
          <Link href="javascript:history.back()">
            <ArrowLeft className="mr-2 h-4 w-4" />
            이전 페이지
          </Link>
        </Button>
        <Button asChild>
          <Link href="/">
            <Home className="mr-2 h-4 w-4" />
            홈으로
          </Link>
        </Button>
      </div>
    </div>
  );
}
