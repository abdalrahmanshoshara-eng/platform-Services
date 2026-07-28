'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import DownloadButton from '@/components/DownloadButton';
import PageHero from '@/components/PageHero';
import StatusBadge from '@/components/StatusBadge';
import { useRequireAuth } from '@/shared/auth/useRequireAuth';
import { useReportTypes } from '@/features/report-catalog/useReportTypes';
import { useCreateReport, validateInput } from '@/features/report-generation/useCreateReport';
import { useReportStatus } from '@/features/report-generation/useReportStatus';
import type { FieldSchema, GeneratedReport } from '@/shared/api/types';

export default function NewReportPage() {
  const ready = useRequireAuth();
  const { reportTypes, error: typesError } = useReportTypes(ready);
  const { create, submitting, error: submitError, fieldErrors } = useCreateReport();

  const [selectedTypeId, setSelectedTypeId] = useState('');
  const [title, setTitle] = useState('');
  const [inputData, setInputData] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [created, setCreated] = useState<GeneratedReport | null>(null);

  const { state: polled } = useReportStatus(created?.id ?? null, created?.status);
  const status = polled?.status ?? created?.status;
  const docxUrl = polled?.download_docx_url ?? created?.download_docx_url ?? null;
  const pdfUrl = polled?.download_pdf_url ?? created?.download_pdf_url ?? null;

  useEffect(() => {
    if (reportTypes.length && !selectedTypeId) {
      const requested = typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('type') : null;
      const match = requested ? reportTypes.find((t) => String(t.id) === requested) : null;
      setSelectedTypeId(String((match || reportTypes[0]).id));
    }
  }, [reportTypes, selectedTypeId]);

  const selectedType = useMemo(
    () => reportTypes.find((t) => String(t.id) === selectedTypeId) || null,
    [reportTypes, selectedTypeId],
  );

  useEffect(() => {
    if (!selectedType) return;
    const initial: Record<string, string> = {};
    selectedType.fields_schema.forEach((f) => (initial[f.name] = ''));
    setInputData(initial);
    setErrors({});
    setCreated(null);
  }, [selectedTypeId]); // eslint-disable-line react-hooks/exhaustive-deps

  function updateField(name: string, value: string) {
    setInputData((cur) => ({ ...cur, [name]: value }));
    setErrors((cur) => ({ ...cur, [name]: '' }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!selectedType) return;
    const clientErrors = validateInput(selectedType.fields_schema, inputData);
    if (Object.keys(clientErrors).length) {
      setErrors(clientErrors);
      return;
    }
    const report = await create(selectedType.id, title || selectedType.name, inputData);
    if (report) setCreated(report);
  }

  if (!ready) return <main className="container"><div className="card">جارٍ التحقق من تسجيل الدخول...</div></main>;

  const isGenerating = status === 'pending' || status === 'queued' || status === 'processing';

  return (
    <main className="container">
      <PageHero title="إنشاء تقرير جديد" description="اختر نوع التقرير، املأ الحقول، ثم يتم توليد الملفات في الخلفية." />
      {typesError && <div className="alert danger">{typesError}</div>}

      <form className="card" onSubmit={handleSubmit}>
        <h2>بيانات التقرير</h2>
        <div className="grid">
          <label>
            نوع التقرير
            <select value={selectedTypeId} onChange={(e) => setSelectedTypeId(e.target.value)} required>
              {reportTypes.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </label>
          <label>
            عنوان التقرير
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="اختياري - سيتم استخدام اسم النوع عند تركه فارغاً" />
          </label>
        </div>

        {selectedType && <p className="helper-text">{selectedType.description}</p>}
        <div className="divider" />

        <div className="grid">
          {selectedType?.fields_schema.map((field) => (
            <FieldInput
              key={field.name}
              field={field}
              value={inputData[field.name] || ''}
              error={errors[field.name] || fieldErrors[field.name]}
              onChange={(v) => updateField(field.name, v)}
            />
          ))}
        </div>

        <div className="button-row compact-actions">
          <button className="gold" type="submit" disabled={submitting}>{submitting ? 'جارٍ الإرسال...' : 'إنشاء التقرير'}</button>
          <Link className="btn secondary" href="/reports">العودة للسجل</Link>
        </div>
      </form>

      {created && (
        <section className="card result-card">
          <h2>حالة التوليد</h2>
          <p><strong>الحالة:</strong> {status && <StatusBadge status={status} />}</p>
          {isGenerating && <p className="helper-text">يتم توليد الملفات في الخلفية… يتم التحديث تلقائياً.</p>}
          {submitError && <div className="alert danger">{submitError}</div>}
          {status === 'failed' && <div className="alert danger">{polled?.error_message || 'فشل توليد التقرير.'}</div>}
          {status === 'completed' && (
            <div className="button-row compact-actions">
              <DownloadButton url={docxUrl} filename={`${created.title}.docx`} label="تحميل Word" />
              <DownloadButton url={pdfUrl} filename={`${created.title}.pdf`} label="تحميل PDF" gold />
              <Link className="btn secondary" href={`/reports/${created.id}`}>فتح تفاصيل التقرير</Link>
            </div>
          )}
        </section>
      )}
    </main>
  );
}

function FieldInput({ field, value, error, onChange }: { field: FieldSchema; value: string; error?: string; onChange: (value: string) => void }) {
  const label = `${field.label_ar}${field.required ? ' *' : ''}`;
  const className = field.type === 'textarea' ? 'full-width' : '';
  return (
    <label className={className}>
      {label}
      {field.type === 'textarea' ? (
        <textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder={field.placeholder || ''} />
      ) : field.type === 'select' ? (
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          <option value="">اختر...</option>
          {(field.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      ) : (
        <input type={field.type === 'date' ? 'date' : field.type === 'number' ? 'number' : 'text'} value={value} onChange={(e) => onChange(e.target.value)} placeholder={field.placeholder || ''} />
      )}
      {error && <span className="field-error">{error}</span>}
    </label>
  );
}
