'use client';

import { useEffect, useState, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/shared/auth/AuthContext';
import { adminGate } from '@/shared/auth/adminGate';
import AdminSidebar from './AdminSidebar';
import AdminTopBar from './AdminTopBar';

export default function AdminChrome({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const gate = adminGate(user, loading);

  useEffect(() => {
    if (gate === 'redirect-login') router.replace('/login');
    else if (gate === 'redirect-dashboard') router.replace('/dashboard');
  }, [gate, router]);

  if (gate !== 'allowed') {
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
