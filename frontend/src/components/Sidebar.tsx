'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  FileClock,
  FilePlus2,
  LayoutDashboard,
  LogOut,
  PanelsTopLeft,
  Settings2,
  UserRound,
} from 'lucide-react';
import { useAuth } from '@/shared/auth/AuthContext';

const primaryItems = [
  { href: '/dashboard', label: 'لوحة التحكم', icon: LayoutDashboard },
  { href: '/services', label: 'الخدمات', icon: PanelsTopLeft },
  { href: '/reports/new', label: 'إنشاء تقرير', icon: FilePlus2 },
  { href: '/reports', label: 'سجل التقارير', icon: FileClock },
  { href: '/profile', label: 'الملف الشخصي', icon: UserRound },
];

function isActive(pathname: string, href: string) {
  if (href === '/dashboard') return pathname === href;
  if (href === '/reports') return pathname === href || (pathname.startsWith('/reports/') && pathname !== '/reports/new');
  if (href === '/reports/new') return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function Sidebar({ onNavigate }: { onNavigate: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading, logout } = useAuth();

  async function handleLogout() {
    await logout();
    router.replace('/login');
    router.refresh();
  }

  return (
    <aside className="app-sidebar" aria-label="القائمة الرئيسية">
      <Link className="sidebar-brand" href="/dashboard" onClick={onNavigate}>
        <img src="/header-logo-ar.png" alt="وزارة الإعلام" />
        <span>بوابة الخدمات الرقمية</span>
      </Link>

      <nav className="sidebar-nav">
        <span className="sidebar-section-label">مساحة العمل</span>
        {primaryItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={isActive(pathname, item.href) ? 'active' : ''}
              onClick={onNavigate}
            >
              <Icon size={19} strokeWidth={1.8} aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}

        {user?.is_staff && (
          <>
            <span className="sidebar-section-label admin-label">الإدارة</span>
            <Link
              href="/report-types"
              className={isActive(pathname, '/report-types') ? 'active' : ''}
              onClick={onNavigate}
            >
              <Settings2 size={19} strokeWidth={1.8} aria-hidden="true" />
              <span>إدارة القوالب</span>
            </Link>
          </>
        )}
      </nav>

      <div className="sidebar-footer">
        <Link href="/profile" className="sidebar-user" onClick={onNavigate}>
          <span className="user-avatar">{user?.username?.slice(0, 1).toUpperCase() || 'م'}</span>
          <span>
            <strong>{loading ? 'جارٍ التحميل...' : user?.username || 'المستخدم'}</strong>
            <small>{user?.is_staff ? 'مدير النظام' : 'مستخدم'}</small>
          </span>
        </Link>
        <button type="button" className="sidebar-logout" onClick={handleLogout}>
          <LogOut size={18} strokeWidth={1.8} aria-hidden="true" />
          <span>تسجيل الخروج</span>
        </button>
      </div>
    </aside>
  );
}
