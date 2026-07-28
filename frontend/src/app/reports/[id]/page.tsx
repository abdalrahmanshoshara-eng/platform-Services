'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import DownloadButton from '@/components/DownloadButton';
import PageHero from '@/components/PageHero';
import StatusBadge from '@/components/StatusBadge';
import { apiFetch as fetchApi } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';
import type { GeneratedReport } from '@/shared/api/types';
import { useRequireAuth } from '@/shared/auth/useRequireAuth';

export default function ReportDetailPage() {
  const ready = useRequireAuth();
  const params = useParams<{ id: string }>();
  const [report, setReport] = useState<GeneratedReport | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!ready || !params.id) return;
    fetchApi<GeneratedReport>(API_ENDPOINTS.reports.detail(params.id))
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : 'تعذر تحميل التقرير.'));
  }, [ready, params.id]);

  const inputRows = useMemo(() => {
    if (!report) return [];
    return report.report_type.fields_schema.map((field) => ({
      label: field.label_ar,
      value: report.input_data[field.name] || '-',
    }));
  }, [report]);

  if (!ready) return <main className="container"><div className="card">جارٍ التحقق من تسجيل الدخول...</div></main>;

  return (
    <main className="container">
      <PageHero title="تفاصيل التقرير" description="عرض حالة التوليد والبيانات المدخلة وروابط التحميل." />
      {error && <div className="alert danger">{error}</div>}
      {!report ? <section className="card">جارٍ تحميل التقرير...</section> : (
        <>
          <section className="card">
            <div className="section-head inline-head">
              <h2>{report.title}</h2>
              <StatusBadge status={report.status} />
            </div>
            <div className="details-grid">
              <div><span>نوع التقرير</span><strong>{report.report_type.name}</strong></div>
              <div><span>أنشئ بواسطة</span><strong>{report.created_by.username}</strong></div>
              <div><span>تاريخ الإنشاء</span><strong>{new Date(report.created_at).toLocaleString('ar')}</strong></div>
              <div><span>آخر تحديث</span><strong>{new Date(report.updated_at).toLocaleString('ar')}</strong></div>
            </div>
            {report.error_message && <div className="alert danger">{report.error_message}</div>}
            <div className="button-row compact-actions">
              <DownloadButton url={report.download_docx_url} filename={`${report.title}.docx`} label="تحميل Word" />
              <DownloadButton url={report.download_pdf_url} filename={`${report.title}.pdf`} label="تحميل PDF" gold />
              <Link className="btn secondary" href="/reports">العودة للسجل</Link>
            </div>
          </section>

          <section className="card">
            <h2>البيانات المدخلة</h2>
            <div className="table-wrap">
              <table className="compact-table">
                <thead><tr><th>الحقل</th><th>القيمة</th></tr></thead>
                <tbody>
                  {inputRows.map((row) => (
                    <tr key={row.label}>
                      <td className="primary-cell">{row.label}</td>
                      <td className="line-cell">{String(row.value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
