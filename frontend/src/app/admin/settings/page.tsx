'use client';

import { useEffect, useState } from 'react';
import { Database, LockKeyhole, ServerCog } from 'lucide-react';
import ReportTemplatesManager from '@/components/admin/ReportTemplatesManager';
import { AdminHeader, StatusBadge } from '@/components/admin/AdminUI';
import { API_URL } from '@/shared/api/client';

type DbStatus = 'checking' | 'ok' | 'error';

export default function AdminSettingsPage() {
  const [db, setDb] = useState<DbStatus>('checking');

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const healthUrl = `${API_URL.replace(/\/api\/?$/, '')}/health/ready`;
    fetch(healthUrl, { signal: controller.signal })
      .then((res) => res.json())
      .then((data: { checks?: { database?: string } }) => {
        if (active) setDb(data?.checks?.database === 'ok' ? 'ok' : 'error');
      })
      .catch(() => {
        if (active) setDb('error');
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, []);

  const dbLabel = db === 'checking' ? 'جارٍ الفحص…' : db === 'ok' ? 'متصل' : 'غير متصل';

  return (
    <main className="admin-content">
      <AdminHeader title="إعدادات المنصة" description="إدارة المكونات التشغيلية وقوالب التقارير من واجهة واحدة." />
      <section className="admin-settings-grid">
        <article>
          <Database size={21} />
          <div><strong>PostgreSQL</strong><small>قاعدة البيانات الأساسية للمنصة (فحص حيّ)</small></div>
          <StatusBadge active={db === 'ok'} label={dbLabel} />
        </article>
        <article>
          <ServerCog size={21} />
          <div><strong>Celery + Redis</strong><small>معالجة الوظائف الخلفية</small></div>
          <StatusBadge active label="مُهيّأ" />
        </article>
        <article>
          <LockKeyhole size={21} />
          <div><strong>HttpOnly JWT</strong><small>جلسات محمية وسياسة إدارة مركزية</small></div>
          <StatusBadge active label="مُفعّل" />
        </article>
      </section>
      <ReportTemplatesManager />
    </main>
  );
}
