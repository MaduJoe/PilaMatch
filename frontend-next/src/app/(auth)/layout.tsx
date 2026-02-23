export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">StudioBridge</h1>
          <p className="mt-2 text-sm text-gray-500">
            신뢰 기반 필라테스/요가 강사-스튜디오 매칭
          </p>
        </div>
        {children}
      </div>
    </div>
  );
}
