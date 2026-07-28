'use client';

import { RefreshCw, Search, Square } from 'lucide-react';
import { useMemo, useState } from 'react';
import { AdminEmpty, AdminHeader, Pagination, StatusBadge } from '@/components/admin/AdminUI';
import { apiFetch } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';
import type { AdminJob } from '@/shared/api/types';
import { useAdminList } from '@/shared/admin/useAdminList';

const activeStatuses = new Set(['pending', 'queued', 'processing']);

export default function AdminJobsPage() {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [actionError, setActionError] = useState('');
  const query = useMemo(() => new URLSearchParams({ search, status, page: String(page) }).toString(), [search, status, page]);
  const { data, loading, error, reload } = useAdminList<AdminJob>(API_ENDPOINTS.admin.jobs, query);

  async function runAction(job: AdminJob, action: 'retry' | 'cancel') {
    setActionError('');
    try { await apiFetch(API_ENDPOINTS.admin.jobAction(job.id, action), { method: 'POST', body: {} }); reload(); }
    catch (err) { setActionError(err instanceof Error ? err.message : 'تعذر تنفيذ العملية.'); }
  }

  return (
    <main className="admin-content">
      <AdminHeader title="مراقبة الوظائف" description="تتبع عمليات توليد التقارير وإعادة تشغيل الفاشل وإلغاء العمليات المنتظرة." action={<button className="admin-secondary-button" type="button" onClick={reload}><RefreshCw size={16} /> تحديث</button>} />
      <div className="admin-filters">
        <label className="admin-search"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="بحث بالعنوان أو المستخدم" /></label>
        <select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">كل الحالات</option><option value="queued">في الانتظار</option><option value="processing">قيد التنفيذ</option><option value="completed">مكتملة</option><option value="failed">فاشلة</option><option value="cancelled">ملغاة</option></select>
      </div>
      {(error || actionError) && <div className="admin-alert">{error || actionError}</div>}
      <div className="admin-panel"><div className="admin-table-wrap"><table className="admin-table">
        <thead><tr><th>الوظيفة</th><th>المستخدم</th><th>الحالة</th><th>المحاولات</th><th>المدة</th><th>الإنشاء</th><th>إجراء</th></tr></thead>
        <tbody>{data?.results.map((job) => <tr key={job.id}>
          <td><strong>{job.title}</strong><small>{job.report_type_name} · #{job.id}</small></td><td>{job.user}</td>
          <td><StatusBadge active={job.status === 'completed'} label={job.status} /></td><td>{job.attempts}</td>
          <td>{job.duration_seconds == null ? '—' : `${job.duration_seconds} ث`}</td><td>{new Date(job.created_at).toLocaleString('ar-SY')}</td>
          <td><div className="admin-row-actions">{job.status === 'failed' && <button type="button" title="إعادة التشغيل" onClick={() => runAction(job, 'retry')}><RefreshCw size={16} /></button>}{activeStatuses.has(job.status) && <button type="button" title="إلغاء" onClick={() => runAction(job, 'cancel')}><Square size={15} /></button>}</div></td>
        </tr>)}</tbody>
      </table>{loading && <div className="admin-loading">جارٍ تحميل الوظائف...</div>}{!loading && !data?.results.length && <AdminEmpty message="لا توجد وظائف مطابقة." />}</div>
      {data && <Pagination page={page} hasNext={!!data.next} hasPrevious={!!data.previous} onChange={setPage} />}</div>
    </main>
  );
}
