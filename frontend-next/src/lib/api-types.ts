/**
 * TypeScript interfaces matching backend Pydantic schemas.
 * Generated from backend/app/schemas/ definitions.
 *
 * Convention:
 *  - Request types end with "Request" or "Create" or "Update"
 *  - Response types end with "Response"
 *  - Enum-like unions use `type` aliases
 */

// ---------------------------------------------------------------------------
// Enums (string literal unions)
// ---------------------------------------------------------------------------

export type UserRole = 'instructor' | 'studio' | 'admin';
export type MembershipTier = 'free' | 'premium';
export type Category = 'pilates' | 'yoga';
export type JobType = 'substitute' | 'regular' | 'contract';
export type JobPostStatus = 'open' | 'closed' | 'filled';
export type ApplicationStatus = 'pending' | 'accepted' | 'rejected' | 'withdrawn';
export type OfferStatus = 'pending' | 'accepted' | 'rejected' | 'expired';
export type ContractStatus =
  | 'confirmed'
  | 'in_progress'
  | 'pending_completion'
  | 'completed'
  | 'disputed'
  | 'cancelled';
export type SubscriptionStatus =
  | 'inactive'
  | 'active'
  | 'cancelled'
  | 'expired'
  | 'suspended';
export type ThreadScope = 'job' | 'contract';
export type MessageType = 'text' | 'system';
export type TicketStatus = 'open' | 'in_progress' | 'resolved' | 'closed';

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface SignupRequest {
  email: string;
  password: string;
  role: UserRole;
  display_name?: string;
  business_name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  no_show_count: number;
  is_suspended: boolean;
  display_name?: string | null;
  business_name?: string | null;
  phone_verified: boolean;
  identity_verified: boolean;
  business_verified: boolean;
  trust_score: number;
  tier?: string | null;
  suspension_until?: string | null;
  restriction_until?: string | null;
  last_active_at?: string | null;
  onboarding_completed: boolean;
}

export interface MeResponse {
  user: UserResponse;
  profile_id?: string | null;
}

// ---------------------------------------------------------------------------
// Instructor Profile
// ---------------------------------------------------------------------------

export interface Certification {
  name: string;
  issuer?: string | null;
  year?: number | null;
  is_verified: boolean;
}

export interface InstructorProfileUpdate {
  display_name?: string;
  bio?: string;
  phone?: string;
  profile_image_url?: string;
  categories?: string[];
  specialties?: string[];
  certifications?: (Certification | string)[];
  experience_years?: number;
  available_regions?: string[];
  is_public?: boolean;
  teaching_style?: Record<string, string>;
}

export interface InstructorProfileResponse {
  id: string;
  user_id: string;
  display_name: string;
  bio?: string | null;
  phone?: string | null;
  profile_image_url?: string | null;
  categories: string[];
  specialties: string[];
  certifications: (Certification | string)[];
  experience_years: number;
  available_regions: string[];
  is_public: boolean;
  rating_average: number;
  review_count: number;
  verified_cert_count: number;
  teaching_style?: Record<string, string> | null;
}

// ---------------------------------------------------------------------------
// Studio Profile
// ---------------------------------------------------------------------------

export interface StudioProfileUpdate {
  business_name?: string;
  description?: string;
  phone?: string;
  address?: string;
  region?: string;
  latitude?: number;
  longitude?: number;
  logo_url?: string;
  categories?: string[];
}

export interface StudioProfileResponse {
  id: string;
  user_id: string;
  business_name: string;
  description?: string | null;
  phone?: string | null;
  address?: string | null;
  region?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  logo_url?: string | null;
  categories: string[];
  is_verified: boolean;
  rating_average: number;
  review_count: number;
}

// ---------------------------------------------------------------------------
// Job Posts
// ---------------------------------------------------------------------------

export interface JobPostCreate {
  title: string;
  description?: string;
  category: Category;
  job_type: JobType;
  date: string; // ISO date (YYYY-MM-DD)
  start_time: string; // HH:MM
  end_time: string; // HH:MM
  hourly_rate: number;
  total_sessions?: number;
  required_experience_years?: number;
  required_certifications?: string[];
  region?: string;
  address?: string;
  latitude?: number | null;
  longitude?: number | null;
  is_urgent?: boolean;
  payment_method?: string;
  terms_agreed?: boolean;
  preferred_style?: Record<string, string>;
  // Handoff note (required)
  handoff_class_topic: string;
  handoff_class_sequence_info: string;
  handoff_atmosphere_preference: string;
  handoff_member_notes: string;
  handoff_equipment_notes: string;
}

