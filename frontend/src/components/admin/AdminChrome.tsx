'use client';

import { useEffect, useState, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/shared/auth/AuthContext';
import AdminSidebar from './AdminSidebar';
import AdminTopBar from './AdminTopBar';

export default function AdminChrome({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!user) router.replace('/login');
    else if (!user.is_staff && !user.is_superuser) router.replace('/dashboard');
  }, [loading, user, router]);

  if (loading || !user || (!user.is_staff && !user.is_superuser)) {
    return <main className="page-loading">جارٍ التحقق من صلاحيات الإدارة...</main>;
  }

  return (
    <div className={`admin-frame ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <AdminSidebar onNavigate={() => setSidebarOpen(false)} />
      <button
        className="sidebar-backdrop"
        type="button"
        aria-label="إغلاق القائمة"
        onClick={() => setSidebarOpen(false)}
      />
      <div className="admin-workspace">
        <AdminTopBar onMenuToggle={() => setSidebarOpen((open) => !open)} />
        <div className="admin-page">{children}</div>
      </div>
    </div>
  );
}
