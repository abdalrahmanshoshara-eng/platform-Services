export default function PageHero({ title, description }: { title: string; description: string }) {
  return (
    <section className="hero">
    {/* <div className="header-overlay"/> */}
    <div className="header-overlay" aria-hidden="true"></div>
      <div className="hero-accent-line" />
      <h1>{title}</h1>
      <p>{description}</p>
    </section>
  );
}
