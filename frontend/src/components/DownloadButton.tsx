'use client';

import { useState } from 'react';
import { downloadFile } from '@/shared/api/client';

export default function DownloadButton({
  url,
  filename,
  label,
  gold = false,
  small = false,
}: {
  url?: string | null;
  filename: string;
  label: string;
  gold?: boolean;
  small?: boolean;
}) {
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    if (!url) return;
    setLoading(true);
    try {
      await downloadFile(url, filename);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      type="button"
      className={`${small ? 'btn-small' : 'btn'}${gold ? ' gold' : ''}`}
      disabled={!url || loading}
      onClick={handleClick}
    >
      {loading ? 'جارٍ التحميل...' : label}
    </button>
  );
}
