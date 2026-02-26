import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { signupSchema } from '@/lib/validators';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/signup',
}));

describe('Signup Terms Agreement', () => {
  describe('signupSchema validation', () => {
    it('rejects when terms_agreed is false', () => {
      const result = signupSchema.safeParse({
        email: 'test@test.com',
        password: '12345678',
        role: 'instructor',
        display_name: 'Test',
        terms_agreed: false,
        privacy_agreed: true,
      });
      expect(result.success).toBe(false);
    });

    it('rejects when privacy_agreed is false', () => {
      const result = signupSchema.safeParse({
        email: 'test@test.com',
        password: '12345678',
        role: 'instructor',
        display_name: 'Test',
        terms_agreed: true,
        privacy_agreed: false,
      });
      expect(result.success).toBe(false);
    });

    it('accepts when both are true', () => {
      const result = signupSchema.safeParse({
        email: 'test@test.com',
        password: '12345678',
        role: 'instructor',
        display_name: 'Test',
        terms_agreed: true,
        privacy_agreed: true,
      });
      expect(result.success).toBe(true);
    });

    it('rejects when terms fields are missing', () => {
      const result = signupSchema.safeParse({
        email: 'test@test.com',
        password: '12345678',
        role: 'instructor',
        display_name: 'Test',
      });
      expect(result.success).toBe(false);
    });
  });
});
