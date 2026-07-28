'use client';

import { Database, LockKeyhole, ServerCog } from 'lucide-react';
import ReportTemplatesManager from '@/components/admin/ReportTemplatesManager';
import { AdminHeader, StatusBadge } from '@/components/admin/AdminUI';

export default function AdminSettingsPage() {
  return (
    <main className="admin-content">
      <AdminHeader title="إعدادات المنصة" description="إدارة المكونات التشغيلية وقوالب التقارير من واجهة واحدة." />
      <section className="admin-settings-grid">
        <article><Database size={21} /><div><strong>PostgreSQL</strong><small>قاعدة البيانات الأساسية للمنصة</small></div><StatusBadge active label="متصل" /></article>
        <article><ServerCog size={21} /><div><strong>Celery + Redis</strong><small>معالجة الوظائف الخلفية</small></div><StatusBadge active label="مفعّل" /></article>
        <article><LockKeyhole size={21} /><div><strong>HttpOnly JWT</strong><small>جلسات محمية وسياسة إدارة مركزية</small></div><StatusBadge active label="مفعّل" /></article>
      </section>
      <ReportTemplatesManager />
    </main>
  );
}
