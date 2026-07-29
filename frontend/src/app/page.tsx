import {
  ArrowLeft,
  BadgeCheck,
  FileCheck2,
  FileInput,
  ShieldCheck,
  WandSparkles,
} from 'lucide-react';
import Link from 'next/link';
import ServiceCatalog from '@/components/public/ServiceCatalog';

export default function HomePage() {
  return (
    <main className="public-main">
      <section className="public-hero" id="about">
        <div className="public-hero-copy">
          <span className="public-eyebrow">
            <BadgeCheck size={16} /> منصّة أعمال رقمية موحّدة
          </span>
          <h1>من الفكرة إلى مستند جاهز، <em>بخطوات واضحة.</em></h1>
          <p>
            اجمع خدمات التقارير ومعالجة ملفات العمل في مكان واحد. تعرّف إلى كل خدمة
            قبل تسجيل الدخول، ثم ابدأ العمل بحسابك عندما تكون مستعداً.
          </p>
          <div className="public-hero-actions">
            <Link className="public-primary-cta" href="#services">
              <span>استعرض الخدمات</span>
              <ArrowLeft size={18} aria-hidden="true" />
            </Link>
            <Link className="public-secondary-cta" href="/login">لديّ حساب</Link>
          </div>
          <div className="public-trust-row">
            <span><ShieldCheck size={17} /> وصول محمي حسب الصلاحيات</span>
            <span><FileCheck2 size={17} /> ملفات جاهزة للتنزيل</span>
          </div>
        </div>

        <div className="document-journey" aria-label="رحلة إنشاء المستند">
          <div className="journey-heading">
            <span>رحلة العمل</span>
            <strong>من بياناتك إلى نتيجة احترافية</strong>
          </div>
          <div className="journey-track" aria-hidden="true">
            <article>
              <span><FileInput size={21} /></span>
              <div><small>المدخلات</small><strong>بيانات منظّمة</strong></div>
            </article>
            <i />
            <article>
              <span><WandSparkles size={21} /></span>
              <div><small>المعالجة</small><strong>قالب معتمد</strong></div>
            </article>
            <i />
            <article className="is-result">
              <span><FileCheck2 size={21} /></span>
              <div><small>النتيجة</small><strong>DOCX + PDF</strong></div>
            </article>
          </div>
          <div className="journey-paper">
            <span />
            <span />
            <span className="short" />
            <b>تمّ</b>
          </div>
        </div>
      </section>

      <section className="public-value-strip" aria-label="مزايا المنصة">
        <article><strong>مكان واحد</strong><span>لكل خدمات العمل المتاحة</span></article>
        <article><strong>صلاحيات واضحة</strong><span>كل حساب يرى ما يمكنه استخدامه</span></article>
        <article><strong>تنفيذ موثوق</strong><span>معالجة آمنة ونتائج قابلة للتنزيل</span></article>
      </section>

      <section className="public-services-section" id="services">
        <header className="public-section-heading">
          <div>
            <span className="public-eyebrow">دليل الخدمات</span>
            <h2>اختر ما تريد إنجازه</h2>
          </div>
          <p>
            الاستعراض متاح للجميع. عند اختيار خدمة سنطلب منك تسجيل الدخول لحماية
            ملفاتك وتطبيق صلاحيات حسابك.
          </p>
        </header>
        <ServiceCatalog compact />
      </section>

      <section className="public-how" id="how-it-works">
        <div className="public-section-heading">
          <div>
            <span className="public-eyebrow">طريقة العمل</span>
            <h2>ثلاث محطات، بلا تعقيد</h2>
          </div>
        </div>
        <div className="public-steps">
          <article><span>١</span><h3>استكشف</h3><p>اقرأ تعريف كل خدمة واختر الأنسب لمهمتك.</p></article>
          <article><span>٢</span><h3>ادخل بأمان</h3><p>سجّل الدخول لنطبّق صلاحيات حسابك ونحمي ملفاتك.</p></article>
          <article><span>٣</span><h3>أنجز ونزّل</h3><p>نفّذ الخدمة وتابع النتيجة من مساحة عملك.</p></article>
        </div>
      </section>

      <section className="public-final-cta">
        <div>
          <span>جاهز للبدء؟</span>
          <h2>حوّل أعمالك المتكررة إلى خطوات أسرع.</h2>
        </div>
        <Link href="/register">أنشئ حسابك <ArrowLeft size={18} /></Link>
      </section>
    </main>
  );
}
