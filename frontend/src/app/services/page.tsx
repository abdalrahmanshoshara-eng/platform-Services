import ServiceCatalog from '@/components/public/ServiceCatalog';

export default function ServicesPage() {
  return (
    <main className="public-main public-catalog-page">
      <section className="public-catalog-hero">
        <span className="public-eyebrow">دليل الخدمات</span>
        <h1>خدمات مصمّمة لتختصر العمل، لا لتزيده.</h1>
        <p>
          تصفّح جميع الخدمات دون حساب. تسجيل الدخول مطلوب فقط عندما تختار استخدام
          خدمة، حتى تبقى ملفاتك ونتائجك مرتبطة بك بأمان.
        </p>
      </section>
      <ServiceCatalog />
    </main>
  );
}
