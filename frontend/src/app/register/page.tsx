'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      await apiFetch(API_ENDPOINTS.auth.register, {
        method: 'POST',
        body: { username, email, password },
      });
      window.location.assign('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'تعذر إنشاء الحساب.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container narrow-container">
      <section className="hero login-hero">
        <div className="hero-accent-line" />
        <div className="header-overlay" aria-hidden="true" />
        <h1>إنشاء حساب</h1>
        <p>أنشئ حساباً للوصول إلى الخدمات المتاحة ضمن البوابة.</p>
      </section>
      <form className="card auth-card" onSubmit={submit}>
        <h2>بيانات الحساب</h2>
        {error && <div className="alert danger">{error}</div>}
        <label>
          اسم المستخدم
          <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
        </label>
        <label>
          البريد الإلكتروني
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required />
        </label>
        <label>
          كلمة المرور
          <input type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" required />
        </label>
        <button className="gold" type="submit" disabled={loading}>{loading ? 'جارٍ إنشاء الحساب...' : 'إنشاء الحساب'}</button>
        <p className="auth-switch">لديك حساب بالفعل؟ <Link href="/login">تسجيل الدخول</Link></p>
      </form>
    </main>
  );
}