export interface JobPostResponse {
  id: string;
  studio_id: string;
  title: string;
  description?: string | null;
  category: Category;
  job_type: JobType;
  status: JobPostStatus;
  date: string;
  start_time: string;
  end_time: string;
  hourly_rate: number;
  total_sessions: number;
  required_experience_years: number;
  required_certifications: string[];
  region?: string | null;
  address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  is_urgent: boolean;
  distance_km?: number | null;
  distance_text?: string | null;
  travel_time_min?: number | null;
  is_past: boolean;
  application_count: number;
  payment_method?: string | null;
  terms_agreed?: boolean;
  created_at: string;
  updated_at: string;
  // Studio info (populated in list endpoints)
  studio_name?: string | null;
  studio_rating?: number | null;
  has_handoff_note?: boolean;
  preferred_style?: Record<string, string> | null;
}

export interface MatchingBreakdownItem {
  score: number;
  weight: number;
}

export interface MatchingScore {
  total: number;
  breakdown: Record<string, MatchingBreakdownItem>;
}

export interface JobPostWithMatchingItem {
  job: JobPostResponse;
  matching: MatchingScore;
  is_premium: boolean;
  is_urgent: boolean;
  distance_km?: number | null;
  distance_text?: string | null;
  travel_time_min?: number | null;
  // Premium-gated fields
  application_count: number;
  early_access_locked: boolean;
  studio_avg_response_hours?: number | null;
}

