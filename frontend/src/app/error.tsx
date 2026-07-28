'use client';

import { useEffect } from 'react';

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log for diagnostics; the UI never exposes internal error detail.
    console.error(error);
  }, [error]);

  return (
    <main className="page-loading">
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, textAlign: 'center' }}>
        <div>
          <h2 style={{ margin: 0 }}>حدث خطأ غير متوقع</h2>
          <p style={{ color: 'var(--text-muted)' }}>تعذّر عرض هذه الصفحة. يمكنك إعادة المحاولة.</p>
        </div>
        <button className="btn" onClick={reset}>إعادة المحاولة</button>
      </div>
    </main>
  );
}
