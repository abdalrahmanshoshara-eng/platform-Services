'use client';

import {
  Archive,
  FileCheck2,
  FilePlus2,
  FileText,
  Pencil,
  Power,
  Upload,
} from 'lucide-react';
import { FormEvent, useEffect, useState } from 'react';
import { apiFetch } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';
import type {
  AdminReportType,
  AdminTemplateVersion,
  PaginatedResponse,
  TemplateVersionStatus,
} from '@/shared/api/types';
import { StatusBadge } from './AdminUI';

type Draft = {
  id?: number;
  name: string;
  slug: string;
  description: string;
  fields_schema: string;
  is_active: boolean;
};

const emptyDraft: Draft = {
  name: '',
  slug: '',
  description: '',
  fields_schema: '[]',
  is_active: true,
};

const statusLabels: Record<TemplateVersionStatus, string> = {
  draft: 'مسودة',
  validated: 'تم التحقق',
  active: 'نشطة',
  inactive: 'غير نشطة',
  archived: 'مؤرشفة',
  rejected: 'مرفوضة',
};

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

export default function ReportTemplatesManager() {
  const [items, setItems] = useState<AdminReportType[]>([]);
  const [versions, setVersions] = useState<AdminTemplateVersion[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busyVersion, setBusyVersion] = useState<number | null>(null);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    try {
      const data = await apiFetch<PaginatedResponse<AdminReportType>>(
        `${API_ENDPOINTS.admin.reportTypes}?ordering=name`,
      );
      setItems(data.results);
    } catch (err) {
      setError(errorMessage(err, 'تعذر تحميل أنواع التقارير.'));
    } finally {
      setLoading(false);
    }
  }

  async function loadVersions(reportTypeId: number) {
    try {
      const data = await apiFetch<AdminTemplateVersion[]>(
        API_ENDPOINTS.admin.templateVersions(reportTypeId),
      );
      setVersions(data);
    } catch (err) {
      setError(errorMessage(err, 'تعذر تحميل نسخ القالب.'));
    }
  }

  useEffect(() => {
    load();
  }, []);

  function edit(item: AdminReportType) {
    setDraft({
      id: item.id,
      name: item.name,
      slug: item.slug,
      description: item.description,
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
      if (!Array.isArray(fieldsSchema)) {
        throw new Error('مخطط الحقول يجب أن يكون مصفوفة JSON.');
      }
      const path = draft.id
        ? API_ENDPOINTS.admin.reportType(draft.id)
        : API_ENDPOINTS.admin.reportTypes;
      await apiFetch(path, {
        method: draft.id ? 'PATCH' : 'POST',
        body: {
          name: draft.name,
          slug: draft.slug,
          description: draft.description,
          fields_schema: fieldsSchema,
          is_active: draft.is_active,
        },
      });
      setDraft(null);
      await load();
    } catch (err) {
      setError(errorMessage(err, 'تعذر حفظ نوع التقرير.'));
    } finally {
      setSaving(false);
    }
  }

  async function toggle(item: AdminReportType) {
    const verb = item.is_active ? 'تعطيل' : 'تفعيل';
    if (!window.confirm(`هل تريد ${verb} نوع التقرير «${item.name}»؟`)) return;
    setError('');
    try {
      await apiFetch(API_ENDPOINTS.admin.reportType(item.id), {
        method: 'PATCH',
        body: { is_active: !item.is_active },
      });
      await load();
    } catch (err) {
      setError(errorMessage(err, 'تعذر تغيير حالة نوع التقرير.'));
    }
  }

  async function selectVersions(reportTypeId: number) {
    if (selectedId === reportTypeId) {
      setSelectedId(null);
      setVersions([]);
      return;
    }
    setSelectedId(reportTypeId);
    setUploadFile(null);
    await loadVersions(reportTypeId);
  }

  async function upload(event: FormEvent) {
    event.preventDefault();
    if (!selectedId || !uploadFile) return;
    const form = new FormData();
    form.append('template_file', uploadFile);
    setSaving(true);
    setError('');
    try {
      await apiFetch(API_ENDPOINTS.admin.templateVersions(selectedId), {
        method: 'POST',
        body: form,
      });
      setUploadFile(null);
      await Promise.all([loadVersions(selectedId), load()]);
    } catch (err) {
      setError(errorMessage(err, 'تعذر رفع ملف القالب.'));
    } finally {
      setSaving(false);
    }
  }

  async function lifecycle(version: AdminTemplateVersion, action: string, label: string) {
    if (!selectedId) return;
    if (!window.confirm(`هل تريد ${label} النسخة ${version.version}؟`)) return;
    setBusyVersion(version.id);
    setError('');
    try {
      await apiFetch(
        API_ENDPOINTS.admin.templateVersionAction(selectedId, version.id, action),
        { method: 'POST', body: { reason: `إجراء من لوحة الإدارة: ${label}` } },
      );
      await Promise.all([loadVersions(selectedId), load()]);
    } catch (err) {
      setError(errorMessage(err, `تعذر ${label} نسخة القالب.`));
    } finally {
      setBusyVersion(null);
    }
  }

  return (
    <section className="admin-panel admin-templates-manager">
      <div className="admin-panel-heading">
        <div>
          <h3>قوالب التقارير</h3>
          <p>إدارة أنواع التقارير ونسخ DOCX المتحققة ودورة تفعيلها.</p>
        </div>
        <button
          className="admin-primary-button"
          type="button"
          onClick={() => setDraft({ ...emptyDraft })}
        >
          <FilePlus2 size={16} /> نوع تقرير جديد
        </button>
      </div>
      {error && <div className="admin-inline-alert">{error}</div>}
      <div className="admin-template-grid">
        {items.map((item) => (
          <article key={item.id}>
            <div className="admin-template-icon"><FileText size={20} /></div>
            <div className="admin-template-info">
              <div><h4>{item.name}</h4><StatusBadge active={item.is_active} /></div>
              <p>{item.description || 'لا يوجد وصف لهذا النوع.'}</p>
              <small>
                {item.fields_schema.length} حقول · {item.versions_count} نسخ ·{' '}
                {item.reports_count} تقارير
              </small>
            </div>
            <div className="admin-template-actions">
              <button type="button" onClick={() => selectVersions(item.id)}>
                <FileCheck2 size={15} /> النسخ
              </button>
              <button type="button" onClick={() => edit(item)}>
                <Pencil size={15} /> تعديل
              </button>
              <button
                type="button"
                className={item.is_active ? 'danger' : ''}
                onClick={() => toggle(item)}
              >
                <Power size={15} /> {item.is_active ? 'تعطيل النوع' : 'تفعيل النوع'}
              </button>
            </div>

            {selectedId === item.id && (
              <div className="admin-template-info">
                <form onSubmit={upload}>
                  <label>
                    رفع نسخة DOCX جديدة
                    <input
                      type="file"
                      accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                      onChange={(event) => setUploadFile(event.target.files?.[0] || null)}
                      required
                    />
                  </label>
                  <button
                    className="admin-primary-button"
                    type="submit"
                    disabled={saving || !uploadFile}
                  >
                    <Upload size={15} /> رفع كمسودة
                  </button>
                </form>
                {versions.map((version) => (
                  <div className="admin-template-actions" key={version.id}>
                    <strong>v{version.version} — {statusLabels[version.status]}</strong>
                    {version.checksum && <small dir="ltr">{version.checksum.slice(0, 12)}…</small>}
                    {version.status === 'draft' && (
                      <button
                        type="button"
                        disabled={busyVersion === version.id}
                        onClick={() => lifecycle(version, 'validate', 'التحقق من')}
                      >
                        <FileCheck2 size={15} /> تحقق
                      </button>
                    )}
                    {['validated', 'inactive'].includes(version.status) && (
                      <button
                        type="button"
                        disabled={busyVersion === version.id}
                        onClick={() => lifecycle(version, 'activate', 'تفعيل')}
                      >
                        <Power size={15} /> تفعيل
                      </button>
                    )}
                    {version.status === 'active' && (
                      <button
                        className="danger"
                        type="button"
                        disabled={busyVersion === version.id}
                        onClick={() => lifecycle(version, 'deactivate', 'تعطيل')}
                      >
                        <Power size={15} /> تعطيل
                      </button>
                    )}
                    {!['active', 'archived'].includes(version.status) && (
                      <button
                        className="danger"
                        type="button"
                        disabled={busyVersion === version.id}
                        onClick={() => lifecycle(version, 'archive', 'أرشفة')}
                      >
                        <Archive size={15} /> أرشفة
                      </button>
                    )}
                  </div>
                ))}
                {!versions.length && <p className="admin-muted">لا توجد نسخ مرفوعة بعد.</p>}
              </div>
            )}
          </article>
        ))}
        {!loading && !items.length && <p className="admin-muted">لا توجد أنواع تقارير.</p>}
        {loading && <div className="admin-loading">جارٍ تحميل القوالب...</div>}
      </div>

      {draft && (
        <div className="admin-modal-backdrop" role="presentation" onMouseDown={() => setDraft(null)}>
          <form
            className="admin-modal admin-template-modal"
            onSubmit={save}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <h3>{draft.id ? 'تعديل نوع التقرير' : 'إنشاء نوع تقرير'}</h3>
            <div className="admin-modal-form-grid">
              <label>
                الاسم
                <input
                  value={draft.name}
                  onChange={(event) => setDraft({ ...draft, name: event.target.value })}
                  required
                />
              </label>
              <label>
                المعرّف Slug
                <input
                  dir="ltr"
                  value={draft.slug}
                  onChange={(event) => setDraft({ ...draft, slug: event.target.value })}
                  required
                />
              </label>
              <label className="wide">
                الوصف
                <textarea
                  rows={3}
                  value={draft.description}
                  onChange={(event) => setDraft({ ...draft, description: event.target.value })}
                />
              </label>
              <label className="wide">
                مخطط الحقول JSON
                <textarea
                  className="admin-code-input"
                  rows={10}
                  value={draft.fields_schema}
                  onChange={(event) => setDraft({ ...draft, fields_schema: event.target.value })}
                  required
                />
              </label>
              <label className="admin-check wide">
                <input
                  type="checkbox"
                  checked={draft.is_active}
                  onChange={(event) => setDraft({ ...draft, is_active: event.target.checked })}
                />
                نوع التقرير متاح للمستخدمين
              </label>
            </div>
            <div className="admin-modal-actions">
              <button className="admin-secondary-button" type="button" onClick={() => setDraft(null)}>
                إلغاء
              </button>
              <button className="admin-primary-button" type="submit" disabled={saving}>
                حفظ
              </button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
