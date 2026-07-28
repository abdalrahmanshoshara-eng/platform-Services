'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useLogin } from '@/features/auth/useLogin';
import { useAuth } from '@/shared/auth/AuthContext';

export default function LoginPage() {
  const router = useRouter();
  const { login, loading, error } = useLogin();
  const { user, loading: authLoading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    if (!authLoading && user) router.replace(user.is_staff || user.is_superuser ? '/admin' : '/dashboard');
  }, [authLoading, user, router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const loggedInUser = await login(username, password);
    if (loggedInUser) {
      router.replace(loggedInUser.is_staff || loggedInUser.is_superuser ? '/admin' : '/dashboard');
      router.refresh();
    }
  }

  if (authLoading || user) return <main className="auth-loading">جارٍ فتح لوحة التحكم...</main>;

  return (
    <main className="container narrow-container">
      <section className="hero login-hero">
        <div className="hero-accent-line" />
        <div className="header-overlay" aria-hidden="true"></div>
        <h1>تسجيل الدخول</h1>
        <p>ادخل بيانات حسابك للوصول إلى بوابة الخدمات الرقمية.</p>
      </section>

      <form className="card auth-card" onSubmit={handleSubmit}>
        <h2>بيانات الدخول</h2>
        {error && <div className="alert danger">{error}</div>}
        <label>
          اسم المستخدم أو البريد الإلكتروني
          <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
        </label>
        <label>
          كلمة المرور
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
        </label>
        <button className="gold" type="submit" disabled={loading}>{loading ? 'جارٍ الدخول...' : 'تسجيل الدخول'}</button>
        <p className="auth-switch">ليس لديك حساب؟ <Link href="/register">إنشاء حساب جديد</Link></p>
      </form>
    </main>
  );
}
