import type {
  SignupRequest,
  TokenResponse,
  MeResponse,
  InstructorProfileResponse,
  InstructorProfileUpdate,
  StudioProfileResponse,
  StudioProfileUpdate,
  JobPostCreate,
  JobPostResponse,
  JobPostListResponse,
  JobPostWithMatchingListResponse,
  ApplicationCreate,
  ApplicationResponse,
  ApplicationWithJobResponse,
  ApplicationWithInstructorResponse,
  ContactRevealResponse,
  OfferCreate,
  OfferResponse,
  OfferListResponse,
  ContractResponse,
  ContractListResponse,
  ContractCancelRequest,
  ReviewCreate,
  ReviewResponse,
  ReviewListResponse,
  ReviewEligibility,
  SubscriptionStatusResponse,
  UpgradeInitializeResponse,
  BillingKeyRegisterResponse,
  BillingMethodResponse,
  BankTransferUpgradeResponse,
  TierResponse,
  TierPublicResponse,
  TierRequirementsResponse,
  PenaltyReportRequest,
  PenaltyRecordResponse,
  MarkPaidRequest,
  PaymentConfirmationResponse,
  VerificationStatusResponse,
  ProfileCompletenessResponse,
  CertUploadResponse,
  // PMF pivot: Chat disabled -- contact reveal replaces in-app chat
  // ThreadCreate,
  // ThreadResponse,
  // MessageResponse,
  SupportTicketCreate,
  SupportTicketResponse,
  // PMF pivot: Application templates disabled
  // ApplicationTemplateResponse,
  // Daily usage removed with Trust Tier pivot
  // DailyUsageResponse,
  HandoffNoteCreate,
  HandoffNotePublicResponse,
  HandoffNoteFullResponse,
  BackupInstructorCreate,
  BackupInstructorUpdate,
  BackupInstructorResponse,
  APIErrorResponse,
} from './api-types';
import { isNativePlatform, getAccessToken } from './token-manager';

export class APIError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.code = code;
  }
}

const BASE_URL = '/api/v1';
const MAX_RETRIES = 3;
const RETRY_DELAYS = [1000, 2000];

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const native = isNativePlatform();
  const baseUrl = native
    ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1'
    : BASE_URL;
  const url = `${baseUrl}${path}`;

  const defaultHeaders: Record<string, string> = {};
  if (options.body && typeof options.body === 'string') {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  // Native app: add Bearer token; Web: use cookies
  if (native) {
    const token = await getAccessToken();
    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  const config: RequestInit = {
    ...options,
    ...(native ? {} : { credentials: 'include' as RequestCredentials }),
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  let lastError: Error | null = null;

  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const detail = body.detail as APIErrorResponse | string | undefined;
        const code = typeof detail === 'object' ? detail.code : 'UNKNOWN';
        const message = typeof detail === 'object'
          ? detail.message
          : typeof detail === 'string'
            ? detail
            : `HTTP ${response.status}`;
        throw new APIError(response.status, code, message);
      }

      // 204 No Content
      if (response.status === 204) {
        return undefined as T;
      }

      return await response.json() as T;
    } catch (error) {
      lastError = error as Error;

      // 401 Unauthorized → session expired, redirect to login
      if (error instanceof APIError && error.status === 401) {
        if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
          window.location.href = `/login?callbackUrl=${encodeURIComponent(window.location.pathname)}`;
        }
        throw error;
      }

      // Don't retry client errors (4xx)
      if (error instanceof APIError && error.status >= 400 && error.status < 500) {
        throw error;
      }

      // Wait before retry (except last attempt)
      if (attempt < MAX_RETRIES - 1) {
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAYS[attempt] || 2000));
      }
    }
  }

  throw lastError || new Error('Request failed');
}

function get<T>(path: string) {
  return request<T>(path, { method: 'GET' });
}

