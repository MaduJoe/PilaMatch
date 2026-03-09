'use client';

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useAuthStore } from '@/stores/auth-store';
import api from '@/lib/api-client';
import { formatCurrency, formatDate, cn } from '@/lib/utils';
import { TierBadge } from '@/components/trust/tier-badge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Briefcase,
  TrendingUp,
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
    <div className={cn('neu neu-hover cursor-default rounded-2xl p-5 flex flex-col gap-3 h-full', href && 'cursor-pointer')}>
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
// Progress Ring — circular progress indicator (neumorphic)
// ---------------------------------------------------------------------------

function ProgressRing({ value, size = 80, strokeWidth = 7 }: { value: number; size?: number; strokeWidth?: number }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        {/* Background ring (inset feel) */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-muted/80"
        />
        {/* Progress arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="text-primary transition-all duration-700 ease-out"
        />
      </svg>
      <span className="absolute font-display text-lg font-bold">{value}%</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Relative time helper
// ---------------------------------------------------------------------------

function relativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ---------------------------------------------------------------------------
// Instructor Dashboard
// ---------------------------------------------------------------------------

function InstructorDashboard() {
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

  const profileQuery = useQuery({
    queryKey: ['profile', 'completeness'],
    queryFn: () => api.profileCompleteness.get(),
  });

  // Derived stats
  const apps = appsQuery.data?.items ?? [];
  const pendingApps = apps.filter(a => a.status === 'pending');
  const acceptedApps = apps.filter(a => a.status === 'accepted');
  const contracts = contractsQuery.data?.items ?? [];
  const activeContracts = contracts.filter(c => c.status === 'in_progress');
  const completedContracts = contracts.filter(c => c.status === 'completed');
  const tier = tierQuery.data;
  const reviews = reviewsQuery.data;
  const profilePct = profileQuery.data?.percentage ?? 0;

  // Build activity feed from recent apps + contracts
  const activities = useMemo(() => {
    const items: { key: string; icon: React.ReactNode; title: string; subtitle: string; time: string; date: string; accent?: string }[] = [];

    for (const app of apps.slice(0, 5)) {
      if (app.status === 'accepted') {
        items.push({
          key: `app-${app.id}`,
          icon: <CheckCircle2 className="size-4 text-success" />,
          title: 'Application accepted',
          subtitle: app.job_title ?? 'Job',
          time: relativeTime(app.updated_at ?? app.created_at),
          date: app.updated_at ?? app.created_at,
        });
      } else if (app.status === 'pending') {
        items.push({
          key: `app-${app.id}`,
          icon: <Clock className="size-4 text-primary" />,
          title: 'Applied',
          subtitle: app.job_title ?? 'Job',
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
          title: 'Completed',
          subtitle: `${c.studio_name ?? 'Studio'} - ${formatCurrency(c.hourly_rate ?? 0)}/h`,
          time: relativeTime(c.updated_at ?? c.created_at),
          date: c.updated_at ?? c.created_at,
        });
      }
    }

    return items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 6);
  }, [apps, contracts]);

  return (
    <div className="stagger-list space-y-6">
      {/* Hero: Greeting + Tier */}
      <div className="neu rounded-2xl p-6 flex items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground">Welcome back</p>
          <h1 className="font-display text-2xl font-bold tracking-tight mt-1 truncate">Dashboard</h1>
          {tier && (
            <div className="flex items-center gap-2 mt-2">
              <TierBadge tier={tier.tier} label={tier.tier_label} size="md" />
              {tier.next_tier && tier.missing_requirements.length > 0 && (
                <span className="text-[10px] text-muted-foreground">
                  {tier.missing_requirements.length} step{tier.missing_requirements.length > 1 ? 's' : ''} to next tier
                </span>
              )}
            </div>
          )}
        </div>
        <ProgressRing value={profilePct} />
      </div>

      {/* Stat Grid */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Pending"
          value={pendingApps.length}
          icon={<Clock className="size-5" />}
          accent="primary"
          href="/steps/offers"
          subtitle="awaiting response"
        />
        <StatCard
          label="Accepted"
          value={acceptedApps.length}
          icon={<CheckCircle2 className="size-5" />}
          accent="success"
          href="/steps/offers"
          subtitle="contact revealed"
        />
        <StatCard
          label="Completed"
          value={completedContracts.length}
          icon={<Briefcase className="size-5" />}
          accent="muted"
          subtitle="all time"
        />
        <StatCard
          label="No-shows"
          value={tier?.no_show_recent ?? 0}
          icon={<AlertTriangle className="size-5" />}
          accent={(tier?.no_show_recent ?? 0) > 0 ? 'urgent' : 'muted'}
          subtitle="last 30 days"
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
              <p className="text-sm font-semibold">Find Jobs</p>
              <p className="text-[10px] text-muted-foreground">Browse open positions</p>
            </div>
          </div>
        </Link>
        <Link href="/steps/profile">
          <div className="neu neu-hover rounded-xl p-4 flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-muted">
              <Shield className="size-5 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold">Profile</p>
              <p className="text-[10px] text-muted-foreground">{profilePct}% complete</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Two-column: Activity + Reviews */}
      <div className="grid gap-4 lg:grid-cols-5">
        {/* Recent Activity */}
        <div className="lg:col-span-3 neu rounded-2xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-display text-sm font-semibold tracking-wide">Recent Activity</h2>
            <Link href="/steps/offers" className="text-[10px] text-primary font-medium hover:underline flex items-center gap-0.5">
              View all <ArrowRight className="size-3" />
            </Link>
          </div>
          {activities.length === 0 ? (
            <div className="neu-inset rounded-xl p-8 text-center">
              <p className="text-sm text-muted-foreground">No recent activity</p>
              <p className="text-xs text-muted-foreground/60 mt-1">Apply to jobs to get started</p>
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
        <div className="lg:col-span-2 neu rounded-2xl p-5">
          <h2 className="font-display text-sm font-semibold tracking-wide mb-4">Reviews</h2>
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
                <p className="text-[10px] text-muted-foreground mt-1.5">{reviews.items?.length ?? 0} reviews</p>
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
              <p className="text-sm text-muted-foreground">No reviews yet</p>
              <p className="text-xs text-muted-foreground/60 mt-1">Complete jobs to receive reviews</p>
            </div>
          )}
        </div>
      </div>

      {/* Tier Progress */}
      {tier && tier.next_tier && tier.missing_requirements.length > 0 && (
        <div className="neu rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="size-4 text-primary" />
            <h2 className="font-display text-sm font-semibold tracking-wide">Tier Progress</h2>
          </div>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="neu-inset rounded-xl p-3 text-center">
              <p className="font-display text-xl font-bold">{tier.completed_jobs_recent}</p>
              <p className="text-[10px] text-muted-foreground">Completed (30d)</p>
            </div>
            <div className="neu-inset rounded-xl p-3 text-center">
              <p className="font-display text-xl font-bold">{tier.no_show_recent}</p>
              <p className="text-[10px] text-muted-foreground">No-shows (30d)</p>
            </div>
            <div className="neu-inset rounded-xl p-3 text-center">
              <p className={cn('font-display text-xl font-bold', (tier.same_day_cancel_recent + tier.late_recent) > 0 && 'text-urgent')}>
                {tier.same_day_cancel_recent + tier.late_recent}
              </p>
              <p className="text-[10px] text-muted-foreground">Issues (30d)</p>
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground">Requirements for next tier:</p>
            {tier.missing_requirements.map((req, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary/40" />
                <span className="text-muted-foreground">{req}</span>
              </div>
            ))}
          </div>
        </div>
      )}
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
    refetchInterval: 30000,
  });

  const contractsQuery = useQuery({
    queryKey: ['my-contracts'],
    queryFn: () => api.contracts.getMyContracts(),
  });

  const reviewsQuery = useQuery({
    queryKey: ['reviews-received'],
    queryFn: () => api.reviews.getReceived(),
  });

  const profileQuery = useQuery({
    queryKey: ['profile', 'completeness'],
    queryFn: () => api.profileCompleteness.get(),
  });

  // Derived stats
  const jobs = jobsQuery.data?.items ?? [];
  const openJobs = jobs.filter(j => j.status === 'open');
  const totalApplicants = openJobs.reduce((sum, j) => sum + (j.application_count ?? 0), 0);
  const contracts = contractsQuery.data?.items ?? [];
  const completedContracts = contracts.filter(c => c.status === 'completed');
  const tier = tierQuery.data;
  const reviews = reviewsQuery.data;
  const profilePct = profileQuery.data?.percentage ?? 0;

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
    <div className="stagger-list space-y-6">
      {/* Hero */}
      <div className="neu rounded-2xl p-6 flex items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground">Studio Dashboard</p>
          <h1 className="font-display text-2xl font-bold tracking-tight mt-1 truncate">Overview</h1>
          {tier && (
            <div className="flex items-center gap-2 mt-2">
              <TierBadge tier={tier.tier} label={tier.tier_label} size="md" />
            </div>
          )}
        </div>
        <ProgressRing value={profilePct} />
      </div>

      {/* Applicant Alert */}
      {totalApplicants > 0 && (
        <Link href="/steps/offers">
          <div className="neu neu-hover rounded-2xl p-5 border-l-4 border-l-primary flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 animate-pulse-soft">
                <Users className="size-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-semibold">{totalApplicants} pending applicant{totalApplicants > 1 ? 's' : ''}</p>
                <p className="text-[10px] text-muted-foreground">across {openJobs.filter(j => (j.application_count ?? 0) > 0).length} open job{openJobs.filter(j => (j.application_count ?? 0) > 0).length > 1 ? 's' : ''}</p>
              </div>
            </div>
            <ArrowRight className="size-5 text-primary" />
          </div>
        </Link>
      )}

      {/* Stat Grid */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Open Posts"
          value={openJobs.length}
          icon={<Briefcase className="size-5" />}
          accent="primary"
          href="/steps/jobs"
          subtitle={`of ${jobs.length} total`}
        />
        <StatCard
          label="Applicants"
          value={totalApplicants}
          icon={<Users className="size-5" />}
          accent={totalApplicants > 0 ? 'success' : 'muted'}
          href="/steps/offers"
          subtitle="awaiting review"
        />
        <StatCard
          label="Completed"
          value={completedContracts.length}
          icon={<CheckCircle2 className="size-5" />}
          accent="muted"
          subtitle="all time"
        />
        <StatCard
          label="Avg Rating"
          value={(reviews?.average_rating ?? 0).toFixed(1)}
          icon={<Star className="size-5" />}
          accent={(reviews?.average_rating ?? 0) >= 4 ? 'success' : 'muted'}
          subtitle={`${reviews?.items?.length ?? 0} reviews`}
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
              <p className="text-sm font-semibold">New Post</p>
              <p className="text-[10px] text-muted-foreground">Create a job listing</p>
            </div>
          </div>
        </Link>
        <Link href="/steps/offers">
          <div className="neu neu-hover rounded-xl p-4 flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-muted">
              <Users className="size-5 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold">Applicants</p>
              <p className="text-[10px] text-muted-foreground">Review & accept</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Recent Job Posts */}
      <div className="neu rounded-2xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display text-sm font-semibold tracking-wide">Recent Posts</h2>
          <Link href="/steps/jobs" className="text-[10px] text-primary font-medium hover:underline flex items-center gap-0.5">
            Manage all <ArrowRight className="size-3" />
          </Link>
        </div>
        {recentJobs.length === 0 ? (
          <div className="neu-inset rounded-xl p-8 text-center">
            <Briefcase className="size-8 text-muted-foreground/20 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">No posts yet</p>
            <Button asChild variant="outline" size="sm" className="mt-3 min-h-[36px]">
              <Link href="/steps/jobs">Create your first post</Link>
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
                    {job.status === 'open' ? 'Open' : job.status === 'filled' ? 'Filled' : 'Closed'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tier Progress */}
      {tier && tier.next_tier && tier.missing_requirements.length > 0 && (
        <div className="neu rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="size-4 text-primary" />
            <h2 className="font-display text-sm font-semibold tracking-wide">Tier Progress</h2>
          </div>
          <div className="space-y-2">
            {tier.missing_requirements.map((req, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary/40" />
                <span className="text-muted-foreground">{req}</span>
              </div>
            ))}
          </div>
        </div>
      )}
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
          <p className="mt-5 font-display text-sm font-medium text-muted-foreground tracking-wide">Loading...</p>
        </div>
      </div>
    );
  }

  const isInstructor = user?.role === 'instructor';

  return isInstructor ? <InstructorDashboard /> : <StudioDashboard />;
}
