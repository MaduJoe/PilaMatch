'use client';

import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useAuthStore } from '@/stores/auth-store';
import api, { APIError } from '@/lib/api-client';
import { formatCurrency, formatDate, cn } from '@/lib/utils';
import { TierBadge } from '@/components/trust/tier-badge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useGeolocation } from '@/hooks/use-geolocation';
import { DispatchAcceptDialog } from '@/components/dispatch/dispatch-accept-dialog';
import { DispatchStatusWidget } from '@/components/dispatch/dispatch-status-widget';
import type { DispatchRecordResponse } from '@/lib/api-types';
import { toast } from 'sonner';
import {
  Briefcase,
  AlertTriangle,
  Clock,
  CheckCircle2,
  ArrowRight,
  Users,
  Star,
  Shield,
  Zap,
  ChevronRight,
  Calendar,
  MapPin,
  Loader2,
  Radio,
  Bell,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Stat Card — neumorphic metric tile
// ---------------------------------------------------------------------------

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  accent?: 'primary' | 'success' | 'urgent' | 'muted';
  href?: string;
  subtitle?: string;
}

function StatCard({ label, value, icon, accent = 'muted', href, subtitle }: StatCardProps) {
  const accentMap = {
    primary: 'text-primary',
    success: 'text-success',
    urgent: 'text-urgent',
    muted: 'text-muted-foreground',
  };

  const accentBgMap = {
    primary: 'bg-primary/10',
    success: 'bg-success/10',
    urgent: 'bg-urgent/10',
    muted: 'bg-muted',
  };

  const inner = (
    <div className={cn('neu neu-hover cursor-default rounded-xl p-5 flex flex-col gap-3 h-full', href && 'cursor-pointer')}>
      <div className="flex items-center justify-between">
        <div className={cn('flex size-10 items-center justify-center rounded-xl', accentBgMap[accent])}>
          <div className={accentMap[accent]}>{icon}</div>
        </div>
        {href && <ChevronRight className="size-4 text-muted-foreground/40" />}
      </div>
      <div>
        <p className="font-display text-3xl font-bold tracking-tight animate-count-up">{value}</p>
        {subtitle && <p className="text-[11px] text-muted-foreground mt-0.5">{subtitle}</p>}
      </div>
      <p className="text-xs font-medium text-muted-foreground tracking-wide">{label}</p>
    </div>
  );

  if (href) {
    return <Link href={href} className="block">{inner}</Link>;
  }
  return inner;
}

// ---------------------------------------------------------------------------
// Activity Item — recent event row
// ---------------------------------------------------------------------------

interface ActivityItemProps {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  time: string;
  accent?: string;
}

function ActivityItem({ icon, title, subtitle, time, accent }: ActivityItemProps) {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-border/40 last:border-b-0">
      <div className={cn('mt-0.5 flex size-8 items-center justify-center rounded-lg neu-inset shrink-0', accent)}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{title}</p>
        <p className="text-xs text-muted-foreground truncate">{subtitle}</p>
      </div>
      <span className="text-[10px] text-muted-foreground/60 shrink-0 mt-1">{time}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Relative time helper
// ---------------------------------------------------------------------------

function relativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return '방금';
  if (mins < 60) return `${mins}분 전`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  return `${days}일 전`;
}

// ---------------------------------------------------------------------------
// Instructor Dashboard
// ---------------------------------------------------------------------------

