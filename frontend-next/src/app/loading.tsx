export default function Loading() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center animate-fade-in">
      <div className="text-center">
        <div className="relative mx-auto size-12">
          <div className="absolute inset-0 rounded-full border-[3px] border-primary/20" />
          <div className="absolute inset-0 animate-spin rounded-full border-[3px] border-primary border-t-transparent" />
        </div>
        <p className="mt-5 font-display text-sm font-medium text-muted-foreground tracking-wide">Loading...</p>
      </div>
    </div>
  );
}
