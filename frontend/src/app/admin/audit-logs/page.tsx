'use client';

import { Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import { AdminEmpty, AdminHeader, Pagination, StatusBadge } from '@/components/admin/AdminUI';
import { useAdminList } from '@/shared/admin/useAdminList';
import type { AuditEvent } from '@/shared/api/types';

export default function AdminAuditPage() {
  const [search, setSearch] = useState('');
  const [outcome, setOutcome] = useState('');
  const [page, setPage] = useState(1);
  const query = useMemo(() => new URLSearchParams({ search, outcome, page: String(page) }).toString(), [search, outcome, page]);
  const { data, loading, error } = useAdminList<AuditEvent>('/v1/admin/audit-logs/', query);
  return (
    <main className="admin-content">
      <AdminHeader title="سجل التدقيق" description="سجل غير قابل للتعديل للعمليات الأمنية والإدارية الحساسة." />
      <div className="admin-filters"><label className="admin-search"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="بحث بالعملية أو المنفذ أو Request ID" /></label><select value={outcome} onChange={(event) => setOutcome(event.target.value)}><option value="">كل النتائج</option><option value="success">ناجحة</option><option value="failure">فاشلة</option><option value="denied">مرفوضة</option></select></div>
      {error && <div className="admin-alert">{error}</div>}
      <div className="admin-panel"><div className="admin-table-wrap"><table className="admin-table">
        <thead><tr><th>العملية</th><th>المنفذ</th><th>الهدف</th><th>IP</th><th>النتيجة</th><th>الوقت</th></tr></thead>
        <tbody>{data?.results.map((event) => <tr key={event.id}><td><strong>{event.action}</strong><small>{event.request_id || 'بدون Request ID'}</small></td><td>{event.actor_name}</td><td>{event.target_type ? `${event.target_type} #${event.target_id}` : '—'}</td><td dir="ltr">{event.ip_address || '—'}</td><td><StatusBadge active={event.outcome === 'success'} label={event.outcome} /></td><td>{new Date(event.created_at).toLocaleString('ar-SY')}</td></tr>)}</tbody>
      </table>{loading && <div className="admin-loading">جارٍ تحميل السجل...</div>}{!loading && !data?.results.length && <AdminEmpty message="لا توجد أحداث مطابقة." />}</div>{data && <Pagination page={page} hasNext={!!data.next} hasPrevious={!!data.previous} onChange={setPage} />}</div>
    </main>
  );
}
