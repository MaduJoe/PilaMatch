import { describe, it, expect } from 'vitest';
import {
  loginSchema,
  signupSchema,
  reviewSchema,
  offerSchema,
  contractCancelSchema,
} from '@/lib/validators';

describe('Zod Validators', () => {
  describe('loginSchema', () => {
    it('accepts valid login', () => {
      const result = loginSchema.safeParse({
        email: 'user@test.com',
        password: 'pass',
      });
      expect(result.success).toBe(true);
    });

    it('rejects invalid email', () => {
      const result = loginSchema.safeParse({
        email: 'not-email',
        password: 'pass',
      });
      expect(result.success).toBe(false);
    });

    it('rejects empty password', () => {
      const result = loginSchema.safeParse({
        email: 'user@test.com',
        password: '',
      });
      expect(result.success).toBe(false);
    });
  });

  describe('signupSchema', () => {
    const validInstructor = {
      email: 'test@test.com',
      password: '12345678',
      role: 'instructor' as const,
      display_name: 'John',
      terms_agreed: true as const,
      privacy_agreed: true as const,
    };

    const validStudio = {
      email: 'studio@test.com',
      password: '12345678',
      role: 'studio' as const,
      business_name: 'My Studio',
      terms_agreed: true as const,
      privacy_agreed: true as const,
    };

    it('accepts valid instructor signup', () => {
      expect(signupSchema.safeParse(validInstructor).success).toBe(true);
    });

    it('accepts valid studio signup', () => {
      expect(signupSchema.safeParse(validStudio).success).toBe(true);
    });

    it('rejects short password', () => {
      const result = signupSchema.safeParse({
        ...validInstructor,
        password: '1234567',
      });
      expect(result.success).toBe(false);
    });

    it('rejects instructor without display_name', () => {
      const result = signupSchema.safeParse({
        ...validInstructor,
        display_name: '',
      });
      expect(result.success).toBe(false);
    });

    it('rejects studio without business_name', () => {
      const result = signupSchema.safeParse({
        ...validStudio,
        business_name: '',
      });
      expect(result.success).toBe(false);
    });

    it('rejects without terms_agreed', () => {
      const result = signupSchema.safeParse({
        ...validInstructor,
        terms_agreed: false,
      });
      expect(result.success).toBe(false);
    });

    it('rejects without privacy_agreed', () => {
      const result = signupSchema.safeParse({
        ...validInstructor,
        privacy_agreed: false,
      });
      expect(result.success).toBe(false);
    });
  });

  describe('reviewSchema', () => {
    it('accepts valid review', () => {
      const result = reviewSchema.safeParse({ rating: 5, comment: 'Great!' });
      expect(result.success).toBe(true);
    });

    it('rejects rating below 1', () => {
      const result = reviewSchema.safeParse({ rating: 0 });
      expect(result.success).toBe(false);
    });

    it('rejects rating above 5', () => {
      const result = reviewSchema.safeParse({ rating: 6 });
      expect(result.success).toBe(false);
    });
  });

  describe('offerSchema', () => {
    it('accepts valid offer', () => {
      const result = offerSchema.safeParse({ proposed_rate: 50000 });
      expect(result.success).toBe(true);
    });

    it('rejects rate below minimum', () => {
      const result = offerSchema.safeParse({ proposed_rate: 5000 });
      expect(result.success).toBe(false);
    });
  });

  describe('contractCancelSchema', () => {
    it('accepts with reason', () => {
      const result = contractCancelSchema.safeParse({ reason: 'schedule conflict' });
      expect(result.success).toBe(true);
    });

    it('rejects empty reason', () => {
      const result = contractCancelSchema.safeParse({ reason: '' });
      expect(result.success).toBe(false);
    });
  });
});
