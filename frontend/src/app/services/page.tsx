'use client';

import { ContactRound, FileText, PanelsTopLeft, Sheet, type LucideIcon } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { abortRequest, apiFetch, isAbortError } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';
import type { PlatformService, ServiceLaunch } from '@/shared/api/types';
import { useRequireAuth } from '@/shared/auth/useRequireAuth';

const icons: Record<string, LucideIcon> = {
  'file-text': FileText,
  sheet: Sheet,
  contact: ContactRound,
  default: PanelsTopLeft,
};

export default function ServicesPage() {
  const router = useRouter();
  const ready = useRequireAuth();
  const [services, setServices] = useState<PlatformService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [launching, setLaunching] = useState('');

  useEffect(() => {
    if (!ready) return;
    const controller = new AbortController();
    apiFetch<PlatformService[]>(API_ENDPOINTS.services.list, { signal: controller.signal })
      .then((catalog) => {
        if (!controller.signal.aborted) setServices(catalog);
      })
      .catch((err) => {
        if (!isAbortError(err, controller.signal)) {
          setError(err instanceof Error ? err.message : 'تعذر تحميل الخدمات.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => abortRequest(controller);
  }, [ready]);

  const grouped = useMemo(() => {
    const groups = new Map<string, { name: string; description: string; services: PlatformService[] }>();
    for (const service of services) {
      const key = service.category.slug;
      const current = groups.get(key) || {
        name: service.category.name,
        description: service.category.description,
        services: [],
      };
      current.services.push(service);
      groups.set(key, current);
    }
    return Array.from(groups.entries());
  }, [services]);

  async function launch(service: PlatformService) {
    if (!service.is_available || launching) return;
    setLaunching(service.slug);
    setError('');
    try {
      const launchInfo = await apiFetch<ServiceLaunch>(API_ENDPOINTS.services.launch(service.slug), { method: 'POST' });
      if (launchInfo.kind === 'external') {
        window.open(launchInfo.target, '_blank', 'noopener,noreferrer');
      } else {
        router.push(launchInfo.target);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'تعذر فتح الخدمة.');
    } finally {
      setLaunching('');
    }
  }

  if (!ready) return <div className="page-loading">جارٍ تجهيز الخدمات...</div>;

  return (
    <main className="portal-main services-page">
      <section className="portal-intro">
        <div>
          <span className="portal-kicker">كتالوج الخدمات</span>
          <h1>كل أدواتك في مكان واحد</h1>
          <p>اختر الخدمة المطلوبة وابدأ العمل مباشرة ضمن صلاحيات حسابك.</p>
        </div>
        <div className="availability-summary">
          <strong>{services.filter((service) => service.is_available).length}</strong>
          <span>خدمات متاحة</span>
        </div>
      </section>

      {error && <div className="alert danger">{error}</div>}

      {loading ? (
        <section className="services-skeleton" aria-label="جارٍ تحميل الخدمات"><span /><span /><span /></section>
      ) : grouped.length ? grouped.map(([slug, group]) => (
        <section className="service-band" key={slug}>
          <div className="band-heading">
            <div><h2>{group.name}</h2><p>{group.description}</p></div>
            <span>{group.services.length} خدمات</span>
          </div>
          <div className="service-grid">
            {group.services.map((service) => {
              const Icon = icons[service.icon] || icons.default;
              return (
                <article className={`service-card accent-${service.accent} ${service.is_available ? '' : 'is-locked'}`} key={service.id}>
                  <div className="service-card-top">
                    <span className="service-glyph" aria-hidden="true"><Icon size={21} /></span>
                    <span className={`service-kind ${service.kind}`}>{service.kind === 'external' ? 'منصة خارجية' : 'ضمن البوابة'}</span>
                  </div>
                  <div><h3>{service.name}</h3><p>{service.description}</p></div>
                  <div className="service-card-footer">
                    <span className={`availability-dot ${service.is_available ? 'available' : ''}`}>
                      {service.is_available ? 'متاحة الآن' : service.restriction_reason}
                    </span>
                    <button type="button" className="service-launch" onClick={() => launch(service)} disabled={!service.is_available || launching === service.slug}>
                      {launching === service.slug ? 'جارٍ الفتح...' : 'فتح الخدمة'}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      )) : <section className="portal-empty">لا توجد خدمات مفعلة حالياً.</section>}
    </main>
  );
}
