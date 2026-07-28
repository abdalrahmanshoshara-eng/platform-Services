'use client';

import Link from 'next/link';
import {
  ArrowLeft,
  CheckCircle2,
  CircleAlert,
  FileClock,
  FilePlus2,
  Files,
  PanelsTopLeft,
} from 'lucide-react';
import { useEffect, useMemo, useState, type CSSProperties } from 'react';
import StatusBadge from '@/components/StatusBadge';
import { abortRequest, apiFetch, isAbortError } from '@/shared/api/client';
import type { DashboardStats, PlatformService } from '@/shared/api/types';
import { useAuth } from '@/shared/auth/AuthContext';
import { useRequireAuth } from '@/shared/auth/useRequireAuth';

export default function DashboardPage() {
  const ready = useRequireAuth();
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [services, setServices] = useState<PlatformService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!ready) return;
    const controller = new AbortController();
    Promise.all([
      apiFetch<DashboardStats>('/dashboard/stats/', { signal: controller.signal }),
      apiFetch<PlatformService[]>('/services/', { signal: controller.signal }),
    ])
      .then(([dashboard, catalog]) => {
        if (controller.signal.aborted) return;
        setStats(dashboard);
        setServices(catalog);
      })
      .catch((err) => {
        if (!isAbortError(err, controller.signal)) {
          setError(err instanceof Error ? err.message : 'تعذر تحميل لوحة التحكم.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => abortRequest(controller);
  }, [ready]);

  const completionRate = useMemo(() => {
    if (!stats?.total_reports) return 0;
    return Math.round((stats.completed_reports / stats.total_reports) * 100);
  }, [stats]);

  if (!ready) return <div className="page-loading">جارٍ تجهيز لوحة التحكم...</div>;

  return (
    <main className="dashboard-shell">
      <section className="dashboard-welcome">
        <div>
          <span className="dashboard-eyebrow">{user?.is_staff ? 'لوحة الإدارة' : 'مساحة العمل'}</span>
          <h2>مرحباً، {user?.username}</h2>
          <p>ملخص مباشر للخدمات والتقارير والعمليات التي تحتاج انتباهك.</p>
        </div>
        <Link className="dashboard-primary-action" href="/reports/new">
          <FilePlus2 size={18} aria-hidden="true" />
          إنشاء تقرير
        </Link>
      </section>

      {error && <div className="alert danger">{error}</div>}

      <section className="dashboard-metrics" aria-label="المؤشرات الرئيسية">
        <article>
          <span className="metric-icon green"><Files size={21} /></span>
          <div><span>إجمالي التقارير</span><strong>{loading ? '—' : stats?.total_reports ?? 0}</strong></div>
          <small>جميع التقارير المسجلة</small>
        </article>
        <article>
          <span className="metric-icon teal"><FileClock size={21} /></span>
          <div><span>تقارير اليوم</span><strong>{loading ? '—' : stats?.today_reports ?? 0}</strong></div>
          <small>النشاط خلال اليوم</small>
        </article>
        <article>
          <span className="metric-icon gold"><CheckCircle2 size={21} /></span>
          <div><span>تقارير مكتملة</span><strong>{loading ? '—' : stats?.completed_reports ?? 0}</strong></div>
          <small>{completionRate}% نسبة الإنجاز</small>
        </article>
        <article>
          <span className="metric-icon red"><CircleAlert size={21} /></span>
          <div><span>تحتاج مراجعة</span><strong>{loading ? '—' : stats?.failed_reports ?? 0}</strong></div>
          <small>عمليات لم تكتمل</small>
        </article>
      </section>

      <section className="dashboard-layout">
        <div className="dashboard-panel reports-panel">
          <div className="panel-heading">
            <div>
              <h3>آخر التقارير</h3>
              <p>أحدث العمليات المسجلة في النظام</p>
            </div>
            <Link href="/reports">عرض السجل <ArrowLeft size={15} /></Link>
          </div>
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>التقرير</th>
                  <th>النوع</th>
                  <th>الحالة</th>
                  <th>التاريخ</th>
                </tr>
              </thead>
              <tbody>
                {stats?.latest_reports?.length ? stats.latest_reports.map((report) => (
                  <tr key={report.id}>
                    <td><Link href={`/reports/${report.id}`}>{report.title}</Link></td>
                    <td>{report.report_type.name}</td>
                    <td><StatusBadge status={report.status} /></td>
                    <td>{new Date(report.created_at).toLocaleDateString('ar-SY')}</td>
                  </tr>
                )) : (
                  <tr><td colSpan={4} className="dashboard-empty">لا توجد تقارير بعد.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <aside className="dashboard-side-stack">
          <section className="dashboard-panel progress-panel">
            <div className="panel-heading">
              <div><h3>مؤشر الإنجاز</h3><p>نسبة التقارير المكتملة</p></div>
            </div>
            <div className="progress-summary">
              <div className="progress-ring" style={{ '--progress': `${completionRate * 3.6}deg` } as CSSProperties}>
                <span>{completionRate}%</span>
              </div>
              <div className="progress-legend">
                <span><i className="completed" /> مكتملة <strong>{stats?.completed_reports ?? 0}</strong></span>
                <span><i className="failed" /> لم تكتمل <strong>{stats?.failed_reports ?? 0}</strong></span>
              </div>
            </div>
          </section>

          <section className="dashboard-panel quick-panel">
            <div className="panel-heading">
              <div><h3>وصول سريع</h3><p>أكثر المسارات استخداماً</p></div>
            </div>
            <div className="dashboard-quick-links">
              <Link href="/services"><PanelsTopLeft size={18} /><span>الخدمات</span><small>{services.filter((item) => item.is_available).length} متاحة</small></Link>
              <Link href="/reports"><FileClock size={18} /><span>سجل التقارير</span><small>{stats?.total_reports ?? 0} تقرير</small></Link>
              {user?.is_staff && <Link href="/report-types"><Files size={18} /><span>إدارة القوالب</span><small>{stats?.report_types ?? 0} قالب</small></Link>}
            </div>
          </section>
        </aside>
      </section>
    </main>
  );
}
