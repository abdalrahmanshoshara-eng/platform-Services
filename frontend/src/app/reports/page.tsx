'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import DownloadButton from '@/components/DownloadButton';
import PageHero from '@/components/PageHero';
import StatusBadge from '@/components/StatusBadge';
import { GeneratedReport, PaginatedResponse, fetchApi } from '@/lib/api';
import { useRequireAuth } from '@/lib/useRequireAuth';

export default function ReportsPage() {
  const ready = useRequireAuth();
  const [reports, setReports] = useState<GeneratedReport[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!ready) return;
    fetchApi<PaginatedResponse<GeneratedReport> | GeneratedReport[]>('/reports/')
      .then((data) => setReports(Array.isArray(data) ? data : data.results))
      .catch((err) => setError(err instanceof Error ? err.message : 'تعذر تحميل سجل التقارير.'));
  }, [ready]);

  if (!ready) return <main className="container"><div className="card">جارٍ التحقق من تسجيل الدخول...</div></main>;

  return (
    <main className="container">
      <PageHero title="سجل التقارير" description="استعرض التقارير السابقة وحمّل ملفات Word و PDF عند الحاجة." />
      {error && <div className="alert danger">{error}</div>}

      <section className="card">
        <div className="section-head inline-head">
          <h2>التقارير</h2>
          <Link className="btn gold" href="/reports/new">إنشاء تقرير جديد</Link>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>نوع التقرير</th>
                <th>العنوان</th>
                <th>المستخدم</th>
                <th>تاريخ الإنشاء</th>
                <th>الحالة</th>
                <th>Word</th>
                <th>PDF</th>
                <th>التفاصيل</th>
              </tr>
            </thead>
            <tbody>
              {reports.length ? reports.map((report) => (
                <tr key={report.id}>
                  <td>{report.report_type.name}</td>
                  <td className="primary-cell">{report.title}</td>
                  <td>{report.created_by.username}</td>
                  <td>{new Date(report.created_at).toLocaleString('ar')}</td>
                  <td><StatusBadge status={report.status} /></td>
                  <td><DownloadButton url={report.download_docx_url} filename={`${report.title}.docx`} label="Word" small /></td>
                  <td><DownloadButton url={report.download_pdf_url} filename={`${report.title}.pdf`} label="PDF" small gold /></td>
                  <td><Link className="btn-small" href={`/reports/${report.id}`}>فتح</Link></td>
                </tr>
              )) : (
                <tr><td className="empty-cell" colSpan={8}>لا توجد تقارير محفوظة.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
