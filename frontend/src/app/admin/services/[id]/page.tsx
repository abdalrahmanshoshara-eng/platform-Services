'use client';

import { ArrowRight, Ban, CheckCircle2, ExternalLink, Save } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';
import ReportTemplatesManager from '@/components/admin/ReportTemplatesManager';
import { AdminHeader, StatusBadge } from '@/components/admin/AdminUI';
import { apiFetch } from '@/shared/api/client';
import type { AdminService } from '@/shared/api/types';

type ServiceDraft = {
  name: string;
  slug: string;
  description: string;
  kind: 'internal' | 'external';
  launch_target: string;
  icon: string;
  accent: string;
  sort_order: number;
  requires_staff: boolean;
  settings: string;
};

export default function AdminServiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [service, setService] = useState<AdminService | null>(null);
  const [draft, setDraft] = useState<ServiceDraft | null>(null);
  const [tab, setTab] = useState<'overview' | 'settings' | 'reports'>('overview');
  const [disableOpen, setDisableOpen] = useState(false);
  const [disableReason, setDisableReason] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [saving, setSaving] = useState(false);

  function hydrate(value: AdminService) {
    setService(value);
    setDraft({
      name: value.name,
      slug: value.slug,
      description: value.description,
      kind: value.kind,
      launch_target: value.launch_target,
      icon: value.icon,
      accent: value.accent,
      sort_order: value.sort_order,
      requires_staff: value.requires_staff,
      settings: JSON.stringify(value.settings || {}, null, 2),
    });
  }

  useEffect(() => {
    apiFetch<AdminService>(`/v1/admin/services/${id}/`).then(hydrate).catch((err) => setError(err instanceof Error ? err.message : 'تعذر تحميل الخدمة.'));
  }, [id]);

  async function toggleService() {
    if (!service) return;
    setSaving(true);
    setError('');
    try {
      const action = service.is_active ? 'deactivate' : 'activate';
      hydrate(await apiFetch<AdminService>(`/v1/admin/services/${id}/${action}/`, {
        method: 'POST',
        body: { reason: disableReason },
      }));
      setDisableOpen(false);
      setDisableReason('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'تعذر تنفيذ العملية.');
    } finally {
      setSaving(false);
    }
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!draft) return;
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const parsedSettings = JSON.parse(draft.settings);
      hydrate(await apiFetch<AdminService>(`/v1/admin/services/${id}/`, {
        method: 'PATCH',
        body: {
          name: draft.name,
          slug: draft.slug,
          description: draft.description,
          kind: draft.kind,
          launch_target: draft.launch_target,
          icon: draft.icon,
          accent: draft.accent,
          sort_order: draft.sort_order,
          requires_staff: draft.requires_staff,
          settings: parsedSettings,
        },
      }));
      setSuccess('تم حفظ إعدادات الخدمة بنجاح.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'تحقق من البيانات وإعدادات JSON.');
    } finally {
      setSaving(false);
    }
  }

  if (!service || !draft) {
    return <main className="admin-content">{error ? <div className="admin-alert">{error}</div> : <div className="admin-loading">جارٍ تحميل الخدمة...</div>}</main>;
  }

  const isReportsService = service.slug === 'reports' || service.launch_target.startsWith('/reports');

  return (
    <main className="admin-content">
      <Link className="admin-back-link" href="/admin/services"><ArrowRight size={16} /> العودة إلى الخدمات</Link>
      <AdminHeader
        title={service.name}
        description={`${service.kind === 'internal' ? 'خدمة داخلية' : 'خدمة خارجية'} · آخر تحديث ${new Date(service.updated_at).toLocaleString('ar-SY')}`}
        action={(
          <button
            className={service.is_active ? 'admin-danger-button' : 'admin-primary-button'}
            onClick={() => service.is_active ? setDisableOpen(true) : toggleService()}
            type="button"
            disabled={saving}
          >
            {service.is_active ? <><Ban size={17} /> تعطيل الخدمة</> : <><CheckCircle2 size={17} /> تفعيل الخدمة</>}
          </button>
        )}
      />
      {error && <div className="admin-alert">{error}</div>}
      {success && <div className="admin-success">{success}</div>}

      <section className="admin-detail-strip">
        <div><small>الحالة</small><StatusBadge active={service.is_active} /></div>
        <div><small>مرات التشغيل</small><strong>{service.launches_count}</strong></div>
        <div><small>المستخدمون المقيدون</small><strong>{service.restrictions_count}</strong></div>
        <div><small>وجهة التشغيل</small><strong className="admin-truncate">{service.launch_target}</strong></div>
      </section>
      {!service.is_active && <div className="admin-notice"><Ban size={19} /><div><strong>الخدمة متوقفة</strong><p>{service.disabled_reason || 'لم يحدد سبب للتعطيل.'}</p></div></div>}

      <div className="admin-tabs">
        <button className={tab === 'overview' ? 'active' : ''} onClick={() => setTab('overview')} type="button">البيانات الأساسية</button>
        <button className={tab === 'settings' ? 'active' : ''} onClick={() => setTab('settings')} type="button">الإعدادات المتقدمة</button>
        {isReportsService && <button className={tab === 'reports' ? 'active' : ''} onClick={() => setTab('reports')} type="button">قوالب التقارير</button>}
      </div>

      {tab === 'reports' && isReportsService ? <ReportTemplatesManager /> : (
        <form className="admin-panel admin-form admin-service-form" onSubmit={save}>
          <div className="admin-form-body">
            {tab === 'overview' ? (
              <div className="admin-service-fields">
                <label>اسم الخدمة<input value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} required /></label>
                <label>المعرّف Slug<input dir="ltr" value={draft.slug} onChange={(event) => setDraft({ ...draft, slug: event.target.value })} required /></label>
                <label className="wide">وصف الخدمة<textarea value={draft.description} onChange={(event) => setDraft({ ...draft, description: event.target.value })} rows={4} required /></label>
                <label>نوع الخدمة<select value={draft.kind} onChange={(event) => setDraft({ ...draft, kind: event.target.value as 'internal' | 'external' })}><option value="internal">داخلية</option><option value="external">خارجية</option></select></label>
                <label>ترتيب الظهور<input type="number" min={0} value={draft.sort_order} onChange={(event) => setDraft({ ...draft, sort_order: Number(event.target.value) })} /></label>
                <label className="wide">وجهة التشغيل<div className="admin-input-with-icon"><ExternalLink size={17} /><input dir="ltr" value={draft.launch_target} onChange={(event) => setDraft({ ...draft, launch_target: event.target.value })} required /></div></label>
                <label>اسم الأيقونة<input dir="ltr" value={draft.icon} onChange={(event) => setDraft({ ...draft, icon: event.target.value })} /></label>
                <label>لون البطاقة<select value={draft.accent} onChange={(event) => setDraft({ ...draft, accent: event.target.value })}><option value="green">أخضر</option><option value="teal">فيروزي</option><option value="gold">ذهبي</option></select></label>
                <label className="admin-check wide"><input type="checkbox" checked={draft.requires_staff} onChange={(event) => setDraft({ ...draft, requires_staff: event.target.checked })} /> متاحة للمديرين فقط</label>
              </div>
            ) : (
              <label>إعدادات الخدمة بصيغة JSON<textarea className="admin-code-input" dir="ltr" value={draft.settings} onChange={(event) => setDraft({ ...draft, settings: event.target.value })} rows={14} spellCheck={false} /></label>
            )}
            <button className="admin-primary-button" type="submit" disabled={saving}><Save size={16} /> حفظ التغييرات</button>
          </div>
        </form>
      )}

      {disableOpen && (
        <div className="admin-modal-backdrop" role="presentation" onMouseDown={() => setDisableOpen(false)}>
          <section className="admin-modal" role="dialog" aria-modal="true" aria-labelledby="disable-service-title" onMouseDown={(event) => event.stopPropagation()}>
            <div className="admin-modal-icon danger"><Ban size={22} /></div>
            <h3 id="disable-service-title">تعطيل خدمة {service.name}</h3>
            <p>ستتوقف الخدمة عن الظهور والعمل لجميع المستخدمين.</p>
            <label>سبب التعطيل <span>(اختياري)</span><textarea rows={3} value={disableReason} onChange={(event) => setDisableReason(event.target.value)} /></label>
            <div className="admin-modal-actions">
              <button className="admin-secondary-button" type="button" onClick={() => setDisableOpen(false)}>إلغاء</button>
              <button className="admin-danger-button" type="button" onClick={toggleService} disabled={saving}>تأكيد التعطيل</button>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
