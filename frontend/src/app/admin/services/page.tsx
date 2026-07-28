'use client';

import { Ban, Boxes, ExternalLink, Search, Settings2, ShieldCheck } from 'lucide-react';
import Link from 'next/link';
import { useMemo, useState } from 'react';
import { AdminEmpty, AdminHeader, Pagination, StatusBadge } from '@/components/admin/AdminUI';
import { apiFetch } from '@/shared/api/client';
import { useAdminList } from '@/shared/admin/useAdminList';
import type { AdminService } from '@/shared/api/types';

export default function AdminServicesPage() {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [kind, setKind] = useState('');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<AdminService | null>(null);
  const [reason, setReason] = useState('');
  const [actionError, setActionError] = useState('');
  const [saving, setSaving] = useState(false);
  const query = useMemo(() => new URLSearchParams({ search, status, kind, page: String(page) }).toString(), [search, status, kind, page]);
  const { data, loading, error, reload } = useAdminList<AdminService>('/v1/admin/services/', query);

  async function toggleService(service: AdminService) {
    setSaving(true);
    setActionError('');
    try {
      await apiFetch(`/v1/admin/services/${service.id}/${service.is_active ? 'deactivate' : 'activate'}/`, {
        method: 'POST',
        body: { reason },
      });
      setSelected(null);
      setReason('');
      reload();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'تعذر تغيير حالة الخدمة.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="admin-content">
      <AdminHeader title="الخدمات" description="إدارة كل خدمة وحالتها وإعداداتها من مكان واحد." />
      <div className="admin-filters">
        <label className="admin-search"><Search size={17} /><input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="بحث في الخدمات" /></label>
        <select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">كل الحالات</option><option value="active">نشطة</option><option value="inactive">معطلة</option></select>
        <select value={kind} onChange={(event) => setKind(event.target.value)}><option value="">كل الأنواع</option><option value="internal">داخلية</option><option value="external">خارجية</option></select>
      </div>
      {(error || actionError) && <div className="admin-alert">{error || actionError}</div>}

      <section className="admin-services-grid">
        {data?.results.map((service) => (
          <article className={`admin-service-admin-card ${service.is_active ? '' : 'disabled'}`} key={service.id}>
            <div className="admin-service-card-head">
              <span className="admin-service-card-icon"><Boxes size={21} /></span>
              <StatusBadge active={service.is_active} />
            </div>
            <div className="admin-service-card-body">
              <small>{service.kind === 'internal' ? 'خدمة داخلية' : 'خدمة خارجية'}</small>
              <h3>{service.name}</h3>
              <p>{service.description}</p>
            </div>
            <div className="admin-service-card-stats">
              <span><strong>{service.launches_count}</strong> تشغيل</span>
              <span><strong>{service.restrictions_count}</strong> مستخدم مقيد</span>
              {service.requires_staff && <span><ShieldCheck size={14} /> للمديرين</span>}
            </div>
            <div className="admin-service-card-actions">
              <Link href={`/admin/services/${service.id}`}><Settings2 size={16} /> إدارة كاملة</Link>
              <button type="button" className={service.is_active ? 'danger' : 'activate'} onClick={() => service.is_active ? setSelected(service) : toggleService(service)}>
                {service.is_active ? <><Ban size={15} /> تعطيل</> : <><ShieldCheck size={15} /> تفعيل</>}
              </button>
            </div>
            {service.kind === 'external' && <ExternalLink className="admin-service-external" size={14} />}
          </article>
        ))}
      </section>
      {loading && <div className="admin-loading">جارٍ تحميل الخدمات...</div>}
      {!loading && !data?.results.length && <AdminEmpty message="لا توجد خدمات مطابقة." />}
      {data && <Pagination page={page} hasNext={!!data.next} hasPrevious={!!data.previous} onChange={setPage} />}

      {selected && (
        <div className="admin-modal-backdrop" role="presentation" onMouseDown={() => setSelected(null)}>
          <section className="admin-modal" role="dialog" aria-modal="true" aria-labelledby="service-disable-title" onMouseDown={(event) => event.stopPropagation()}>
            <div className="admin-modal-icon danger"><Ban size={22} /></div>
            <h3 id="service-disable-title">تعطيل خدمة {selected.name}</h3>
            <p>ستختفي الخدمة فوراً عن المستخدمين حتى تعيد تفعيلها.</p>
            <label>سبب التعطيل <span>(اختياري)</span><textarea rows={3} value={reason} onChange={(event) => setReason(event.target.value)} /></label>
            <div className="admin-modal-actions">
              <button className="admin-secondary-button" type="button" onClick={() => setSelected(null)}>إلغاء</button>
              <button className="admin-danger-button" type="button" onClick={() => toggleService(selected)} disabled={saving}>تأكيد التعطيل</button>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
