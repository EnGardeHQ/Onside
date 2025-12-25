/**
 * Register Page
 * User registration page with form validation
 */

import React, { useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { UserPlus, Mail, Lock, User } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { Button, Input, Card } from '../components/common';

const registerSchema = z
  .object({
    email: z.string().email('Invalid email address'),
    username: z
      .string()
      .min(3, 'Username must be at least 3 characters')
      .max(20, 'Username must be at most 20 characters')
      .regex(/^[a-zA-Z0-9_]+$/, 'Username can only contain letters, numbers, and underscores'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Password must contain at least one number'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register: registerUser, isAuthenticated, isLoading, error, clearError } = useAuthStore();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    return () => clearError();
  }, [clearError]);

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser(data.email, data.username, data.password);
      // Navigation handled by useEffect after auto-login
    } catch (err) {
      // Error handled by store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <div className="w-full max-w-md">
        <Card padding="lg">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-full mb-4">
              <UserPlus className="w-8 h-8 text-primary-600 dark:text-primary-400" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Create Account
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Get started with OnSide
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && (
              <div
                className="p-3 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-lg text-danger-700 dark:text-danger-400 text-sm"
                role="alert"
              >
                {error}
              </div>
            )}

            <Input
              label="Email"
              type="email"
              placeholder="your.email@example.com"
              leftIcon={<Mail size={18} />}
              error={errors.email?.message}
              autoComplete="email"
              {...register('email')}
            />

            <Input
              label="Username"
              type="text"
              placeholder="Choose a username"
              leftIcon={<User size={18} />}
              error={errors.username?.message}
              autoComplete="username"
              {...register('username')}
            />

            <Input
              label="Password"
              type="password"
              placeholder="Create a strong password"
              leftIcon={<Lock size={18} />}
              error={errors.password?.message}
              autoComplete="new-password"
              helperText="Must be at least 8 characters with uppercase, lowercase, and numbers"
              {...register('password')}
            />

            <Input
              label="Confirm Password"
              type="password"
              placeholder="Re-enter your password"
              leftIcon={<Lock size={18} />}
              error={errors.confirmPassword?.message}
              autoComplete="new-password"
              {...register('confirmPassword')}
            />

            <div className="text-xs text-gray-600 dark:text-gray-400">
              By creating an account, you agree to our{' '}
              <a href="#terms" className="text-primary-600 dark:text-primary-400 hover:underline">
                Terms of Service
              </a>{' '}
              and{' '}
              <a href="#privacy" className="text-primary-600 dark:text-primary-400 hover:underline">
                Privacy Policy
              </a>
              .
            </div>

            <Button type="submit" variant="primary" fullWidth isLoading={isLoading} size="lg">
              Create Account
            </Button>
          </form>

          <div className="mt-6 text-center text-sm">
            <span className="text-gray-600 dark:text-gray-400">Already have an account? </span>
            <Link
              to="/login"
              className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium"
            >
              Sign in
            </Link>
          </div>
        </Card>

        <div className="mt-8 text-center text-xs text-gray-500 dark:text-gray-500">
          <p>OnSide Competitive Intelligence Platform</p>
          <p className="mt-1">© 2025 OnSide. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
};
