'use client';

import { BarChart3, FileCheck2, ShieldBan } from 'lucide-react';
import { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminUI';
import { apiFetch } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';

type Analytics = {
  period_days: number;
  daily_reports: { day: string; total: number; completed: number; failed: number }[];
  services: { id: number; name: string; category: string; launches: number; denied: number; restricted_users: number }[];
  top_report_types: { id: number; name: string; count: number }[];
};

export default function AdminAnalyticsPage() {
  const [days, setDays] = useState(30);
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    setData(null);
    apiFetch<Analytics>(API_ENDPOINTS.admin.analytics(days)).then(setData).catch((err) => setError(err instanceof Error ? err.message : 'تعذر تحميل التحليلات.'));
  }, [days]);

  const maximum = Math.max(1, ...(data?.daily_reports.map((item) => item.total) || [1]));
  return (
    <main className="admin-content">
      <AdminHeader title="التحليلات" description="قياس استخدام الخدمات وإنتاج التقارير من أحداث الخادم الفعلية." action={<select value={days} onChange={(event) => setDays(Number(event.target.value))}><option value={7}>آخر 7 أيام</option><option value={30}>آخر 30 يوماً</option><option value={90}>آخر 90 يوماً</option></select>} />
      {error && <div className="admin-alert">{error}</div>}
      {!data && !error && <div className="admin-loading">جارٍ تحليل البيانات...</div>}
      {data && <>
        <section className="admin-panel admin-chart-panel">
          <div className="admin-panel-heading"><div><h3>نشاط التقارير اليومي</h3><p>إجمالي الطلبات المكتملة والفاشلة.</p></div><BarChart3 size={20} /></div>
          <div className="admin-bar-chart">{data.daily_reports.map((item) => <div className="admin-bar-column" key={item.day} title={`${item.total} تقرير`}><div className="admin-bar" style={{ height: `${Math.max(5, (item.total / maximum) * 100)}%` }}><span>{item.total}</span></div><small>{new Date(item.day).toLocaleDateString('ar-SY', { day: 'numeric', month: 'short' })}</small></div>)}{!data.daily_reports.length && <p className="admin-muted">لا توجد تقارير في هذه الفترة.</p>}</div>
        </section>
        <section className="admin-two-column">
          <div className="admin-panel"><div className="admin-panel-heading"><div><h3>استخدام الخدمات</h3><p>التشغيل الناجح والمحاولات المرفوضة.</p></div></div>
            <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>الخدمة</th><th>التشغيل</th><th>المرفوض</th><th>المقيدون</th></tr></thead><tbody>{data.services.map((service) => <tr key={service.id}><td><strong>{service.name}</strong><small>{service.category}</small></td><td><FileCheck2 size={15} /> {service.launches}</td><td><ShieldBan size={15} /> {service.denied}</td><td>{service.restricted_users}</td></tr>)}</tbody></table></div>
          </div>
          <div className="admin-panel"><div className="admin-panel-heading"><div><h3>أنواع التقارير الأكثر استخداماً</h3><p>مرتبة حسب عدد التقارير.</p></div></div><div className="admin-ranking">{data.top_report_types.map((item, index) => <div key={item.id}><span>{index + 1}</span><strong>{item.name}</strong><b>{item.count}</b></div>)}{!data.top_report_types.length && <p className="admin-muted">لا تتوفر بيانات لهذه الفترة.</p>}</div></div>
        </section>
      </>}
    </main>
  );
}
