import type { Metadata } from 'next';
import AppChrome from '@/components/AppChrome';
import { AuthProvider } from '@/shared/auth/AuthContext';
import './globals.css';

export const metadata: Metadata = {
  title: 'بوابة الخدمات الرقمية',
  description: 'بوابة موحدة للوصول إلى الخدمات والأدوات الرقمية.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <AuthProvider>
          <AppChrome>{children}</AppChrome>
        </AuthProvider>
      </body>
    </html>
  );
}