export interface JobPostListResponse {
  items: JobPostResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface JobPostWithMatchingListResponse {
  items: JobPostWithMatchingItem[];
  total: number;
  page: number;
  page_size: number;
}

// ---------------------------------------------------------------------------
// Applications
// ---------------------------------------------------------------------------

export interface ApplicationCreate {
  cover_letter?: string;
}

export interface ApplicationResponse {
  id: string;
  job_post_id: string;
  instructor_id: string;
  status: ApplicationStatus;
  cover_letter?: string | null;
  contact_revealed: boolean;
  contact_revealed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationWithJobResponse extends ApplicationResponse {
  job_title?: string | null;
  studio_name?: string | null;
  studio_phone?: string | null;    // Only when contact_revealed=true
  studio_address?: string | null;  // Only when contact_revealed=true
}

export interface ApplicationWithInstructorResponse extends ApplicationResponse {
  instructor_name?: string | null;
  instructor_phone?: string | null;
  instructor_experience_years?: number | null;
  instructor_categories?: string[] | null;
  instructor_rating?: number | null;
  has_offer: boolean;
  is_premium: boolean;
  contact_revealed: boolean;
  instructor_full_phone?: string | null;
  studio_phone?: string | null;
  studio_name?: string | null;
  instructor_completed_substitutes: number;
  instructor_no_show_count: number;
  instructor_review_count: number;
  instructor_tier?: string | null;
  instructor_tier_label?: string | null;
}

export interface ContactRevealResponse {
  application_id: string;
  instructor_phone: string;
  instructor_name: string;
  studio_phone: string;
  studio_name: string;
  studio_address?: string | null;
  message: string;
}

// ---------------------------------------------------------------------------
// Offers
// ---------------------------------------------------------------------------

export interface OfferCreate {
  application_id?: string;
  instructor_id?: string;
  message?: string;
  proposed_rate: number;
}

export interface OfferResponse {
  id: string;
  application_id?: string | null;
  studio_id: string;
  instructor_id: string;
  status: OfferStatus;
  message?: string | null;
  proposed_rate: number;
  expires_at?: string | null;
  created_at: string;
  updated_at: string;
  // Populated fields
  studio_name?: string | null;
  job_title?: string | null;
}

// ---------------------------------------------------------------------------
// Offers (list response)
// ---------------------------------------------------------------------------

export interface OfferListResponse {
  items: OfferResponse[];
  total: number;
}

// ---------------------------------------------------------------------------
// Contracts
// ---------------------------------------------------------------------------

export interface ContractResponse {
  id: string;
  offer_id: string;
  studio_id: string;
  instructor_id: string;
  status: ContractStatus;
  hourly_rate: number;
  total_amount: number;
  total_sessions: number;
  date: string;
  start_time: string;
  end_time: string;
  instructor_name?: string | null;
  studio_name?: string | null;
  instructor_signed_at?: string | null;
  studio_signed_at?: string | null;
  studio_confirmed_at?: string | null;
  instructor_confirmed_at?: string | null;
  platform_fee?: number | null;
  settlement_amount?: number | null;
  cancellation_reason?: string | null;
  cancelled_by_user_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContractListResponse {
  items: ContractResponse[];
  total: number;
}

export interface ContractCancelRequest {
  reason: string;
}

// ---------------------------------------------------------------------------
// Reviews
// ---------------------------------------------------------------------------

export interface ReviewCreate {
  rating: number;
  comment?: string;
  time_punctuality?: boolean;
  professionalism?: boolean;
  would_rehire?: boolean;
}

export interface ReviewResponse {
  id: string;
  application_id?: string | null;
  contract_id?: string | null;
  reviewer_user_id: string;
  reviewee_instructor_id?: string | null;
  reviewee_studio_id?: string | null;
  rating: number;
  comment?: string | null;
  time_punctuality?: boolean | null;
  professionalism?: boolean | null;
  would_rehire?: boolean | null;
  created_at: string;
  updated_at?: string | null;
  // Populated by backend
  reviewer_name?: string | null;
  reviewee_name?: string | null;
  job_date?: string | null;
}

export interface ReviewListResponse {
  items: ReviewResponse[];
  total: number;
  average_rating?: number | null;
}

export interface ReviewEligibility {
  application_id: string;
  review_eligible: boolean;
  review_expired: boolean;
  has_written: boolean;
  both_reviewed: boolean;
  my_review?: ReviewResponse | null;
  partner_review?: ReviewResponse | null;
}

// ---------------------------------------------------------------------------
// Subscriptions
// ---------------------------------------------------------------------------

export interface SubscriptionResponse {
  id: string;
  user_id: string;
  tier: string;
  status: SubscriptionStatus;
  start_date?: string | null;
  end_date?: string | null;
  next_billing_date?: string | null;
  monthly_amount: number;
  auto_renew: boolean;
  cancelled_at?: string | null;
  created_at: string;
  updated_at: string;
  card_last_four?: string | null;
  card_company?: string | null;
  has_billing_key?: boolean;
}

export interface SubscriptionStatusResponse {
  has_subscription: boolean;
  membership_tier: MembershipTier;
  subscription?: SubscriptionResponse | null;
}

export interface UpgradeInitializeResponse {
  order_id: string;
  amount: number;
  subscription_id: string;
  client_key: string;
  customer_key?: string | null;
}

export interface BillingKeyRegisterResponse {
  success: boolean;
  card_last_four?: string | null;
  card_company?: string | null;
  message: string;
}

export interface BillingMethodResponse {
  has_billing_key: boolean;
  card_last_four?: string | null;
  card_company?: string | null;
}

export interface BankTransferUpgradeResponse {
  order_id: string;
  amount: number;
  bank_name: string;
  account_number: string;
  account_holder: string;
  depositor_name: string;
  expires_at: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Trust Tier (replaces old Trust Score)
// ---------------------------------------------------------------------------

export type TeacherTier = 't1_basic' | 't2_verified' | 't3_pro';
export type CenterTier = 'c1_basic' | 'c2_verified';
export type PenaltyTypeEnum = 'no_show' | 'same_day_cancel' | 'late' | 'cancel_after_confirm';

export interface TierResponse {
  tier: string;
  tier_label: string;
  tier_label_ko: string;
  tier_color: string;
  role: string;
  completed_jobs_recent: number;
  no_show_recent: number;
  same_day_cancel_recent: number;
  late_recent: number;
  cancel_after_confirm_recent: number;
  next_tier: string | null;
  missing_requirements: string[];
}

export interface TierPublicResponse {
  user_id: string;
  tier: string;
  tier_label: string;
  tier_color: string;
  role: string;
  completed_jobs_recent: number;
  no_show_recent: number;
}

export interface TierRequirementsResponse {
  teacher_tiers: TierRequirementItem[];
  center_tiers: TierRequirementItem[];
}

export interface TierRequirementItem {
  tier: string;
  label: string;
  label_ko: string;
  requirements: string[];
  limits: Record<string, number>;
}

export interface PenaltyReportRequest {
  reported_user_id: string;
  penalty_type: PenaltyTypeEnum;
  description?: string;
}

export interface PenaltyRecordResponse {
  id: string;
  user_id: string;
  penalty_type: string;
  status: string;
  reported_by?: string | null;
  suspend_until?: string | null;
  restrict_until?: string | null;
  description?: string | null;
  created_at: string;
}

export interface MarkPaidRequest {
  amount: number;
}

export interface PaymentConfirmationResponse {
  id: string;
  application_id: string;
  center_user_id: string;
  instructor_user_id: string;
  amount: number;
  status: string;
  center_marked_paid_at?: string | null;
  instructor_confirmed_at?: string | null;
  dispute_reason?: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Verification
// ---------------------------------------------------------------------------

export interface VerificationStatusResponse {
  phone_verified: boolean;
  identity_verified: boolean;
  business_verified: boolean;
}

// ---------------------------------------------------------------------------
// Profile Completeness
// ---------------------------------------------------------------------------

export interface CertUploadResponse {
  certification: {
    name: string;
    issuer: string;
    file_url: string;
    is_verified: boolean;
    confidence?: number;
    verification_reason?: string;
  };
  verification: {
    is_valid: boolean | null;
    confidence: number | null;
    reason: string;
    auto_approved: boolean;
  };
}

export interface ProfileCompletenessResponse {
  percentage: number;
  is_complete: boolean;
  missing_fields: string[];
  missing_fields_display?: Record<string, string>;
  message?: string;
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export interface ThreadCreate {
  scope: ThreadScope;
  job_post_id?: string;
  contract_id?: string;
  instructor_id: string;
}

export interface MessageResponse {
  id: string;
  thread_id: string;
  sender_user_id?: string | null;
  message_type: MessageType;
  content: string;
  is_read: boolean;
  created_at: string;
}

export interface ThreadResponse {
  id: string;
  scope: ThreadScope;
  job_post_id?: string | null;
  contract_id?: string | null;
  studio_id: string;
  instructor_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_message?: MessageResponse | null;
}

// ---------------------------------------------------------------------------
// Support
// ---------------------------------------------------------------------------

export interface SupportTicketCreate {
  subject: string;
  description: string;
}

export interface SupportTicketResponse {
  id: string;
  user_id: string;
  subject: string;
  description: string;
  status: TicketStatus;
  resolution_note?: string | null;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Application Templates
// ---------------------------------------------------------------------------

export interface ApplicationTemplateResponse {
  id: string;
  user_id: string;
  name: string;
  content: string;
  is_default: boolean;
  use_count: number;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Daily Usage (deprecated -- removed with Trust Tier pivot)
// ---------------------------------------------------------------------------

// export interface DailyUsageResponse {
//   daily_applications_today: number;
//   daily_views_today: number;
//   last_usage_reset_date: string;
//   application_limit: number;
//   view_limit: number;
//   is_premium: boolean;
// }

// ---------------------------------------------------------------------------
// Handoff Notes
// ---------------------------------------------------------------------------

export interface HandoffNoteCreate {
  class_topic?: string;
  class_sequence_info?: string;
  atmosphere_preference?: string;
  additional_notes?: string;
  member_notes?: string;
  equipment_notes?: string;
}

export interface HandoffNotePublicResponse {
  id: string;
  job_post_id: string;
  class_topic?: string | null;
  class_sequence_info?: string | null;
  atmosphere_preference?: string | null;
  additional_notes?: string | null;
  has_sensitive_info: boolean;
  created_at: string;
  updated_at: string;
}

export interface HandoffNoteFullResponse extends HandoffNotePublicResponse {
  member_notes?: string | null;
  equipment_notes?: string | null;
}

// ---------------------------------------------------------------------------
// Teaching Style
// ---------------------------------------------------------------------------

export interface TeachingStyle {
  correction_style?: string;
  class_atmosphere?: string;
  intensity_level?: string;
  music_preference?: string;
}

// ---------------------------------------------------------------------------
// Backup Instructors
// ---------------------------------------------------------------------------

export interface BackupInstructorCreate {
  instructor_id: string;
  nickname?: string;
  note?: string;
  priority?: number;
}

export interface BackupInstructorUpdate {
  nickname?: string;
  note?: string;
  priority?: number;
}

export interface BackupInstructorResponse {
  id: string;
  studio_id: string;
  instructor_id: string;
  nickname?: string | null;
  note?: string | null;
  priority: number;
  last_worked_at?: string | null;
  total_completed: number;
  instructor_name?: string | null;
  instructor_phone?: string | null;
  instructor_categories?: string[] | null;
  instructor_rating?: number | null;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// API Error
// ---------------------------------------------------------------------------

export interface APIErrorResponse {
  code: string;
  message: string;
}
