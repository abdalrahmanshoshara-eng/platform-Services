'use client';

import { usePathname } from 'next/navigation';
import { useState, type ReactNode } from 'react';
import Sidebar from '@/components/Sidebar';
import TopBar from '@/components/TopBar';
import AdminChrome from '@/components/admin/AdminChrome';
import PublicChrome from '@/components/public/PublicChrome';

const AUTH_PATHS = ['/login', '/register'];
const MARKETING_PATHS = ['/', '/services'];

export default function AppChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isAuthPage = AUTH_PATHS.some((path) => pathname.startsWith(path));
  const isMarketingPage = MARKETING_PATHS.includes(pathname);

  if (isAuthPage) return children;
  if (isMarketingPage) return <PublicChrome>{children}</PublicChrome>;
  if (pathname.startsWith('/admin')) return <AdminChrome>{children}</AdminChrome>;

  return (
    <div className={`app-frame ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <Sidebar onNavigate={() => setSidebarOpen(false)} />
      <button
        className="sidebar-backdrop"
        type="button"
        aria-label="إغلاق القائمة"
        onClick={() => setSidebarOpen(false)}
      />
      <div className="app-workspace">
        <TopBar onMenuToggle={() => setSidebarOpen((open) => !open)} />
        <div className="app-page">{children}</div>
      </div>
    </div>
  );
}
