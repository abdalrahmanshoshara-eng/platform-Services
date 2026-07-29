'use client';

import {
  ArrowLeft,
  ContactRound,
  FileText,
  LockKeyhole,
  PanelsTopLeft,
  Sheet,
  Sparkles,
  type LucideIcon,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { abortRequest, apiFetch, isAbortError } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';
import type { PlatformService, ServiceLaunch } from '@/shared/api/types';
import { useAuth } from '@/shared/auth/AuthContext';
import {
  serviceActionFor,
  serviceActionLabel,
} from '@/shared/services/serviceAction';

const icons: Record<string, LucideIcon> = {
  'file-text': FileText,
  sheet: Sheet,
  contact: ContactRound,
  default: PanelsTopLeft,
};

export default function ServiceCatalog({ compact = false }: { compact?: boolean }) {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [services, setServices] = useState<PlatformService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [launching, setLaunching] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    apiFetch<PlatformService[]>(API_ENDPOINTS.services.list, { signal: controller.signal })
      .then((catalog) => {
        if (!controller.signal.aborted) setServices(catalog);
      })
      .catch((err) => {
        if (!isAbortError(err, controller.signal)) {
          setError(err instanceof Error ? err.message : 'تعذّر تحميل الخدمات حالياً.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => abortRequest(controller);
  }, [user]);

  const grouped = useMemo(() => {
    const groups = new Map<string, {
      name: string;
      description: string;
      services: PlatformService[];
    }>();
    for (const service of services) {
      const current = groups.get(service.category.slug) ?? {
        name: service.category.name,
        description: service.category.description,
        services: [],
      };
      current.services.push(service);
      groups.set(service.category.slug, current);
    }
    return Array.from(groups.entries());
  }, [services]);

  async function handleServiceAction(service: PlatformService) {
    const action = serviceActionFor(user, service);
    if (action === 'login') {
      router.push('/login');
      return;
    }
    if (action !== 'launch' || launching) return;

    setLaunching(service.slug);
    setError('');
    try {
      const launchInfo = await apiFetch<ServiceLaunch>(
        API_ENDPOINTS.services.launch(service.slug),
        { method: 'POST' },
      );
      if (launchInfo.kind === 'external') {
        window.open(launchInfo.target, '_blank', 'noopener,noreferrer');
      } else {
        router.push(launchInfo.target);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'تعذّر فتح الخدمة.');
    } finally {
      setLaunching('');
    }
  }

  return (
    <div className={`public-catalog ${compact ? 'is-compact' : ''}`}>
      {error && <div className="public-alert" role="alert">{error}</div>}

      {loading ? (
        <div className="public-services-skeleton" aria-label="جارٍ تحميل الخدمات">
          <span /><span /><span />
        </div>
      ) : grouped.length ? grouped.map(([slug, group]) => (
        <section className="public-service-group" key={slug} aria-labelledby={`category-${slug}`}>
          <header className="public-group-heading">
            <div>
              <span>مجموعة خدمات</span>
              <h3 id={`category-${slug}`}>{group.name}</h3>
              {group.description && <p>{group.description}</p>}
            </div>
            <strong>{group.services.length.toLocaleString('ar-SY')}</strong>
          </header>

          <div className="public-service-grid">
            {group.services.map((service) => {
              const Icon = icons[service.icon] ?? icons.default;
              const action = serviceActionFor(user, service);
              const isLaunching = launching === service.slug;
              return (
                <article
                  className={`public-service-card accent-${service.accent}`}
                  key={service.id}
                >
                  <div className="public-service-topline">
                    <span className="public-service-icon" aria-hidden="true">
                      <Icon size={24} />
                    </span>
                    <span className="public-service-kind">
                      {service.kind === 'external' ? 'خدمة خارجية موثوقة' : 'داخل المنصّة'}
                    </span>
                  </div>
                  <div className="public-service-copy">
                    <h4>{service.name}</h4>
                    <p>{service.description}</p>
                  </div>
                  <div className="public-service-status">
                    {action === 'login' ? (
                      <span><LockKeyhole size={14} /> يتطلب حساباً للاستخدام</span>
                    ) : action === 'launch' ? (
                      <span className="is-ready"><Sparkles size={14} /> متاحة لحسابك</span>
                    ) : (
                      <span><LockKeyhole size={14} /> {service.restriction_reason}</span>
                    )}
                  </div>
                  <button
                    type="button"
                    className="public-service-action"
                    onClick={() => handleServiceAction(service)}
                    disabled={authLoading || action === 'unavailable' || isLaunching}
                  >
                    <span>{serviceActionLabel(action, isLaunching)}</span>
                    {action !== 'unavailable' && <ArrowLeft size={17} aria-hidden="true" />}
                  </button>
                </article>
              );
            })}
          </div>
        </section>
      )) : (
        <div className="public-empty">لا توجد خدمات منشورة حالياً.</div>
      )}
    </div>
  );
}
