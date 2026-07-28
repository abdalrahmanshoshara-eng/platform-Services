'use client';

import { Menu } from 'lucide-react';
import { usePathname } from 'next/navigation';

const pageTitles: Record<string, string> = {
  '/dashboard': 'لوحة التحكم',
  '/services': 'الخدمات',
  '/reports': 'سجل التقارير',
  '/reports/new': 'إنشاء تقرير',
  '/report-types': 'إدارة القوالب',
  '/profile': 'الملف الشخصي',
  '/tools/excel-contacts': 'تهيئة جهات الاتصال',
};

function titleFor(pathname: string) {
  if (pageTitles[pathname]) return pageTitles[pathname];
  if (pathname.startsWith('/reports/')) return 'تفاصيل التقرير';
  return 'بوابة الخدمات الرقمية';
}

export default function TopBar({ onMenuToggle }: { onMenuToggle: () => void }) {
  const pathname = usePathname();
  const today = new Intl.DateTimeFormat('ar-SY', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(new Date());

  return (
    <header className="app-topbar">
      <div className="topbar-page">
        <button type="button" className="sidebar-toggle" onClick={onMenuToggle} aria-label="فتح القائمة">
          <Menu size={22} aria-hidden="true" />
        </button>
        <div>
          <span>بوابة الخدمات الرقمية</span>
          <h1>{titleFor(pathname)}</h1>
        </div>
      </div>
      <time>{today}</time>
    </header>
  );
}
