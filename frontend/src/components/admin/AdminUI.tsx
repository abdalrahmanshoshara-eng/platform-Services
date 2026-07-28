import Link from 'next/link';
import type { ReactNode } from 'react';

export function AdminHeader({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="admin-page-header">
      <div><h2>{title}</h2><p>{description}</p></div>
      {action}
    </div>
  );
}

export function StatusBadge({ active, label }: { active: boolean; label?: string }) {
  return <span className={`admin-status ${active ? 'active' : 'inactive'}`}>{label || (active ? 'نشط' : 'معطل')}</span>;
}

export function AdminEmpty({ message }: { message: string }) {
  return <div className="admin-empty">{message}</div>;
}

export function Pagination({
  page,
  hasNext,
  hasPrevious,
  onChange,
}: {
  page: number;
  hasNext: boolean;
  hasPrevious: boolean;
  onChange: (page: number) => void;
}) {
  return (
    <div className="admin-pagination">
      <button type="button" disabled={!hasPrevious} onClick={() => onChange(page - 1)}>السابق</button>
      <span>الصفحة {page}</span>
      <button type="button" disabled={!hasNext} onClick={() => onChange(page + 1)}>التالي</button>
    </div>
  );
}

export function DetailLink({ href, children }: { href: string; children: ReactNode }) {
  return <Link className="admin-detail-link" href={href}>{children}</Link>;
}
