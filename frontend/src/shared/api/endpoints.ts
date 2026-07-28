const item = (collection: string, id: string | number) => `${collection}${id}/`;

export const API_ENDPOINTS = {
  auth: {
    login: '/auth/login/',
    register: '/auth/register/',
    refresh: '/auth/refresh/',
    logout: '/auth/logout/',
    me: '/auth/me/',
  },
  dashboard: {
    stats: '/dashboard/stats/',
  },
  reportTypes: {
    list: '/report-types/',
  },
  reports: {
    list: '/reports/',
    detail: (id: string | number) => item('/reports/', id),
    status: (id: string | number) => `${item('/reports/', id)}status/`,
  },
  services: {
    list: '/services/',
    detail: (slug: string) => item('/services/', slug),
    launch: (slug: string) => `${item('/services/', slug)}launch/`,
  },
  excelContacts: {
    process: '/tools/excel-contacts/process/',
  },
  admin: {
    dashboard: '/admin/dashboard/',
    analytics: (days: number) => `/admin/analytics/?days=${days}`,
    auditLogs: '/admin/audit-logs/',
    jobs: '/admin/jobs/',
    jobAction: (id: number, action: string) => `/admin/jobs/${id}/${action}/`,
    services: '/admin/services/',
    service: (id: string | number) => item('/admin/services/', id),
    serviceAction: (id: string | number, action: string) =>
      `${item('/admin/services/', id)}${action}/`,
    users: '/admin/users/',
    user: (id: string | number) => item('/admin/users/', id),
    userAction: (id: string | number, action: string) =>
      `${item('/admin/users/', id)}${action}/`,
    userRestrictions: (id: string | number) =>
      `${item('/admin/users/', id)}restrictions/`,
    reportTypes: '/admin/report-types/',
    reportType: (id: string | number) => item('/admin/report-types/', id),
    templateVersions: (reportTypeId: string | number) =>
      `${item('/admin/report-types/', reportTypeId)}template-versions/`,
    templateVersionAction: (
      reportTypeId: string | number,
      versionId: string | number,
      action: string,
    ) =>
      `${item('/admin/report-types/', reportTypeId)}template-versions/${versionId}/${action}/`,
  },
} as const;
