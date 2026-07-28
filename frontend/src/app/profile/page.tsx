'use client';

import { BadgeCheck, Mail, ShieldCheck, UserRound } from 'lucide-react';
import { useAuth } from '@/shared/auth/AuthContext';
import { useRequireAuth } from '@/shared/auth/useRequireAuth';

export default function ProfilePage() {
  const ready = useRequireAuth();
  const { user } = useAuth();

  if (!ready) return <div className="page-loading">جارٍ تحميل الملف الشخصي...</div>;

  return (
    <main className="profile-page">
      <section className="profile-header">
        <span className="profile-avatar">{user?.username?.slice(0, 1).toUpperCase()}</span>
        <div>
          <span className="dashboard-eyebrow">بيانات الحساب</span>
          <h2>{user?.username}</h2>
          <p>{user?.is_staff ? 'حساب إداري بصلاحيات إدارة المنصة.' : 'حساب مستخدم للوصول إلى الخدمات المتاحة.'}</p>
        </div>
      </section>

      <section className="profile-details">
        <article>
          <span><UserRound size={20} /></span>
          <div><small>اسم المستخدم</small><strong>{user?.username}</strong></div>
        </article>
        <article>
          <span><Mail size={20} /></span>
          <div><small>البريد الإلكتروني</small><strong>{user?.email || 'غير مضاف'}</strong></div>
        </article>
        <article>
          <span><ShieldCheck size={20} /></span>
          <div><small>نوع الحساب</small><strong>{user?.is_staff ? 'مدير النظام' : 'مستخدم'}</strong></div>
        </article>
        <article>
          <span><BadgeCheck size={20} /></span>
          <div><small>حالة الحساب</small><strong>نشط</strong></div>
        </article>
      </section>
    </main>
  );
}
