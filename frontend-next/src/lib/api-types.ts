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
  hourly_rate_min?: number;
  hourly_rate_max?: number;
  available_regions?: string[];
  is_public?: boolean;
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
  hourly_rate_min?: number | null;
  hourly_rate_max?: number | null;
  available_regions: string[];
  is_public: boolean;
  rating_average: number;
  review_count: number;
  verified_cert_count: number;
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
  created_at: string;
  updated_at: string;
  // Studio info (populated in list endpoints)
  studio_name?: string | null;
  studio_rating?: number | null;
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
}

export interface ReviewResponse {
  id: string;
  contract_id: string;
  reviewer_user_id: string;
  reviewee_instructor_id?: string | null;
  reviewee_studio_id?: string | null;
  rating: number;
  comment?: string | null;
  created_at: string;
  updated_at?: string | null;
  // Populated
  reviewer_name?: string | null;
}

export interface ReviewListResponse {
  items: ReviewResponse[];
  total: number;
  average_rating?: number | null;
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
// Trust Score
// ---------------------------------------------------------------------------

export interface TrustScoreFactorLabel {
  name: string;
  max: number;
}

export interface TrustScoreLevelThreshold {
  min: number;
  max: number;
  level: string;
  color: string;
}

export interface ExperienceBadge {
  label: string;
  tier: string;
}

export interface TrustScoreResponse {
  score: number;
  level: string;
  level_color: string;
  breakdown: Record<string, number>;
  recommendations: string[];
  points_to_next_level: number;
  next_level_score: number;
  factor_labels: Record<string, TrustScoreFactorLabel>;
  level_thresholds: TrustScoreLevelThreshold[];
  completed_contracts_count: number;
  experience_badge?: ExperienceBadge | null;
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
// Daily Usage
// ---------------------------------------------------------------------------

export interface DailyUsageResponse {
  daily_applications_today: number;
  daily_views_today: number;
  last_usage_reset_date: string;
  application_limit: number;
  view_limit: number;
  is_premium: boolean;
}

// ---------------------------------------------------------------------------
// API Error
// ---------------------------------------------------------------------------

export interface APIErrorResponse {
  code: string;
  message: string;
}
