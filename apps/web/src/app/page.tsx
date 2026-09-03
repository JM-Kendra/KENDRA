import { internalHealthEndpoint } from "@/lib/config";

import { HealthPanel, type HealthResponse } from "./HealthPanel";

// Fetched server-side (container-to-container) so release_tag is present in
// the initial server-rendered HTML -- e.g. for a plain `curl`, which never
// runs client-side JS -- not only after the browser hydrates and refetches.
async function fetchInitialHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch(internalHealthEndpoint(), { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as HealthResponse;
  } catch {
    return null;
  }
}

export default async function Home() {
  const initialHealth = await fetchInitialHealth();
  const productLabel = initialHealth?.release_tag
    ? `Kendra ${initialHealth.release_tag}`
    : "Kendra";

  return (
    <main>
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">{productLabel} · Local foundation</p>
        <h1 id="page-title">Kendra service readiness</h1>
        <p className="lede">
          This local scaffold checks its required services without exposing connection
          details or secrets.
        </p>
      </section>

      <HealthPanel initialHealth={initialHealth} />

      <aside className="boundary" aria-label="Milestone scope">
        <h2>Foundation only</h2>
        <p>
          Document ingestion and question answering are intentionally not implemented.
          Use only the approved public evaluation sample on a controlled workstation.
        </p>
      </aside>
    </main>
  );
}
