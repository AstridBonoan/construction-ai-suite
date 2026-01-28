import { useEffect, useState, useRef } from "react";

export default function ProjectDelay() {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const latestRequestRef = useRef(0);

  // Prefer explicit env var (used in Docker). If missing, use relative path
  // so a Vite dev proxy can forward to the backend on localhost.
  const VITE_API_URL = import.meta.env.VITE_API_URL;
  // During development, prefer the Vite dev-server proxy (relative path).
  // In production or when VITE_API_URL is explicitly set for runtime, use that.
  const isDev = import.meta.env.DEV;
  const apiBase = VITE_API_URL ? VITE_API_URL.replace(/\/+$/, "") : "";
  const endpoint = isDev ? "/project-delay" : (apiBase ? `${apiBase}/project-delay` : "/project-delay");

  useEffect(() => {
    const controller = new AbortController();
    const timeoutMs = 20000; // increased timeout to reduce spurious aborts
    const reqId = latestRequestRef.current + 1;
    latestRequestRef.current = reqId;

    const fetchWithTimeout = async () => {
      // mark start of this request
      if (latestRequestRef.current !== reqId) return;
      setLoading(true);
      setError("");
      setMessage("");
      console.log("[ProjectDelay] Request endpoint:", endpoint, "(reqId:", reqId, ")");

      const timeout = setTimeout(() => {
        controller.abort();
      }, timeoutMs);

      try {
        const res = await fetch(endpoint, {
          method: "GET",
          signal: controller.signal,
          headers: { "Content-Type": "application/json" },
        });

        clearTimeout(timeout);

        console.log("[ProjectDelay] HTTP status:", res.status, "(reqId:", reqId, ")");

        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new Error(`Backend error ${res.status} ${text}`);
        }

        const data = await res.json();
        console.log("[ProjectDelay] Response data:", data, "(reqId:", reqId, ")");

        // Only update state for the latest request
        if (latestRequestRef.current === reqId) {
          setMessage(data?.message ?? JSON.stringify(data));
          setError("");
        }
      } catch (err) {
        if (err.name === "AbortError") {
          // Aborted request (often due to StrictMode dev re-mount); ignore silently.
          console.debug("[ProjectDelay] Request aborted / timed out (reqId:", reqId, ")");
          // don't set an error for aborted/stale requests
        } else {
          console.error("[ProjectDelay] Fetch error:", err, "(reqId:", reqId, ")");
          if (latestRequestRef.current === reqId) {
            setError("Could not connect to backend — " + (err.message || "unknown error"));
          }
        }
      } finally {
        if (latestRequestRef.current === reqId) {
          setLoading(false);
        }
      }
    };

    fetchWithTimeout();

    return () => {
      // invalidate this request and abort
      latestRequestRef.current += 1;
      controller.abort();
    };
  }, [endpoint]);

  return (
    <div>
      <h2>Project Delay Prediction</h2>

      {loading && <p>Loading prediction...</p>}

      {!loading && message && <p>{message}</p>}

      {!loading && error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
