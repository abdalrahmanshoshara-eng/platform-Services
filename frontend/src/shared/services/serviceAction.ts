import type { PlatformService, UserSummary } from '@/shared/api/types';

export type ServiceAction = 'login' | 'launch' | 'unavailable';

export function serviceActionFor(
  user: UserSummary | null,
  service: PlatformService,
): ServiceAction {
  if (!user) return 'login';
  return service.is_available ? 'launch' : 'unavailable';
}

export function serviceActionLabel(
  action: ServiceAction,
  isLaunching: boolean,
): string {
  if (isLaunching) return 'جارٍ فتح الخدمة...';
  if (action === 'login') return 'سجّل الدخول للاستخدام';
  if (action === 'unavailable') return 'غير متاحة لحسابك';
  return 'استخدم الخدمة';
}
