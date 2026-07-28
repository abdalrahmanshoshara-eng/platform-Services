'use client';

import { Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import { AdminEmpty, AdminHeader, DetailLink, Pagination, StatusBadge } from '@/components/admin/AdminUI';
import type { AdminUser } from '@/shared/api/types';
import { useAdminList } from '@/shared/admin/useAdminList';

export default function AdminUsersPage() {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [role, setRole] = useState('');
  const [page, setPage] = useState(1);
  const query = useMemo(() => new URLSearchParams({ search, status, role, page: String(page) }).toString(), [search, status, role, page]);
  const { data, loading, error } = useAdminList<AdminUser>('/v1/admin/users/', query);

  return (
    <main className="admin-content">
      <AdminHeader title="المستخدمون" description="إدارة الحسابات والصلاحيات والقيود على الخدمات." />
      <div className="admin-filters">
        <label className="admin-search"><Search size={17} /><input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="بحث بالاسم أو البريد أو الهاتف" /></label>
        <select value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="">كل الحالات</option><option value="active">نشط</option><option value="inactive">معطل</option></select>
        <select value={role} onChange={(event) => { setRole(event.target.value); setPage(1); }}><option value="">كل الأدوار</option><option value="admin">مدير</option><option value="user">مستخدم</option></select>
      </div>
      {error && <div className="admin-alert">{error}</div>}
      <div className="admin-panel">
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead><tr><th>المستخدم</th><th>الدور</th><th>التقارير</th><th>القيود</th><th>الحالة</th><th></th></tr></thead>
            <tbody>
              {data?.results.map((user) => (
                <tr key={user.id}>
                  <td><strong>{user.full_name}</strong><small>{user.email || user.username}</small></td>
                  <td>{user.is_staff || user.is_superuser ? 'مدير النظام' : 'مستخدم'}</td>
                  <td>{user.reports_count}</td><td>{user.restrictions_count}</td>
                  <td><StatusBadge active={user.is_active} /></td>
                  <td><DetailLink href={`/admin/users/${user.id}`}>التفاصيل</DetailLink></td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && !data?.results.length && <AdminEmpty message="لا توجد حسابات مطابقة للفلاتر الحالية." />}
          {loading && <div className="admin-loading">جارٍ تحميل المستخدمين...</div>}
        </div>
        {data && <Pagination page={page} hasNext={!!data.next} hasPrevious={!!data.previous} onChange={setPage} />}
      </div>
    </main>
  );
}
