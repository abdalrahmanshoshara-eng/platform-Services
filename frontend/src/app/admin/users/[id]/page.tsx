'use client';

import { ArrowRight, Ban, CalendarDays, Check, CheckCircle2, Clock3, Infinity, ShieldOff } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import { AdminHeader, StatusBadge } from '@/components/admin/AdminUI';
import { apiFetch } from '@/shared/api/client';
import type { AdminService, AdminUser } from '@/shared/api/types';

type DurationMode = 'permanent' | '5' | '15' | '30' | 'custom';

function localInput(date: Date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

export default function AdminUserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [user, setUser] = useState<AdminUser | null>(null);
  const [services, setServices] = useState<AdminService[]>([]);
  const [selectedServices, setSelectedServices] = useState<number[]>([]);
  const [reason, setReason] = useState('');
  const [duration, setDuration] = useState<DurationMode>('5');
  const [startsAt, setStartsAt] = useState(localInput(new Date()));
  const [expiresAt, setExpiresAt] = useState(localInput(new Date(Date.now() + 5 * 86400000)));
  const [disableOpen, setDisableOpen] = useState(false);
  const [disableReason, setDisableReason] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([
      apiFetch<AdminUser>(`/v1/admin/users/${id}/`),
      apiFetch<{ results: AdminService[] }>('/v1/admin/services/?ordering=sort_order'),
    ]).then(([account, serviceData]) => {
      setUser(account);
      setServices(serviceData.results);
    }).catch((err) => setError(err instanceof Error ? err.message : 'تعذر تحميل المستخدم.'));
  }, [id]);

  const selectedCount = selectedServices.length;
  const restrictionPeriod = useMemo(() => {
    const start = new Date(startsAt);
    if (duration === 'permanent') return { starts_at: start.toISOString(), expires_at: null };
    if (duration === 'custom') return {
      starts_at: start.toISOString(),
      expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
    };
    return {
      starts_at: start.toISOString(),
      expires_at: new Date(start.getTime() + Number(duration) * 86400000).toISOString(),
    };
  }, [duration, startsAt, expiresAt]);

  function chooseDuration(value: DurationMode) {
    setDuration(value);
    if (value !== 'custom' && value !== 'permanent') {
      setExpiresAt(localInput(new Date(new Date(startsAt).getTime() + Number(value) * 86400000)));
    }
  }

  function toggleService(serviceId: number) {
    setSelectedServices((current) => current.includes(serviceId)
      ? current.filter((idValue) => idValue !== serviceId)
      : [...current, serviceId]);
  }

  async function toggleAccount() {
    if (!user) return;
    setSaving(true);
    setError('');
    try {
      const action = user.is_active ? 'deactivate' : 'activate';
      const updated = await apiFetch<AdminUser>(`/v1/admin/users/${id}/${action}/`, {
        method: 'POST',
        body: { reason: disableReason },
      });
      setUser(updated);
      setDisableOpen(false);
      setDisableReason('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'تعذر تنفيذ العملية.');
    } finally {
      setSaving(false);
    }
  }

  async function addRestrictions(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      const updated = await apiFetch<AdminUser>(`/v1/admin/users/${id}/restrictions/`, {
        method: 'POST',
        body: {
          mode: 'add',
          service_ids: selectedServices,
          reason,
          ...restrictionPeriod,
        },
      });
      setUser(updated);
      setReason('');
      setSelectedServices([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'تعذر حفظ القيود.');
    } finally {
      setSaving(false);
    }
  }

  async function removeRestriction(targetId: number) {
    setSaving(true);
    try {
      const updated = await apiFetch<AdminUser>(`/v1/admin/users/${id}/restrictions/`, {
        method: 'POST',
        body: { mode: 'remove', service_ids: [targetId] },
      });
      setUser(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'تعذر إزالة القيد.');
    } finally {
      setSaving(false);
    }
  }

  if (!user && !error) return <main className="admin-content"><div className="admin-loading">جارٍ تحميل الحساب...</div></main>;

  return (
    <main className="admin-content">
      <Link className="admin-back-link" href="/admin/users"><ArrowRight size={16} /> العودة إلى المستخدمين</Link>
      <AdminHeader
        title={user?.full_name || 'تفاصيل المستخدم'}
        description={user ? `${user.email || user.username} · انضم ${new Date(user.date_joined).toLocaleDateString('ar-SY')}` : ''}
        action={user && (
          <button
            className={user.is_active ? 'admin-danger-button' : 'admin-primary-button'}
            type="button"
            onClick={() => user.is_active ? setDisableOpen(true) : toggleAccount()}
            disabled={saving}
          >
            {user.is_active ? <><Ban size={17} /> تعطيل الحساب</> : <><CheckCircle2 size={17} /> تفعيل الحساب</>}
          </button>
        )}
      />
      {error && <div className="admin-alert">{error}</div>}

      {user && (
        <>
          <section className="admin-detail-strip">
            <div><small>الحالة</small><StatusBadge active={user.is_active} /></div>
            <div><small>الدور</small><strong>{user.is_staff ? 'مدير النظام' : 'مستخدم'}</strong></div>
            <div><small>التقارير</small><strong>{user.reports_count}</strong></div>
            <div><small>آخر دخول</small><strong>{user.last_login ? new Date(user.last_login).toLocaleString('ar-SY') : 'لم يسجل بعد'}</strong></div>
          </section>

          {!user.is_active && <div className="admin-notice"><ShieldOff size={19} /><div><strong>الحساب معطل</strong><p>{user.disabled_reason || 'لم يحدد سبب للتعطيل.'}</p></div></div>}

          <form className="admin-restriction-workspace" onSubmit={addRestrictions}>
            <section className="admin-panel">
              <div className="admin-panel-heading">
                <div><h3>اختر الخدمات المراد تقييدها</h3><p>اضغط على بطاقة الخدمة لتحديدها أو إلغاء تحديدها.</p></div>
                <span className="admin-selection-count">{selectedCount} محددة</span>
              </div>
              <div className="admin-service-picker">
                {services.map((service) => {
                  const selected = selectedServices.includes(service.id);
                  return (
                    <button
                      className={selected ? 'selected' : ''}
                      type="button"
                      key={service.id}
                      onClick={() => toggleService(service.id)}
                      aria-pressed={selected}
                    >
                      <span className="admin-picker-check">{selected && <Check size={15} />}</span>
                      <strong>{service.name}</strong>
                      <small>{service.description}</small>
                    </button>
                  );
                })}
              </div>
            </section>

            <section className="admin-panel admin-restriction-period">
              <div className="admin-panel-heading"><div><h3>مدة التقييد</h3><p>اختر مدة جاهزة أو حدد فترة دقيقة.</p></div><Clock3 size={19} /></div>
              <div className="admin-form-body">
                <label>بداية التقييد<input type="datetime-local" value={startsAt} onChange={(event) => setStartsAt(event.target.value)} required /></label>
                <div className="admin-duration-options">
                  {([
                    ['5', '5 أيام'],
                    ['15', '15 يوماً'],
                    ['30', '30 يوماً'],
                    ['permanent', 'دائم'],
                    ['custom', 'فترة مخصصة'],
                  ] as [DurationMode, string][]).map(([value, label]) => (
                    <button className={duration === value ? 'active' : ''} type="button" key={value} onClick={() => chooseDuration(value)}>
                      {value === 'permanent' ? <Infinity size={16} /> : value === 'custom' ? <CalendarDays size={16} /> : null}
                      {label}
                    </button>
                  ))}
                </div>
                {duration === 'custom' && <label>نهاية التقييد<input type="datetime-local" value={expiresAt} onChange={(event) => setExpiresAt(event.target.value)} required /></label>}
                <label>سبب التقييد <span>(اختياري)</span><textarea rows={3} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="ملاحظة داخلية تساعد الإدارة لاحقاً" /></label>
                <button className="admin-primary-button" type="submit" disabled={saving || selectedCount === 0}>تطبيق التقييد على {selectedCount || 0} خدمة</button>
              </div>
            </section>
          </form>

          <section className="admin-panel admin-current-restrictions">
            <div className="admin-panel-heading"><div><h3>القيود الحالية</h3><p>جميع الخدمات المقيدة وفترة كل قيد.</p></div></div>
            <div className="admin-restrictions">
              {user.restrictions?.map((restriction) => (
                <article key={restriction.id}>
                  <div>
                    <strong>{restriction.target_name}</strong>
                    <small>
                      {restriction.starts_at ? `من ${new Date(restriction.starts_at).toLocaleString('ar-SY')}` : 'من الآن'}
                      {' · '}
                      {restriction.expires_at ? `حتى ${new Date(restriction.expires_at).toLocaleString('ar-SY')}` : 'دائم'}
                      {restriction.reason ? ` · ${restriction.reason}` : ''}
                    </small>
                  </div>
                  <div><StatusBadge active={!restriction.is_expired} label={restriction.is_expired ? 'منتهي' : 'ساري'} /><button type="button" onClick={() => removeRestriction(restriction.target_id)} disabled={saving}>إزالة</button></div>
                </article>
              ))}
              {!user.restrictions?.length && <p className="admin-muted">لا توجد قيود على هذا المستخدم.</p>}
            </div>
          </section>
        </>
      )}

      {disableOpen && (
        <div className="admin-modal-backdrop" role="presentation" onMouseDown={() => setDisableOpen(false)}>
          <section className="admin-modal" role="dialog" aria-modal="true" aria-labelledby="disable-title" onMouseDown={(event) => event.stopPropagation()}>
            <div className="admin-modal-icon danger"><Ban size={22} /></div>
            <h3 id="disable-title">تعطيل حساب {user?.full_name}</h3>
            <p>لن يتمكن المستخدم من تسجيل الدخول حتى تعيد تفعيل الحساب.</p>
            <label>سبب التعطيل <span>(اختياري)</span><textarea rows={3} value={disableReason} onChange={(event) => setDisableReason(event.target.value)} /></label>
            <div className="admin-modal-actions">
              <button className="admin-secondary-button" type="button" onClick={() => setDisableOpen(false)}>إلغاء</button>
              <button className="admin-danger-button" type="button" onClick={toggleAccount} disabled={saving}>تأكيد التعطيل</button>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