function post<T>(path: string, body?: unknown) {
  return request<T>(path, {
    method: 'POST',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

function put<T>(path: string, body?: unknown) {
  return request<T>(path, {
    method: 'PUT',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

function del<T>(path: string) {
  return request<T>(path, { method: 'DELETE' });
}

function patch<T>(path: string, body?: unknown) {
  return request<T>(path, {
    method: 'PATCH',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

// --- Auth ------------------------------------------------

export const auth = {
  /** Sign up (called via BFF route, not directly) */
  signup: (data: SignupRequest) =>
    post<TokenResponse>('/auth/signup', data),

  /** Login (called via BFF route, not directly) */
  login: (data: { email: string; password: string }) =>
    post<TokenResponse>('/auth/login', data),

  /** Get current user */
  me: () => get<MeResponse>('/auth/me'),
};

// --- Profiles --------------------------------------------

export const instructors = {
  getMyProfile: () =>
    get<InstructorProfileResponse>('/instructors/me'),

  updateMyProfile: (data: InstructorProfileUpdate) =>
    put<InstructorProfileResponse>('/instructors/me', data),

  getProfile: (id: string) =>
    get<InstructorProfileResponse>(`/instructors/${id}`),
};

export const studios = {
  getMyProfile: () =>
    get<StudioProfileResponse>('/studios/me'),

  updateMyProfile: (data: StudioProfileUpdate) =>
    put<StudioProfileResponse>('/studios/me', data),

  getProfile: (id: string) =>
    get<StudioProfileResponse>(`/studios/${id}`),
};

// --- Job Posts -------------------------------------------

export const jobPosts = {
  create: (data: JobPostCreate) =>
    post<JobPostResponse>('/job-posts', data),

  list: (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return get<JobPostListResponse>(`/job-posts${query}`);
  },

  listMine: () =>
    get<JobPostListResponse>('/job-posts/mine'),

  listWithMatching: (params?: Record<string, string> & {
    user_latitude?: string;
    user_longitude?: string;
    max_distance_km?: string;
  }) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return get<JobPostWithMatchingListResponse>(`/job-posts/for-me/with-matching${query}`);
  },

  get: (id: string) =>
    get<JobPostResponse>(`/job-posts/${id}`),

  update: (id: string, data: Partial<JobPostCreate>) =>
    put<JobPostResponse>(`/job-posts/${id}`, data),

  delete: (id: string) =>
    del<void>(`/job-posts/${id}`),
};

// --- Applications ----------------------------------------

export const applications = {
  apply: (jobPostId: string, data?: ApplicationCreate) =>
    post<ApplicationResponse>(`/job-posts/${jobPostId}/applications`, data || {}),

  getMyApplications: () =>
    get<{ items: ApplicationWithJobResponse[]; total: number }>('/applications/me'),

  withdraw: (id: string) =>
    post<ApplicationResponse>(`/applications/${id}/withdraw`),

  getForJobPost: (jobPostId: string) =>
    get<{ items: ApplicationWithInstructorResponse[]; total: number }>(`/job-posts/${jobPostId}/applications`),

  /** Accept application and reveal contact info (PMF pivot: replaces offer flow for urgent) */
  accept: (applicationId: string) =>
    post<ContactRevealResponse>(`/applications/${applicationId}/accept`),
};

// --- Offers ----------------------------------------------

export const offers = {
  create: (data: OfferCreate) =>
    post<OfferResponse>('/offers', data),

  getMyOffers: () =>
    get<OfferListResponse>('/offers/me'),

  accept: (id: string) =>
    post<OfferResponse>(`/offers/${id}/accept`),

  reject: (id: string) =>
    post<OfferResponse>(`/offers/${id}/reject`),
};

// --- Contracts -------------------------------------------

export const contracts = {
  createFromOffer: (offerId: string) =>
    post<ContractResponse>(`/contracts/from-offer/${offerId}`),

  getMyContracts: () =>
    get<ContractListResponse>('/contracts/me'),

  setInProgress: (id: string) =>
    post<ContractResponse>(`/contracts/${id}/set-in-progress`),

  confirmCompletion: (id: string) =>
    post<ContractResponse>(`/contracts/${id}/confirm-completion`),

  cancel: (id: string, data: ContractCancelRequest) =>
    post<ContractResponse>(`/contracts/${id}/cancel`, data),

  reportNoShow: (id: string, reportedUserId: string) =>
    post<ContractResponse>(`/contracts/${id}/report-no-show`, { reported_user_id: reportedUserId }),
};

// --- Reviews ---------------------------------------------

export const reviews = {
  create: (applicationId: string, data: ReviewCreate) =>
    post<ReviewResponse>(`/applications/${applicationId}/reviews`, data),

  getEligibility: (applicationId: string) =>
    get<ReviewEligibility>(`/applications/${applicationId}/reviews`),

  getMyReviewForApplication: (applicationId: string) =>
    get<ReviewResponse>(`/applications/${applicationId}/reviews/my`),

  update: (id: string, data: ReviewCreate) =>
    put<ReviewResponse>(`/reviews/${id}`, data),

  delete: (id: string) =>
    del<void>(`/reviews/${id}`),

  getReceived: () =>
    get<ReviewListResponse>('/reviews/received'),

  getWritten: () =>
    get<ReviewListResponse>('/reviews/written'),
};

// --- Subscriptions ---------------------------------------

export const subscriptions = {
  getStatus: () =>
    get<SubscriptionStatusResponse>('/subscriptions/me'),

  initializeUpgrade: () =>
    post<UpgradeInitializeResponse>('/subscriptions/upgrade'),

  confirmPayment: (data: { payment_key: string; order_id: string }) =>
    post<SubscriptionStatusResponse>('/subscriptions/confirm', data),

  cancel: (reason?: string) =>
    post<SubscriptionStatusResponse>('/subscriptions/cancel', reason ? { reason } : {}),

  getHistory: () =>
    get<unknown[]>('/subscriptions/history'),

  registerBillingKey: (data: { auth_key: string; customer_key: string }) =>
    post<BillingKeyRegisterResponse>('/subscriptions/billing/register', data),

  getBillingMethod: () =>
    get<BillingMethodResponse>('/subscriptions/billing'),

  removeBillingKey: () =>
    del<void>('/subscriptions/billing'),

  initBankTransfer: (data: { depositor_name: string }) =>
    post<BankTransferUpgradeResponse>('/subscriptions/upgrade/bank-transfer', data),
};

// --- Trust Tier ------------------------------------------

export const tier = {
  getMyTier: () =>
    get<TierResponse>('/tier/me'),

  getUserTier: (userId: string) =>
    get<TierPublicResponse>(`/tier/user/${userId}`),

  getRequirements: () =>
    get<TierRequirementsResponse>('/tier/requirements'),
};

// --- Penalties -------------------------------------------

export const penalties = {
  report: (data: PenaltyReportRequest) =>
    post<PenaltyRecordResponse>('/penalties/report', data),

  getMyPenalties: () =>
    get<{ items: PenaltyRecordResponse[]; total: number }>('/penalties/me'),
};

// --- Payment Confirmations -------------------------------

export const paymentConfirmations = {
  markPaid: (applicationId: string, data: MarkPaidRequest) =>
    post<PaymentConfirmationResponse>(`/applications/${applicationId}/mark-paid`, data),

  confirm: (id: string) =>
    post<PaymentConfirmationResponse>(`/payment-confirmations/${id}/confirm`),

  dispute: (id: string, reason: string) =>
    post<PaymentConfirmationResponse>(`/payment-confirmations/${id}/dispute`, { reason }),

  getMyConfirmations: () =>
    get<{ items: PaymentConfirmationResponse[] }>('/payment-confirmations/me'),
};

// --- Verification ----------------------------------------

export const verification = {
  requestPhone: (phone: string) =>
    post<{ message: string }>('/verification/phone/request', { phone }),

  verifyPhone: (phone: string, otp: string) =>
    post<{ message: string }>('/verification/phone/verify', { phone, otp }),

  verifyBusiness: (businessNumber: string) =>
    post<{ message: string }>('/verification/business/verify', { business_number: businessNumber }),

  getStatus: () =>
    get<VerificationStatusResponse>('/verification/status'),
};

// --- Profile Completeness --------------------------------

export const profileCompleteness = {
  get: () =>
    get<ProfileCompletenessResponse>('/profile/completeness'),

  checkAction: (action: string) =>
    get<{ allowed: boolean; reason?: string }>(`/profile/completeness/check/${action}`),

  uploadCertification: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<CertUploadResponse>('/profile/certifications', {
      method: 'POST',
      body: formData,
    });
  },
};

// --- Chat ------------------------------------------------
// PMF pivot: Chat disabled -- contact reveal replaces in-app chat
// export const chat = {
//   getThreads: () =>
//     get<ThreadResponse[]>('/threads'),
//
//   createThread: (data: ThreadCreate) =>
//     post<ThreadResponse>('/threads', data),
//
//   getMessages: (threadId: string) =>
//     get<MessageResponse[]>(`/threads/${threadId}/messages`),
//
//   sendMessage: (threadId: string, content: string) =>
//     post<MessageResponse>(`/threads/${threadId}/messages`, { content }),
// };

// --- Support ---------------------------------------------

export const support = {
  createTicket: (data: SupportTicketCreate) =>
    post<SupportTicketResponse>('/support/tickets', data),

  getMyTickets: () =>
    get<SupportTicketResponse[]>('/support/tickets/me'),
};

// --- Application Templates -------------------------------
// PMF pivot: Application templates disabled -- simplifying application flow
// export const applicationTemplates = {
//   list: () =>
//     get<ApplicationTemplateResponse[]>('/application-templates'),
//
//   create: (data: { name: string; content: string; is_default?: boolean }) =>
//     post<ApplicationTemplateResponse>('/application-templates', data),
//
//   update: (id: string, data: { name?: string; content?: string; is_default?: boolean }) =>
//     put<ApplicationTemplateResponse>(`/application-templates/${id}`, data),
//
//   delete: (id: string) =>
//     del<void>(`/application-templates/${id}`),
//
//   use: (id: string) =>
//     post<ApplicationTemplateResponse>(`/application-templates/${id}/use`),
//
//   getSuggestions: (jobType?: string) => {
//     const query = jobType ? `?job_type=${jobType}` : '';
//     return get<ApplicationTemplateResponse[]>(`/application-templates/suggestions${query}`);
//   },
// };

// --- Daily Usage -----------------------------------------
// Removed with Trust Tier pivot

// --- Handoff Notes ---------------------------------------

export const handoffNotes = {
  upsert: (jobPostId: string, data: HandoffNoteCreate) =>
    put<HandoffNoteFullResponse>(`/job-posts/${jobPostId}/handoff-note`, data),

  get: (jobPostId: string) =>
    get<HandoffNotePublicResponse | HandoffNoteFullResponse>(`/job-posts/${jobPostId}/handoff-note`),

  delete: (jobPostId: string) =>
    del<void>(`/job-posts/${jobPostId}/handoff-note`),
};

// --- Backup Instructors ----------------------------------

export const backupInstructors = {
  list: () =>
    get<{ items: BackupInstructorResponse[]; total: number }>('/studios/me/backup-instructors'),

  add: (data: BackupInstructorCreate) =>
    post<BackupInstructorResponse>('/studios/me/backup-instructors', data),

  update: (instructorId: string, data: BackupInstructorUpdate) =>
    patch<BackupInstructorResponse>(`/studios/me/backup-instructors/${instructorId}`, data),

  remove: (instructorId: string) =>
    del<void>(`/studios/me/backup-instructors/${instructorId}`),
};

// --- Convenience: grouped API ----------------------------

export const api = {
  auth,
  instructors,
  studios,
  jobPosts,
  applications,
  offers,
  contracts,
  reviews,
  subscriptions,
  tier,
  penalties,
  paymentConfirmations,
  verification,
  profileCompleteness,
  // PMF pivot: chat disabled -- contact reveal replaces in-app chat
  // chat,
  support,
  // PMF pivot: applicationTemplates disabled
  // applicationTemplates,
  // Daily usage removed with Trust Tier pivot
  // usage,
  handoffNotes,
  backupInstructors,
} as const;

export default api;
