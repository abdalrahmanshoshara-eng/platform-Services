'use client';

import Link from 'next/link';
import { Activity, Boxes, CircleAlert, FileStack, ListChecks, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { AdminHeader, StatusBadge } from '@/components/admin/AdminUI';
import { abortRequest, apiFetch, isAbortError } from '@/shared/api/client';
import type { AdminDashboard } from '@/shared/api/types';

export default function AdminDashboardPage() {
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    apiFetch<AdminDashboard>('/v1/admin/dashboard/', { signal: controller.signal })
      .then(setData)
      .catch((err) => {
        if (!isAbortError(err, controller.signal)) setError(err instanceof Error ? err.message : 'تعذر تحميل لوحة الإدارة.');
      });
    return () => abortRequest(controller);
  }, []);

  if (!data && !error) return <main className="admin-content"><div className="admin-loading">جارٍ تحميل مؤشرات المنصة...</div></main>;

  const metrics = data ? [
    { label: 'المستخدمون', value: data.summary.users, detail: `${data.summary.active_users} حساباً نشطاً`, icon: Users, tone: 'green' },
    { label: 'الخدمات', value: data.summary.services, detail: `${data.summary.active_services} خدمة متاحة`, icon: Boxes, tone: 'teal' },
    { label: 'التقارير', value: data.summary.reports, detail: `${data.summary.reports_last_24h} خلال آخر 24 ساعة`, icon: FileStack, tone: 'gold' },
    { label: 'قيد التنفيذ', value: data.summary.queued_jobs, detail: `${data.summary.failed_jobs} وظائف فاشلة`, icon: ListChecks, tone: data.summary.failed_jobs ? 'red' : 'green' },
  ] : [];

  return (
    <main className="admin-content">
      <AdminHeader title="نظرة عامة" description="الحالة التشغيلية الفعلية للمنصة من قاعدة البيانات." />
      {error && <div className="admin-alert">{error}</div>}
      <section className="admin-metrics">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <article key={metric.label}>
              <span className={`admin-metric-icon ${metric.tone}`}><Icon size={21} /></span>
              <div><small>{metric.label}</small><strong>{metric.value.toLocaleString('ar-SY')}</strong></div>
              <p>{metric.detail}</p>
            </article>
          );
        })}
      </section>
      <section className="admin-dashboard-grid">
        <div className="admin-panel">
          <div className="admin-panel-heading"><div><h3>النشاط الإداري الأخير</h3><p>آخر العمليات الأمنية والإدارية المسجلة.</p></div><Link href="/admin/audit-logs">عرض السجل</Link></div>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead><tr><th>العملية</th><th>المنفذ</th><th>النتيجة</th><th>الوقت</th></tr></thead>
              <tbody>
                {data?.recent_activity.map((event) => (
                  <tr key={event.id}>
                    <td><strong>{event.action}</strong><small>{event.target_type} {event.target_id}</small></td>
                    <td>{event.actor_name}</td>
                    <td><StatusBadge active={event.outcome === 'success'} label={event.outcome === 'success' ? 'نجحت' : 'مرفوضة'} /></td>
                    <td>{new Date(event.created_at).toLocaleString('ar-SY')}</td>
                  </tr>
                ))}
                {!data?.recent_activity.length && <tr><td colSpan={4} className="admin-table-empty">لا يوجد نشاط مسجل بعد.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
        <aside className="admin-side-panel">
          <div className="admin-panel-heading"><div><h3>حالة الوظائف</h3><p>توزيع عمليات توليد التقارير.</p></div><Activity size={19} /></div>
          <div className="admin-status-list">
            {data?.job_statuses.map((item) => <div key={item.status}><span>{item.status}</span><strong>{item.count}</strong></div>)}
            {!data?.job_statuses.length && <p className="admin-muted">لا توجد وظائف حتى الآن.</p>}
          </div>
          {!!data?.summary.failed_jobs && <Link className="admin-warning-link" href="/admin/jobs?status=failed"><CircleAlert size={17} /> مراجعة الوظائف الفاشلة</Link>}
        </aside>
      </section>
    </main>
  );
}
