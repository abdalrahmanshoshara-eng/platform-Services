'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import PageHero from '@/components/PageHero';
import { apiFetch as fetchApi } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';
import type { ReportType } from '@/shared/api/types';
import { useRequireAuth } from '@/shared/auth/useRequireAuth';

export default function ReportTypesPage() {
  const ready = useRequireAuth();
  const [items, setItems] = useState<ReportType[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!ready) return;
    fetchApi<ReportType[]>(API_ENDPOINTS.reportTypes.list)
      .then(setItems)
      .catch((err) => setError(err instanceof Error ? err.message : 'تعذر تحميل أنواع التقارير.'));
  }, [ready]);

  if (!ready) return <main className="container"><div className="card">جارٍ التحقق من تسجيل الدخول...</div></main>;

  return (
    <main className="container">
      <PageHero title="أنواع التقارير" description="قوالب المرحلة الأولى مع الحقول المعرفة لكل نوع تقرير." />
      {error && <div className="alert danger">{error}</div>}
      <section className="type-grid">
        {items.map((item) => (
          <article className="card type-card" key={item.id}>
            <h2>{item.name}</h2>
            <p className="helper-text">{item.description}</p>
            <div className="field-chip-list">
              {item.fields_schema.map((field) => <span className="field-chip" key={field.name}>{field.label_ar}</span>)}
            </div>
            <div className="button-row compact-actions">
              <Link className="btn gold" href={`/reports/new?type=${item.id}`}>استخدام القالب</Link>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
