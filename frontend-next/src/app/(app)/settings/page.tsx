'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useAuthStore } from '@/stores/auth-store';
import { useLogout } from '@/hooks/use-auth';
import api from '@/lib/api-client';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle, Crown, Check, Loader2, Mail, UserCircle } from 'lucide-react';
import { TierCard } from '@/components/trust/tier-card';

// ---------------------------------------------------------------------------
// Premium benefits
// ---------------------------------------------------------------------------

const PRO_BENEFITS = [
  'All regions for applications/posts',
  'Unlimited urgent job access',
  'Unlimited daily applications',
];

// ---------------------------------------------------------------------------
// Upgrade button with depositor name dialog
// ---------------------------------------------------------------------------

function UpgradeButton({ onUpgrade, isPending }: { onUpgrade: (name: string) => void; isPending: boolean }) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [depositorName, setDepositorName] = useState('');

  return (
    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
      <DialogTrigger asChild>
        <Button className="min-h-[48px] w-full text-base font-display font-semibold">
          Subscribe to Premium
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="font-display">Premium Subscription</DialogTitle>
          <DialogDescription>
            Enter your depositor name to receive bank transfer instructions.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="depositor-name">Depositor Name</Label>
            <Input
              id="depositor-name"
              placeholder="Full name"
              className="min-h-[44px]"
              value={depositorName}
              onChange={(e) => setDepositorName(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            disabled={isPending || !depositorName.trim()}
            onClick={() => {
              onUpgrade(depositorName.trim());
              setDialogOpen(false);
            }}
          >
            {isPending ? <Loader2 className="mr-1 size-4 animate-spin" /> : null}
            {isPending ? 'Processing...' : 'Request Transfer'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function SettingsPage() {
  const { user } = useAuthStore();
  const logout = useLogout();
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const tierQuery = useQuery({
    queryKey: ['my-tier'],
    queryFn: () => api.tier.getMyTier(),
  });
  const subQuery = useQuery({
    queryKey: ['my-subscription'],
    queryFn: () => api.subscriptions.getStatus(),
  });

  const bankTransferMutation = useMutation({
    mutationFn: (name: string) => api.subscriptions.initBankTransfer({ depositor_name: name }),
    onSuccess: () => {
      toast.success('Transfer request submitted. Auto-activated after confirmation.');
    },
    onError: () => toast.error('Request failed. Please try again.'),
  });

  const cancelSubMutation = useMutation({
    mutationFn: () => api.subscriptions.cancel(),
    onSuccess: () => {
      toast.success('Subscription cancelled.');
      subQuery.refetch();
      tierQuery.refetch();
    },
    onError: () => toast.error('Cancellation failed.'),
  });

  const isPremium = subQuery.data?.has_subscription === true;

  const handleDelete = async () => {
    if (!password.trim()) {
      setError('Please enter your password.');
      return;
    }

    setError(null);
    setIsDeleting(true);
    try {
      const res = await fetch('/api/v1/auth/users/me', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ password }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const message =
          typeof body.detail === 'string'
            ? body.detail
            : body.detail?.message || 'Account deletion failed.';
        throw new Error(message);
      }

      logout.mutate();
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Account deletion failed.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-up">
      <h1 className="font-display text-2xl font-bold tracking-tight">Settings</h1>

      {/* Account info */}
      <Card>
        <CardHeader>
          <CardTitle className="font-display">Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-muted">
              <Mail className="size-4 text-muted-foreground" />
            </div>
            <div>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-display">Email</p>
              <p className="font-medium">{user?.email}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-muted">
              <UserCircle className="size-4 text-muted-foreground" />
            </div>
            <div>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-display">Role</p>
              <p className="font-medium">{user?.role === 'instructor' ? 'Instructor' : 'Studio'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tier card */}
      {tierQuery.data && <TierCard data={tierQuery.data} />}

      {/* Subscription */}
      <Card className={isPremium ? 'border-amber-300/50 dark:border-amber-700/50' : 'border-primary/20'}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="font-display flex items-center gap-2">
              <Crown className="size-5 text-amber-500" />
              Subscription
            </CardTitle>
            {isPremium ? (
              <Badge className="bg-amber-500 text-white hover:bg-amber-600 font-display text-[10px] uppercase tracking-wider">Active</Badge>
            ) : (
              <Badge variant="outline" className="font-display text-[10px] uppercase tracking-wider">Free</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {isPremium ? (
            <div className="space-y-3">
              <p className="text-sm">
                <span className="font-display text-2xl font-bold">9,900</span>
                <span className="ml-1 text-muted-foreground">KRW/month</span>
                <span className="ml-2 text-xs text-muted-foreground">
                  Next: {subQuery.data?.subscription?.next_billing_date?.slice(0, 10) ?? '-'}
                </span>
              </p>
              <Button
                variant="outline"
                size="sm"
                className="min-h-[44px]"
                onClick={() => cancelSubMutation.mutate()}
                disabled={cancelSubMutation.isPending}
              >
                {cancelSubMutation.isPending ? 'Cancelling...' : 'Cancel Subscription'}
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-xl bg-muted/40 p-4 space-y-2.5">
                {PRO_BENEFITS.map((b) => (
                  <div key={b} className="flex items-start gap-2.5 text-sm">
                    <div className="mt-0.5 flex size-5 items-center justify-center rounded-md bg-primary/10">
                      <Check className="size-3 text-primary" />
                    </div>
                    <span>{b}</span>
                  </div>
                ))}
              </div>
              <div className="text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-display mb-1">Monthly</p>
                <p className="font-display text-3xl font-bold">9,900<span className="text-base font-normal text-muted-foreground ml-0.5">KRW</span></p>
              </div>
              <UpgradeButton
                onUpgrade={(name) => bankTransferMutation.mutate(name)}
                isPending={bankTransferMutation.isPending}
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Button
        variant="outline"
        className="w-full min-h-[44px] font-display"
        onClick={() => logout.mutate()}
      >
        Sign Out
      </Button>

      {/* Danger zone */}
      <Card className="border-destructive/30">
        <CardHeader>
          <CardTitle className="font-display text-destructive">Delete Account</CardTitle>
          <CardDescription>
            All data will be permanently deleted. This action cannot be undone.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button variant="destructive" className="font-display">Delete Account</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="font-display">Confirm Deletion</DialogTitle>
                <DialogDescription asChild>
                  <div className="space-y-2">
                    <p>Please review before proceeding:</p>
                    <ul className="list-inside list-disc space-y-1 text-sm">
                      <li>Recovery possible within 30 days</li>
                      <li>Active contracts will be cancelled</li>
                      <li>Posts and applications will be deleted</li>
                    </ul>
                  </div>
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-3">
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Enter your password to confirm.
                  </AlertDescription>
                </Alert>

                <div className="space-y-2">
                  <Label htmlFor="delete-password">Password</Label>
                  <Input
                    id="delete-password"
                    type="password"
                    placeholder="Enter password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>

                {error && (
                  <p className="text-sm text-destructive">{error}</p>
                )}
              </div>

              <DialogFooter className="gap-2 sm:gap-0">
                <Button
                  variant="outline"
                  onClick={() => {
                    setOpen(false);
                    setPassword('');
                    setError(null);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                  disabled={isDeleting || !password.trim()}
                >
                  {isDeleting ? 'Deleting...' : 'Delete'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
