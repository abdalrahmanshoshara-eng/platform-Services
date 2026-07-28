'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useAuth } from './AuthContext';

/** Redirect to /login when there is no authenticated user. */
export function useRequireAuth(): boolean {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && !user) router.replace('/login');
  }, [loading, user, router]);

  return !loading && !!user;
}
