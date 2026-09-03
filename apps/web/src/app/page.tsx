"use client";

import { useCallback, useEffect, useState } from "react";

import { healthEndpoint } from "@/lib/config";

type ServiceState = {
  status: "ready" | "not_ready";
  code: "reachable" | "unreachable" | "available" | "unavailable";
};

type HealthResponse = {
  status: "ready" | "not_ready";
  services: Record<string, ServiceState>;
  release_tag?: string;
};

type ViewState =
  | { kind: "loading" }
  | { kind: "loaded"; health: HealthResponse }
  | { kind: "error" };

const serviceLabels: Record<string, string> = {
  postgres: "PostgreSQL",
  qdrant: "Qdrant",
  ollama: "Ollama",
  document_store: "Document store",
};

export default function Home() {
  const [view, setView] = useState<ViewState>({ kind: "loading" });

  const refresh = useCallback(async () => {
    setView({ kind: "loading" });
    try {
      const response = await fetch(
        healthEndpoint(process.env.NEXT_PUBLIC_KENDRA_API_BASE_URL),
        { cache: "no-store" },
      );
      const health = (await response.json()) as HealthResponse;
      setView({ kind: "loaded", health });
    } catch {
      setView({ kind: "error" });
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const productLabel =
    view.kind === "loaded" && view.health.release_tag
      ? `Kendra ${view.health.release_tag}`
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

      <section className="panel" aria-live="polite">
        <div className="panel-heading">
          <div>
            <p className="label">System state</p>
            <h2>
              {view.kind === "loading" && "Checking…"}
              {view.kind === "error" && "API unavailable"}
              {view.kind === "loaded" &&
                (view.health.status === "ready" ? "Ready" : "Not ready")}
            </h2>
          </div>
          <button type="button" onClick={() => void refresh()}>
            Check again
          </button>
        </div>

        {view.kind === "loaded" && (
          <ul className="services">
            {Object.entries(view.health.services).map(([name, service]) => (
              <li key={name}>
                <span>{serviceLabels[name] || name}</span>
                <strong data-ready={service.status === "ready"}>
                  {service.status === "ready" ? "Ready" : "Unavailable"}
                </strong>
              </li>
            ))}
          </ul>
        )}

        {view.kind === "error" && (
          <p className="notice">
            Confirm the API is running on the configured loopback URL, then try again.
          </p>
        )}
      </section>

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
