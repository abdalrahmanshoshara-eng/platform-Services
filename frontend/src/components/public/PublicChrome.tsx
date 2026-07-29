'use client';

import { ArrowLeft, LogOut, UserRound } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { ReactNode } from 'react';
import { useAuth } from '@/shared/auth/AuthContext';

export default function PublicChrome({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { user, loading, logout } = useAuth();

  async function handleLogout() {
    await logout();
    router.refresh();
  }

  return (
    <div className="public-site">
      <header className="public-header">
        <div className="public-header-inner">
          <Link className="public-brand" href="/" aria-label="الرئيسية">
            <span className="public-brand-mark" aria-hidden="true">م</span>
            <span>
              <strong>منصّة الخدمات</strong>
              <small>مساحة واحدة لأعمالك الرقمية</small>
            </span>
          </Link>

          <nav className="public-nav" aria-label="التنقل الرئيسي">
            <Link href="/#about">عن المنصّة</Link>
            <Link href="/#services">الخدمات</Link>
            <Link href="/#how-it-works">كيف تعمل</Link>
          </nav>

          <div className="public-auth">
            {loading ? (
              <span className="public-auth-loading" aria-label="جارٍ التحقق من الجلسة" />
            ) : user ? (
              <>
                <Link
                  className="public-user-link"
                  href={user.is_staff || user.is_superuser ? '/admin' : '/dashboard'}
                >
                  <UserRound size={17} aria-hidden="true" />
                  <span>لوحة العمل</span>
                </Link>
                <button
                  type="button"
                  className="public-logout"
                  onClick={handleLogout}
                  aria-label="تسجيل الخروج"
                >
                  <LogOut size={17} aria-hidden="true" />
                </button>
              </>
            ) : (
              <>
                <Link className="public-login" href="/login">تسجيل الدخول</Link>
                <Link className="public-register" href="/register">
                  <span>إنشاء حساب</span>
                  <ArrowLeft size={16} aria-hidden="true" />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {children}

      <footer className="public-footer">
        <div>
          <Link className="public-brand public-footer-brand" href="/">
            <span className="public-brand-mark" aria-hidden="true">م</span>
            <span>
              <strong>منصّة الخدمات</strong>
              <small>أدوات واضحة. نتائج جاهزة.</small>
            </span>
          </Link>
          <p>منصّة موحّدة تساعدك على إنجاز التقارير ومعالجة ملفات العمل بأمان وكفاءة.</p>
        </div>
        <div className="public-footer-links">
          <Link href="/#services">استعراض الخدمات</Link>
          <Link href="/login">تسجيل الدخول</Link>
          <Link href="/register">إنشاء حساب</Link>
        </div>
        <small>© {new Date().getFullYear()} منصّة الخدمات الرقمية</small>
      </footer>
    </div>
  );
}
