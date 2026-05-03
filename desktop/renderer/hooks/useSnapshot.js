import { useState, useEffect, useRef } from "react";

const SNAPSHOT_ENDPOINTS = {
  launchControl: "/api/launch-control",
  paperHealth: "/api/paper-sessions-health",
  brokerHealth: "/api/broker-submissions-health",
  stepbitWorkspace: "/api/stepbit-workspace",
};

const MAX_CONSECUTIVE_ERRORS = 5;
const POLL_INTERVAL_MS = 30_000;

/**
 * Fetches snapshot data (paperHealth, brokerHealth, launchControl, stepbitWorkspace)
 * from the local API server when legacy has not already populated state.snapshot.
 *
 * Mirrors app-legacy.js::refreshSnapshot semantics: same endpoints, same Promise.allSettled
 * pattern (partial failures produce "degraded" not "error"), same snapshotStatus shape.
 *
 * Pass serverUrl=null to skip all fetching (when legacy has already hydrated state.snapshot).
 */
export function useSnapshot(serverUrl) {
  const [snapshot, setSnapshot] = useState(null);
  const [snapshotStatus, setSnapshotStatus] = useState({
    status: "waiting",
    error: null,
    source: "none",
    lastSuccessAt: null,
    consecutiveErrors: 0,
    refreshPaused: false,
  });
  const errCount = useRef(0);

  useEffect(() => {
    if (!serverUrl) return;

    let cancelled = false;

    async function refresh() {
      const results = await Promise.allSettled(
        Object.values(SNAPSHOT_ENDPOINTS).map((path) =>
          window.quantlabDesktop.requestJson(path)
        )
      );
      if (cancelled) return;

      const [launchControl, paperHealth, brokerHealth, stepbitWorkspace] = results.map(
        (r) => (r.status === "fulfilled" ? r.value : null)
      );
      const rejected = results.filter((r) => r.status === "rejected");
      errCount.current = rejected.length ? errCount.current + 1 : 0;

      setSnapshot({ launchControl, paperHealth, brokerHealth, stepbitWorkspace });
      setSnapshotStatus({
        status: rejected.length ? "degraded" : "ok",
        error: rejected.length ? (rejected[0].reason?.message ?? null) : null,
        source: "native",
        lastSuccessAt: new Date().toISOString(),
        consecutiveErrors: errCount.current,
        refreshPaused: errCount.current >= MAX_CONSECUTIVE_ERRORS,
      });
    }

    refresh();
    const timer = window.setInterval(refresh, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [serverUrl]);

  return { snapshot, snapshotStatus };
}
