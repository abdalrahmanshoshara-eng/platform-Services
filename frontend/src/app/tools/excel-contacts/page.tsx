'use client';

import Link from 'next/link';
import ContactProcessor from '@/components/ContactProcessor';
import { useRequireAuth } from '@/shared/auth/useRequireAuth';

export default function ExcelContactsPage() {
  const ready = useRequireAuth();

  if (!ready) {
    return <main className="portal-main"><div className="portal-loading">جارٍ التحقق من الصلاحية...</div></main>;
  }

  return (
    <main className="portal-main tool-page">
      <div className="tool-breadcrumb">
        <Link href="/dashboard">الخدمات</Link>
        <span>/</span>
        <span>تهيئة جهات الاتصال</span>
      </div>
      <header className="tool-heading">
        <span className="service-glyph accent-teal" aria-hidden="true">س</span>
        <div>
          <span className="portal-kicker">Excel إلى VCF</span>
          <h1>تهيئة جهات الاتصال</h1>
          <p>نظّف أرقام التواصل، ادمج المكررات، ثم نزّل ملف VCF وتقارير المراجعة في حزمة واحدة.</p>
        </div>
      </header>
      <ContactProcessor />
      <p className="privacy-note">تتم معالجة الملف في الذاكرة ولا تُحفظ جهات الاتصال داخل المنصة.</p>
    </main>
  );
}
