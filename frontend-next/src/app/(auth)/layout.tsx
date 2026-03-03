export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-primary">PilaMatch</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            신뢰 기반 필라테스/요가 강사-스튜디오 매칭
          </p>
        </div>
        {children}
      </div>
    </div>
  );
}
