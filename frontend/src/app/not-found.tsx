import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="page-loading">
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, textAlign: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 44 }}>404</h2>
          <p style={{ color: 'var(--text-muted)' }}>الصفحة التي تبحث عنها غير موجودة.</p>
        </div>
        <Link className="btn" href="/">العودة إلى الرئيسية</Link>
      </div>
    </main>
  );
}
