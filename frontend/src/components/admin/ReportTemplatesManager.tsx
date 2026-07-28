'use client';

import { FilePlus2, FileText, Pencil, Power } from 'lucide-react';
import { FormEvent, useEffect, useState } from 'react';
import { apiFetch } from '@/shared/api/client';
import type { AdminReportType, PaginatedResponse } from '@/shared/api/types';
import { StatusBadge } from './AdminUI';

type Draft = {
  id?: number;
  name: string;
  slug: string;
  description: string;
  template_file: string;
  fields_schema: string;
  is_active: boolean;
};

const emptyDraft: Draft = {
  name: '',
  slug: '',
  description: '',
  template_file: '',
  fields_schema: '[]',
  is_active: true,
};

export default function ReportTemplatesManager() {
  const [items, setItems] = useState<AdminReportType[]>([]);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    try {
      const data = await apiFetch<PaginatedResponse<AdminReportType>>('/v1/admin/report-types/?ordering=name');
      setItems(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'تعذر تحميل القوالب.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  function edit(item: AdminReportType) {
    setDraft({
      id: item.id,
      name: item.name,
      slug: item.slug,
      description: item.description,
      template_file: item.template_file,
      fields_schema: JSON.stringify(item.fields_schema, null, 2),
      is_active: item.is_active,
    });
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!draft) return;
    setSaving(true);
    setError('');
    try {
      const fieldsSchema = JSON.parse(draft.fields_schema);
      if (!Array.isArray(fieldsSchema)) throw new Error('مخطط الحقول يجب أن يكون مصفوفة JSON.');
      const path = draft.id ? `/v1/admin/report-types/${draft.id}/` : '/v1/admin/report-types/';
      await apiFetch(path, {
        method: draft.id ? 'PATCH' : 'POST',
        body: {
          name: draft.name,
          slug: draft.slug,
          description: draft.description,
          template_file: draft.template_file,
          fields_schema: fieldsSchema,
          is_active: draft.is_active,
        },
      });
      setDraft(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'تعذر حفظ القالب.');
    } finally {
      setSaving(false);
    }
  }

  async function toggle(item: AdminReportType) {
    setError('');
    try {
      await apiFetch(`/v1/admin/report-types/${item.id}/`, { method: 'PATCH', body: { is_active: !item.is_active } });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'تعذر تغيير حالة القالب.');
    }
  }

  return (
    <section className="admin-panel admin-templates-manager">
      <div className="admin-panel-heading">
        <div><h3>قوالب التقارير</h3><p>إنشاء القوالب وتعديل مخطط الحقول والتحكم بحالتها.</p></div>
        <button className="admin-primary-button" type="button" onClick={() => setDraft({ ...emptyDraft })}><FilePlus2 size={16} /> قالب جديد</button>
      </div>
      {error && <div className="admin-inline-alert">{error}</div>}
      <div className="admin-template-grid">
        {items.map((item) => (
          <article key={item.id}>
            <div className="admin-template-icon"><FileText size={20} /></div>
            <div className="admin-template-info">
              <div><h4>{item.name}</h4><StatusBadge active={item.is_active} /></div>
              <p>{item.description || 'لا يوجد وصف لهذا القالب.'}</p>
              <small>{item.template_file} · {item.fields_schema.length} حقول · {item.reports_count} تقارير</small>
            </div>
            <div className="admin-template-actions">
              <button type="button" onClick={() => edit(item)}><Pencil size={15} /> تعديل</button>
              <button type="button" className={item.is_active ? 'danger' : ''} onClick={() => toggle(item)}><Power size={15} /> {item.is_active ? 'تعطيل' : 'تفعيل'}</button>
            </div>
          </article>
        ))}
        {!loading && !items.length && <p className="admin-muted">لا توجد قوالب تقارير.</p>}
        {loading && <div className="admin-loading">جارٍ تحميل القوالب...</div>}
      </div>

      {draft && (
        <div className="admin-modal-backdrop" role="presentation" onMouseDown={() => setDraft(null)}>
          <form className="admin-modal admin-template-modal" onSubmit={save} onMouseDown={(event) => event.stopPropagation()}>
            <h3>{draft.id ? 'تعديل قالب التقرير' : 'إنشاء قالب تقرير'}</h3>
            <div className="admin-modal-form-grid">
              <label>اسم القالب<input value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} required /></label>
              <label>المعرّف Slug<input dir="ltr" value={draft.slug} onChange={(event) => setDraft({ ...draft, slug: event.target.value })} required /></label>
              <label className="wide">الوصف<textarea rows={3} value={draft.description} onChange={(event) => setDraft({ ...draft, description: event.target.value })} /></label>
              <label className="wide">ملف DOCX<input dir="ltr" value={draft.template_file} onChange={(event) => setDraft({ ...draft, template_file: event.target.value })} placeholder="template.docx" required /></label>
              <label className="wide">مخطط الحقول JSON<textarea className="admin-code-input" rows={10} value={draft.fields_schema} onChange={(event) => setDraft({ ...draft, fields_schema: event.target.value })} required /></label>
              <label className="admin-check wide"><input type="checkbox" checked={draft.is_active} onChange={(event) => setDraft({ ...draft, is_active: event.target.checked })} /> القالب مفعّل ومتاح للمستخدمين</label>
            </div>
            <div className="admin-modal-actions">
              <button className="admin-secondary-button" type="button" onClick={() => setDraft(null)}>إلغاء</button>
              <button className="admin-primary-button" type="submit" disabled={saving}>حفظ القالب</button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
