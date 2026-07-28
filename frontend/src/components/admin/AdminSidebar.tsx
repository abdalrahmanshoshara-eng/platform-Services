'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Activity,
  BarChart3,
  Boxes,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Settings,
  ShieldCheck,
  Users,
} from 'lucide-react';
import { useAuth } from '@/shared/auth/AuthContext';

const sections = [
  {
    label: 'نظرة عامة',
    items: [{ href: '/admin', label: 'لوحة الإدارة', icon: LayoutDashboard }],
  },
  {
    label: 'إدارة المنصة',
    items: [
      { href: '/admin/users', label: 'المستخدمون', icon: Users },
      { href: '/admin/services', label: 'الخدمات', icon: Boxes },
    ],
  },
  {
    label: 'التشغيل والرقابة',
    items: [
      { href: '/admin/jobs', label: 'الوظائف', icon: ListChecks },
      { href: '/admin/analytics', label: 'التحليلات', icon: BarChart3 },
      { href: '/admin/audit-logs', label: 'سجل التدقيق', icon: ShieldCheck },
      { href: '/admin/settings', label: 'الإعدادات', icon: Settings },
    ],
  },
];

function isActive(pathname: string, href: string) {
  return href === '/admin' ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);
}

export default function AdminSidebar({ onNavigate }: { onNavigate: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  async function handleLogout() {
    await logout();
    router.replace('/login');
    router.refresh();
  }

  return (
    <aside className="admin-sidebar" aria-label="قائمة الإدارة">
      <Link className="admin-brand" href="/admin" onClick={onNavigate}>
        <img src="/header-logo-ar.png" alt="وزارة الإعلام" />
        <span><ShieldCheck size={15} /> مركز التحكم الإداري</span>
      </Link>
      <nav className="admin-nav">
        {sections.map((section) => (
          <div className="admin-nav-section" key={section.label}>
            <span>{section.label}</span>
            {section.items.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  href={item.href}
                  key={item.href}
                  className={isActive(pathname, item.href) ? 'active' : ''}
                  onClick={onNavigate}
                >
                  <Icon size={18} strokeWidth={1.8} />
                  {item.label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
      <div className="admin-sidebar-footer">
        <div className="admin-account">
          <span>{user?.username?.slice(0, 1).toUpperCase()}</span>
          <div><strong>{user?.username}</strong><small>مدير النظام</small></div>
        </div>
        <button type="button" onClick={handleLogout}>
          <LogOut size={18} />
          تسجيل الخروج
        </button>
      </div>
    </aside>
  );
}
