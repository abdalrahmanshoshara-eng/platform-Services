const labels: Record<string, string> = {
  pending: 'قيد الانتظار',
  processing: 'جارٍ التوليد',
  completed: 'مكتمل',
  failed: 'فشل',
};

export default function StatusBadge({ status }: { status: string }) {
  const className = status === 'completed' ? 'success' : status === 'failed' ? 'danger' : 'warning';
  return <span className={`badge ${className}`}>{labels[status] || status}</span>;
}
