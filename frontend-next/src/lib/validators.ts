/**
 * Zod v4 validation schemas for all form inputs.
 * Each schema exports a corresponding TypeScript type via z.infer.
 *
 * Naming convention:
 *  - Schema:  fooSchema
 *  - Type:    FooFormData
 */

import { z } from 'zod/v4';

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export const loginSchema = z.object({
  email: z.email('올바른 이메일을 입력해주세요'),
  password: z.string().min(1, '비밀번호를 입력해주세요'),
});

export type LoginFormData = z.infer<typeof loginSchema>;

export const signupSchema = z
  .object({
    email: z.email('올바른 이메일을 입력해주세요'),
    password: z.string().min(8, '비밀번호는 8자 이상이어야 합니다'),
    role: z.enum(['instructor', 'studio'], {
      message: '역할을 선택해주세요',
    }),
    display_name: z.string().optional(),
    business_name: z.string().optional(),
    terms_agreed: z.literal(true, {
      message: '이용약관에 동의해주세요',
    }),
    privacy_agreed: z.literal(true, {
      message: '개인정보 처리방침에 동의해주세요',
    }),
  })
  .refine(
    (data) => {
      if (data.role === 'instructor') return !!data.display_name?.trim();
      return true;
    },
    { message: '이름을 입력해주세요', path: ['display_name'] },
  )
  .refine(
    (data) => {
      if (data.role === 'studio') return !!data.business_name?.trim();
      return true;
    },
    { message: '업체명을 입력해주세요', path: ['business_name'] },
  );

export type SignupFormData = z.infer<typeof signupSchema>;

// ---------------------------------------------------------------------------
// Profiles
// ---------------------------------------------------------------------------

export const instructorProfileSchema = z.object({
  display_name: z.string().min(1, '활동명을 입력해주세요').max(100),
  bio: z
    .string()
    .min(1, '자기소개를 입력해주세요')
    .refine(
      (val) => val.split('\n').filter((line) => line.trim().length > 0).length >= 3,
      '자기소개는 최소 3줄 이상 작성해주세요',
    ),
  phone: z.string().optional(),
  categories: z.array(z.string()).min(1, '카테고리를 선택해주세요'),
  experience_years: z.number().min(0, '경력은 0년 이상이어야 합니다'),
  available_regions: z
    .array(z.string())
    .min(1, '활동 지역을 선택해주세요'),
});

export type InstructorProfileFormData = z.infer<
  typeof instructorProfileSchema
>;

export const studioProfileSchema = z.object({
  business_name: z.string().min(1, '업체명을 입력해주세요').max(200),
  description: z.string().optional(),
  phone: z.string().optional(),
  address: z.string().optional(),
  region: z.string().optional(),
  latitude: z.number().optional(),
  longitude: z.number().optional(),
  categories: z.array(z.string()).min(1, '카테고리를 선택해주세요'),
});

export type StudioProfileFormData = z.infer<typeof studioProfileSchema>;

// ---------------------------------------------------------------------------
// Job Posts
// ---------------------------------------------------------------------------

export const jobPostSchema = z.object({
  title: z.string().max(200).default(''),
  description: z.string().optional(),
  category: z.enum(['pilates', 'yoga'], {
    message: '카테고리를 선택해주세요',
  }),
  job_type: z.enum(['substitute', 'regular', 'contract'], {
    message: '유형을 선택해주세요',
  }),
  date: z.string().min(1, '날짜를 선택해주세요'),
  start_time: z.string().min(1, '시작 시간을 입력해주세요'),
  end_time: z.string().min(1, '종료 시간을 입력해주세요'),
  hourly_rate: z.number().min(10000, '시급은 10,000원 이상이어야 합니다'),
  total_sessions: z.number().min(1).default(1),
  required_experience_years: z.number().min(0).default(0),
  required_certifications: z.array(z.string()).default([]),
  region: z.string().optional(),
  address: z.string().optional(),
  is_urgent: z.boolean().default(false),
  latitude: z.number().nullable().optional(),
  longitude: z.number().nullable().optional(),
  payment_method: z.string().optional(),
  terms_agreed: z.boolean().optional(),
  // Handoff note (필수 — 신뢰 기반 매칭)
  handoff_class_topic: z.string().min(1, '수업 주제를 입력해주세요'),
  handoff_class_sequence_info: z.string().min(1, '수업 진도/내용을 입력해주세요'),
  handoff_atmosphere_preference: z.string().min(1, '수업 분위기를 선택해주세요'),
  handoff_member_notes: z.string().min(1, '회원 주의사항을 입력해주세요'),
  handoff_equipment_notes: z.string().min(1, '기구 세팅을 입력해주세요'),
});

export type JobPostFormData = z.infer<typeof jobPostSchema>;

// ---------------------------------------------------------------------------
// Reviews
// ---------------------------------------------------------------------------

export const reviewSchema = z.object({
  rating: z.number().min(1, '별점을 선택해주세요').max(5),
  comment: z.string().optional(),
});

export type ReviewFormData = z.infer<typeof reviewSchema>;

// ---------------------------------------------------------------------------
// Offers
// ---------------------------------------------------------------------------

export const offerSchema = z.object({
  proposed_rate: z
    .number()
    .min(10000, '시급은 10,000원 이상이어야 합니다'),
  message: z.string().optional(),
});

export type OfferFormData = z.infer<typeof offerSchema>;

// ---------------------------------------------------------------------------
// Verification
// ---------------------------------------------------------------------------

export const phoneVerificationSchema = z.object({
  phone: z
    .string()
    .min(10, '올바른 전화번호를 입력해주세요')
    .max(20),
});

export type PhoneVerificationFormData = z.infer<
  typeof phoneVerificationSchema
>;

export const otpVerificationSchema = z.object({
  otp: z.string().length(6, '인증번호 6자리를 입력해주세요'),
});

export type OtpVerificationFormData = z.infer<
  typeof otpVerificationSchema
>;

export const businessVerificationSchema = z.object({
  business_number: z
    .string()
    .length(10, '사업자등록번호 10자리를 입력해주세요'),
});

export type BusinessVerificationFormData = z.infer<
  typeof businessVerificationSchema
>;

// ---------------------------------------------------------------------------
// Contracts
// ---------------------------------------------------------------------------

export const contractCancelSchema = z.object({
  reason: z.string().min(1, '취소 사유를 입력해주세요'),
});

export type ContractCancelFormData = z.infer<typeof contractCancelSchema>;

// ---------------------------------------------------------------------------
// Handoff Notes
// ---------------------------------------------------------------------------

export const handoffNoteSchema = z.object({
  class_topic: z.string().max(200).optional(),
  class_sequence_info: z.string().optional(),
  atmosphere_preference: z.string().max(50).optional(),
  additional_notes: z.string().optional(),
  member_notes: z.string().optional(),
  equipment_notes: z.string().optional(),
});

export type HandoffNoteFormData = z.infer<typeof handoffNoteSchema>;
