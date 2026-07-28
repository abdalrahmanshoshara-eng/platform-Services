'use client';

import { Activity, Menu } from 'lucide-react';
import { usePathname } from 'next/navigation';

const titles: Record<string, string> = {
  '/admin': 'لوحة الإدارة',
  '/admin/users': 'إدارة المستخدمين',
  '/admin/services': 'إدارة الخدمات',
  '/admin/jobs': 'مراقبة الوظائف',
  '/admin/analytics': 'التحليلات',
  '/admin/audit-logs': 'سجل التدقيق',
  '/admin/settings': 'إعدادات المنصة',
};

export default function AdminTopBar({ onMenuToggle }: { onMenuToggle: () => void }) {
  const pathname = usePathname();
  let title = titles[pathname];
  if (!title && pathname.startsWith('/admin/users/')) title = 'تفاصيل المستخدم';
  if (!title && pathname.startsWith('/admin/services/')) title = 'تفاصيل الخدمة';

  return (
    <header className="admin-topbar">
      <button type="button" className="admin-menu-button" onClick={onMenuToggle} aria-label="فتح القائمة">
        <Menu size={21} />
      </button>
      <h1>{title || 'مركز التحكم الإداري'}</h1>
      <span className="admin-environment"><Activity size={14} /> النظام متصل</span>
    </header>
  );
}