function InstructorDashboard() {
  const queryClient = useQueryClient();
  const geo = useGeolocation();

  // Dialog state for dispatch accept
  const [selectedDispatch, setSelectedDispatch] = useState<DispatchRecordResponse | null>(null);

  const tierQuery = useQuery({
    queryKey: ['my-tier'],
    queryFn: () => api.tier.getMyTier(),
  });

  const appsQuery = useQuery({
    queryKey: ['my-applications'],
    queryFn: () => api.applications.getMyApplications(),
  });

  const contractsQuery = useQuery({
    queryKey: ['my-contracts'],
    queryFn: () => api.contracts.getMyContracts(),
  });

  const reviewsQuery = useQuery({
    queryKey: ['reviews-received'],
    queryFn: () => api.reviews.getReceived(),
  });

  // Availability query — 404 means "not available yet"
  const availabilityQuery = useQuery({
    queryKey: ['availability-me'],
    queryFn: async () => {
      try {
        return await api.availability.getMe();
      } catch (err) {
        if (err instanceof APIError && err.status === 404) return null;
        throw err;
      }
    },
  });

  const isAvailable = availabilityQuery.data?.is_available ?? false;

  // Toggle mutation
  const toggleMutation = useMutation({
    mutationFn: (data: { is_available: boolean; latitude?: number; longitude?: number }) =>
      api.availability.toggle(data),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ['availability-me'] });
      if (data.is_available) {
        toast.success('대기 상태를 켰습니다');
      } else {
        toast.info('대기 상태를 껐습니다');
      }
    },
    onError: (err: Error) => {
      if (err instanceof APIError) {
        toast.error(err.message);
      } else {
        toast.error('대기 상태 변경에 실패했습니다');
      }
    },
  });

  // Pending dispatches — only fetch when available
  const pendingDispatchQuery = useQuery({
    queryKey: ['dispatch-pending'],
    queryFn: () => api.dispatch.getMyPending(),
    enabled: isAvailable,
    refetchInterval: 10_000,
  });

  const pendingDispatches = pendingDispatchQuery.data ?? [];

  // Handle toggle click
  const handleToggle = () => {
    if (isAvailable) {
      // Turn OFF
      toggleMutation.mutate({ is_available: false });
    } else {
      // Turn ON — need GPS
      if (geo.loading) {
        toast.info('위치 확인 중입니다. 잠시 후 다시 시도해주세요.');
        return;
      }
      if (geo.error || !geo.latitude || !geo.longitude) {
        toast.error('위치를 가져올 수 없습니다. 위치 권한을 확인해주세요.');
        return;
      }
      toggleMutation.mutate({
        is_available: true,
        latitude: geo.latitude,
        longitude: geo.longitude,
      });
    }
  };

  // Format expiry time
  const expiryText = useMemo(() => {
    const until = availabilityQuery.data?.available_until;
    if (!until) return null;
    try {
      return new Intl.DateTimeFormat('ko-KR', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      }).format(new Date(until));
    } catch {
      return null;
    }
  }, [availabilityQuery.data?.available_until]);

  // Approximate location text from coordinates
  const locationText = useMemo(() => {
    if (geo.loading) return '위치 확인 중...';
    if (geo.error) return '위치를 가져올 수 없습니다';
    if (geo.latitude && geo.longitude) {
      // Simple approximate: use stored coords from availability response if available
      const lat = availabilityQuery.data?.latitude ?? geo.latitude;
      const lng = availabilityQuery.data?.longitude ?? geo.longitude;
      // Rough Seoul district approximation
      if (lat >= 37.49 && lat <= 37.53 && lng >= 127.02 && lng <= 127.06) return '강남구 부근';
      if (lat >= 37.47 && lat <= 37.50 && lng >= 126.98 && lng <= 127.03) return '서초구 부근';
      if (lat >= 37.54 && lat <= 37.58 && lng >= 126.96 && lng <= 127.01) return '마포구 부근';
      if (lat >= 37.55 && lat <= 37.58 && lng >= 127.0 && lng <= 127.05) return '성동구 부근';
      if (lat >= 37.50 && lat <= 37.54 && lng >= 127.0 && lng <= 127.05) return '송파구 부근';
      return `${lat.toFixed(2)}, ${lng.toFixed(2)} 부근`;
    }
    return null;
  }, [geo.loading, geo.error, geo.latitude, geo.longitude, availabilityQuery.data?.latitude, availabilityQuery.data?.longitude]);

  // Derived stats
  const apps = appsQuery.data?.items ?? [];
  const pendingApps = apps.filter(a => a.status === 'pending');
  const acceptedApps = apps.filter(a => a.status === 'accepted');
  const contracts = contractsQuery.data?.items ?? [];
  const completedContracts = contracts.filter(c => c.status === 'completed');
  const tier = tierQuery.data;
  const reviews = reviewsQuery.data;

  // Build activity feed from recent apps + contracts
  const activities = useMemo(() => {
    const items: { key: string; icon: React.ReactNode; title: string; subtitle: string; time: string; date: string; accent?: string }[] = [];

    for (const app of apps.slice(0, 5)) {
      if (app.status === 'accepted') {
        items.push({
          key: `app-${app.id}`,
          icon: <CheckCircle2 className="size-4 text-success" />,
          title: '지원 수락됨',
          subtitle: app.job_title ?? '공고',
          time: relativeTime(app.updated_at ?? app.created_at),
          date: app.updated_at ?? app.created_at,
        });
      } else if (app.status === 'pending') {
        items.push({
          key: `app-${app.id}`,
          icon: <Clock className="size-4 text-primary" />,
          title: '지원함',
          subtitle: app.job_title ?? '공고',
          time: relativeTime(app.created_at),
          date: app.created_at,
        });
      }
    }

    for (const c of contracts.slice(0, 3)) {
      if (c.status === 'completed') {
        items.push({
          key: `contract-${c.id}`,
          icon: <Star className="size-4 text-amber-500" />,
          title: '완료',
          subtitle: `${c.studio_name ?? '스튜디오'} - ${formatCurrency(c.hourly_rate ?? 0)}/h`,
          time: relativeTime(c.updated_at ?? c.created_at),
          date: c.updated_at ?? c.created_at,
        });
      }
    }

    return items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 6);
  }, [apps, contracts]);

  return (
    <div className="stagger-list space-y-8">
      {/* Hero: Greeting + Tier + Next tier */}
      <div className="neu rounded-xl p-6">
        <div>
          <p className="text-sm text-muted-foreground">강사 대시보드</p>
          <div className="flex items-center gap-3 mt-1">
            <h1 className="font-display text-2xl font-bold tracking-tight truncate">홈</h1>
            {tier && <TierBadge tier={tier.tier} label={tier.tier_label} size="md" />}
          </div>
        </div>
        {tier && tier.next_tier && tier.missing_requirements.length > 0 && (
          <div className="mt-4 pt-4 border-t border-border/40">
            <p className="text-[11px] font-medium text-muted-foreground mb-2">
              다음 등급 조건:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {tier.missing_requirements.map((req, i) => (
                <span key={i} className="inline-flex items-center gap-1 rounded-md bg-muted/50 px-2 py-0.5 text-[11px] text-muted-foreground">
                  <span className="size-1 shrink-0 rounded-full bg-primary/40" />
                  {req}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Availability Toggle Card */}
      <button
        type="button"
        onClick={handleToggle}
        disabled={toggleMutation.isPending}
        aria-label={isAvailable ? '대기 상태 끄기' : '대기 상태 켜기'}
        className={cn(
          'neu rounded-xl p-5 w-full text-left transition-colors',
          isAvailable
            ? 'border-emerald-200 bg-emerald-50/50 dark:border-emerald-800 dark:bg-emerald-950/20'
            : '',
        )}
      >
        <div className="flex items-center gap-3 mb-3">
          <div className={cn(
            'flex size-10 items-center justify-center rounded-xl',
            isAvailable ? 'bg-emerald-100 dark:bg-emerald-900/30' : 'bg-muted',
          )}>
            <Radio className={cn('size-5', isAvailable ? 'text-emerald-600' : 'text-muted-foreground')} />
          </div>
          <h2 className="text-sm font-semibold">대기 상태</h2>
          {toggleMutation.isPending && (
            <Loader2 className="ml-auto size-4 animate-spin text-muted-foreground" />
          )}
        </div>

        <div className={cn(
          'rounded-lg p-4 text-center transition-colors',
          isAvailable
            ? 'bg-emerald-100/60 dark:bg-emerald-900/20'
            : 'bg-muted/50',
        )}>
          {isAvailable ? (
            <div className="space-y-1.5">
              <div className="flex items-center justify-center gap-2">
                <span className="relative flex size-2.5">
                  <span className="absolute inline-flex size-full animate-pulse-soft rounded-full bg-emerald-500 opacity-75" />
                  <span className="relative inline-flex size-2.5 rounded-full bg-emerald-500" />
                </span>
                <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">
                  ON: 대기 중
                </span>
              </div>
              {locationText && (
                <p className="text-xs text-emerald-600/80 dark:text-emerald-400/80">
                  {locationText}
                </p>
              )}
              {expiryText && (
                <p className="text-[11px] text-muted-foreground">
                  만료: {expiryText}
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">OFF: 오프라인</p>
            </div>
          )}
        </div>

        <p className="mt-3 text-[11px] text-muted-foreground leading-relaxed">
          대기를 켜면 주변 센터의 긴급 요청을 자동으로 받을 수 있습니다
        </p>
      </button>

      {/* Dispatch Pending Banner */}
      {isAvailable && (
        <div className={cn(
          'rounded-xl p-5 border-l-4',
          pendingDispatches.length > 0
            ? 'border-l-amber-500 bg-amber-50/50 dark:bg-amber-950/20 neu'
            : 'neu',
        )}>
          {pendingDispatches.length > 0 ? (
            <>
              <div className="flex items-center gap-2 mb-3">
                <Bell className="size-4 text-amber-600 animate-pulse-soft" aria-hidden="true" />
                <h3 className="text-sm font-semibold">
                  긴급 대타 요청 {pendingDispatches.length}건
                </h3>
              </div>
              <div className="space-y-2">
                {pendingDispatches.map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => setSelectedDispatch(d)}
                    className="w-full rounded-lg border bg-card p-3 text-left hover:bg-muted/40 transition-colors"
                    aria-label="긴급 대타 요청 확인하기"
                  >
                    <div className="flex items-center justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 text-sm font-medium">
                          {d.distance_km != null && (
                            <span className="inline-flex items-center gap-1 text-muted-foreground text-xs">
                              <MapPin className="size-3" />
                              {d.distance_km.toFixed(1)}km
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                          <span className="inline-flex items-center gap-1">
                            <Clock className="size-3" />
                            {relativeTime(d.dispatched_at)}
                          </span>
                        </div>
                      </div>
                      <span className="flex items-center gap-1 text-xs font-medium text-primary">
                        확인하기 <ArrowRight className="size-3" />
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center gap-3 py-2">
              <Loader2 className="size-4 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                대기 중... 긴급 요청을 기다리는 중입니다
              </p>
            </div>
          )}
        </div>
      )}

      {/* Dispatch Accept Dialog */}
      <DispatchAcceptDialog
        dispatch={selectedDispatch}
        open={selectedDispatch !== null}
        onClose={() => setSelectedDispatch(null)}
        onAccepted={() => {
          void queryClient.invalidateQueries({ queryKey: ['dispatch-pending'] });
        }}
      />

      {/* Stat Grid */}
      <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
        <StatCard
          label="대기 중"
          value={pendingApps.length}
          icon={<Clock className="size-5" />}
          accent="primary"
          href="/steps/offers"
          subtitle="응답 대기"
        />
        <StatCard
          label="수락됨"
          value={acceptedApps.length}
          icon={<CheckCircle2 className="size-5" />}
          accent="success"
          href="/steps/offers"
          subtitle="연락처 공개"
        />
        <StatCard
          label="완료"
          value={completedContracts.length}
          icon={<Briefcase className="size-5" />}
          accent="muted"
          subtitle="누적"
        />
        <StatCard
          label="노쇼"
          value={tier?.no_show_recent ?? 0}
          icon={<AlertTriangle className="size-5" />}
          accent={(tier?.no_show_recent ?? 0) > 0 ? 'urgent' : 'muted'}
          subtitle="최근 30일"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3">
        <Link href="/steps/jobs">
          <div className="neu neu-hover rounded-xl p-4 flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10">
              <Zap className="size-5 text-primary" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold">찾기</p>
              <p className="text-[10px] text-muted-foreground">공고 둘러보기</p>
            </div>
          </div>
        </Link>
        <Link href="/steps/profile">
          <div className="neu neu-hover rounded-xl p-4 flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-muted">
              <Shield className="size-5 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold">프로필</p>
              <p className="text-[10px] text-muted-foreground">내 정보 관리</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Two-column: Activity + Reviews */}
      <div className="grid gap-5 lg:grid-cols-5">
        {/* Recent Activity */}
        <div className="lg:col-span-3 neu rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-display text-sm font-semibold tracking-wide">최근 활동</h2>
            <Link href="/steps/offers" className="text-[10px] text-primary font-medium hover:underline flex items-center gap-0.5">
              전체 보기 <ArrowRight className="size-3" />
            </Link>
          </div>
          {activities.length === 0 ? (
            <div className="neu-inset rounded-xl p-8 text-center">
              <p className="text-sm text-muted-foreground">최근 활동이 없습니다</p>
              <p className="text-xs text-muted-foreground/60 mt-1">공고에 지원하면 여기에 표시됩니다</p>
            </div>
          ) : (
            <div>
              {activities.map(({ key, date, ...rest }) => (
                <ActivityItem key={key} {...rest} />
              ))}
            </div>
          )}
        </div>

        {/* Reviews Summary */}
        <div className="lg:col-span-2 neu rounded-xl p-5">
          <h2 className="font-display text-sm font-semibold tracking-wide mb-4">받은 리뷰</h2>
          {reviews && (reviews.items?.length ?? 0) > 0 ? (
            <div className="space-y-4">
              {/* Average rating display */}
              <div className="neu-inset rounded-xl p-4 text-center">
                <p className="font-display text-4xl font-bold text-primary animate-count-up">
                  {(reviews.average_rating ?? 0).toFixed(1)}
                </p>
                <div className="flex items-center justify-center gap-0.5 mt-1">
                  {[1, 2, 3, 4, 5].map(i => (
                    <Star
                      key={i}
                      className={cn(
                        'size-3.5',
                        i <= Math.round(reviews.average_rating ?? 0)
                          ? 'fill-amber-400 text-amber-400'
                          : 'text-muted-foreground/30',
                      )}
                    />
                  ))}
                </div>
                <p className="text-[10px] text-muted-foreground mt-1.5">{reviews.items?.length ?? 0}개 리뷰</p>
              </div>
              {/* Latest reviews */}
              <div className="space-y-2">
                {(reviews.items ?? []).slice(0, 3).map((review) => (
                  <div key={review.id} className="rounded-lg p-2.5 bg-muted/30 text-xs">
                    <div className="flex items-center gap-1 mb-1">
                      {[1, 2, 3, 4, 5].map(i => (
                        <Star
                          key={i}
                          className={cn(
                            'size-2.5',
                            i <= review.rating ? 'fill-amber-400 text-amber-400' : 'text-muted-foreground/30',
                          )}
                        />
                      ))}
                      <span className="text-[10px] text-muted-foreground ml-1">{review.reviewer_name}</span>
                    </div>
                    {review.comment && (
                      <p className="text-muted-foreground line-clamp-2">{review.comment}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="neu-inset rounded-xl p-8 text-center">
              <Star className="size-8 text-muted-foreground/20 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">아직 리뷰가 없습니다</p>
              <p className="text-xs text-muted-foreground/60 mt-1">수업을 완료하면 리뷰를 받을 수 있습니다</p>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}

// ---------------------------------------------------------------------------
// Studio Dashboard
// ---------------------------------------------------------------------------

function StudioDashboard() {
  const tierQuery = useQuery({
    queryKey: ['my-tier'],
    queryFn: () => api.tier.getMyTier(),
  });

  const jobsQuery = useQuery({
    queryKey: ['studio-job-posts'],
    queryFn: () => api.jobPosts.listMine(),
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  });

  const contractsQuery = useQuery({
    queryKey: ['my-contracts'],
    queryFn: () => api.contracts.getMyContracts(),
  });

  const reviewsQuery = useQuery({
    queryKey: ['reviews-received'],
    queryFn: () => api.reviews.getReceived(),
  });

  // Derived stats
  const jobs = jobsQuery.data?.items ?? [];
  const openJobs = jobs.filter(j => j.status === 'open');
  const totalApplicants = openJobs.reduce((sum, j) => sum + (j.application_count ?? 0), 0);
  const contracts = contractsQuery.data?.items ?? [];
  const completedContracts = contracts.filter(c => c.status === 'completed');
  const tier = tierQuery.data;
  const reviews = reviewsQuery.data;

  // Urgent open jobs for dispatch summary
  const urgentOpenJobs = useMemo(
    () => jobs.filter(j => j.is_urgent && j.status === 'open'),
    [jobs],
  );

  // Recent jobs as activity
  const recentJobs = useMemo(() => {
    return jobs.slice(0, 6).map(job => ({
      key: job.id,
      title: job.title,
      region: job.region,
      date: job.date,
      applicants: job.application_count ?? 0,
      status: job.status,
      isUrgent: job.is_urgent,
      created: job.created_at,
    }));
  }, [jobs]);

  return (
    <div className="stagger-list space-y-8">
      {/* Hero */}
      <div className="neu rounded-xl p-6">
        <div>
          <p className="text-sm text-muted-foreground">스튜디오 대시보드</p>
          <div className="flex items-center gap-3 mt-1">
            <h1 className="font-display text-2xl font-bold tracking-tight truncate">홈</h1>
            {tier && <TierBadge tier={tier.tier} label={tier.tier_label} size="md" />}
          </div>
        </div>
        {tier && tier.next_tier && tier.missing_requirements.length > 0 && (
          <div className="mt-4 pt-4 border-t border-border/40">
            <p className="text-[11px] font-medium text-muted-foreground mb-2">
              다음 등급 조건:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {tier.missing_requirements.map((req, i) => (
                <span key={i} className="inline-flex items-center gap-1 rounded-md bg-muted/50 px-2 py-0.5 text-[11px] text-muted-foreground">
                  <span className="size-1 shrink-0 rounded-full bg-primary/40" />
                  {req}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Applicant Alert */}
      {totalApplicants > 0 && (
        <Link href="/steps/offers">
          <div className="neu neu-hover rounded-xl p-5 border-l-4 border-l-primary flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 animate-pulse-soft">
                <Users className="size-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-semibold">대기 중인 지원자 {totalApplicants}명</p>
                <p className="text-[10px] text-muted-foreground">{openJobs.filter(j => (j.application_count ?? 0) > 0).length}개 공고에서</p>
              </div>
            </div>
            <ArrowRight className="size-5 text-primary" />
          </div>
        </Link>
      )}

      {/* Stat Grid */}
      <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
        <StatCard
          label="모집 중"
          value={openJobs.length}
          icon={<Briefcase className="size-5" />}
          accent="primary"
          href="/steps/jobs"
          subtitle={`전체 ${jobs.length}개 중`}
        />
        <StatCard
          label="지원자"
          value={totalApplicants}
          icon={<Users className="size-5" />}
          accent={totalApplicants > 0 ? 'success' : 'muted'}
          href="/steps/offers"
          subtitle="검토 대기"
        />
        <StatCard
          label="완료"
          value={completedContracts.length}
          icon={<CheckCircle2 className="size-5" />}
          accent="muted"
          subtitle="누적"
        />
        <StatCard
          label="평균 평점"
          value={(reviews?.average_rating ?? 0).toFixed(1)}
          icon={<Star className="size-5" />}
          accent={(reviews?.average_rating ?? 0) >= 4 ? 'success' : 'muted'}
          subtitle={`${reviews?.items?.length ?? 0}개 리뷰`}
        />
      </div>

      {/* Active Dispatches Summary */}
      {urgentOpenJobs.length > 0 && (
        <div className="neu rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="size-4 text-urgent" aria-hidden="true" />
            <h2 className="font-display text-sm font-semibold tracking-wide">
              진행 중인 긴급 대타
            </h2>
          </div>
          <div className="space-y-3">
            {urgentOpenJobs.map((job) => (
              <div key={job.id} className="rounded-lg border p-3">
                <p className="text-sm font-medium truncate mb-1">{job.title}</p>
                <DispatchStatusWidget jobPostId={job.id} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3">
        <Link href="/steps/jobs">
          <div className="neu neu-hover rounded-xl p-4 flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10">
              <Zap className="size-5 text-primary" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold">공고 등록</p>
              <p className="text-[10px] text-muted-foreground">새 공고 작성하기</p>
            </div>
          </div>
        </Link>
        <Link href="/steps/offers">
          <div className="neu neu-hover rounded-xl p-4 flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-muted">
              <Users className="size-5 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold">지원자</p>
              <p className="text-[10px] text-muted-foreground">검토 및 수락</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Recent Job Posts */}
      <div className="neu rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display text-sm font-semibold tracking-wide">최근 공고</h2>
          <Link href="/steps/jobs" className="text-[10px] text-primary font-medium hover:underline flex items-center gap-0.5">
            전체 관리 <ArrowRight className="size-3" />
          </Link>
        </div>
        {recentJobs.length === 0 ? (
          <div className="neu-inset rounded-xl p-8 text-center">
            <Briefcase className="size-8 text-muted-foreground/20 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">아직 공고가 없습니다</p>
            <Button asChild variant="outline" size="sm" className="mt-3 min-h-[36px]">
              <Link href="/steps/jobs">첫 공고 등록하기</Link>
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            {recentJobs.map(job => (
              <div
                key={job.key}
                className="flex items-center gap-3 rounded-xl p-3 bg-muted/20 hover:bg-muted/40 transition-colors"
              >
                <div className={cn(
                  'flex size-9 items-center justify-center rounded-lg neu-inset shrink-0',
                )}>
                  {job.isUrgent ? (
                    <Zap className="size-4 text-urgent" />
                  ) : (
                    <Briefcase className="size-4 text-muted-foreground" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{job.title}</p>
                  <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                    {job.region && (
                      <span className="inline-flex items-center gap-0.5">
                        <MapPin className="size-2.5" /> {job.region}
                      </span>
                    )}
                    <span className="inline-flex items-center gap-0.5">
                      <Calendar className="size-2.5" /> {formatDate(job.date)}
                    </span>
                  </div>
                </div>
                <div className="shrink-0 flex items-center gap-2">
                  {job.applicants > 0 && (
                    <Badge variant="secondary" className="text-[10px] font-display">
                      {job.applicants}
                    </Badge>
                  )}
                  <Badge
                    variant={job.status === 'open' ? 'default' : 'outline'}
                    className="text-[10px] font-display"
                  >
                    {job.status === 'open' ? '모집 중' : job.status === 'filled' ? '마감' : '종료'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const { user, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center animate-fade-in">
        <div className="text-center">
          <div className="relative mx-auto size-12">
            <div className="absolute inset-0 rounded-full border-[3px] border-primary/20" />
            <div className="absolute inset-0 animate-spin rounded-full border-[3px] border-primary border-t-transparent" />
          </div>
          <p className="mt-5 font-display text-sm font-medium text-muted-foreground tracking-wide">불러오는 중...</p>
        </div>
      </div>
    );
  }

  const isInstructor = user?.role === 'instructor';

  return isInstructor ? <InstructorDashboard /> : <StudioDashboard />;
}
