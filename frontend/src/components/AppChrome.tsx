'use client';

import { usePathname } from 'next/navigation';
import { useState, type ReactNode } from 'react';
import Sidebar from '@/components/Sidebar';
import TopBar from '@/components/TopBar';
import AdminChrome from '@/components/admin/AdminChrome';

const PUBLIC_PATHS = ['/login', '/register'];

export default function AppChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isPublicPage = PUBLIC_PATHS.some((path) => pathname.startsWith(path));

  if (isPublicPage) return children;
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
