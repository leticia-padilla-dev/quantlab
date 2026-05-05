import { useState, useEffect } from "react";
import { loadRunDetailNative } from "../modules/run-detail-loader.js";

const CACHE_MAX = 50;
const _cache = new Map();

/**
 * Lazily hydrates run detail via native IPC when legacy has not pre-populated
 * tab.detail. Mirrors the semantics of app-legacy.js::loadRunDetail exactly:
 * same artifact names, same detail shape, same optional directory listing,
 * same cache-only-when-report-present rule.
 *
 * Pass runId=null to skip loading (when tab.detail is already hydrated).
 */
export function useRunDetail(runId, run) {
  const [state, setState] = useState(() => {
    if (!runId) return { detail: null, status: "idle", error: null };
    const cached = _cache.get(runId);
    if (cached) return { detail: cached, status: "ready", error: null };
    if (!run?.path) return { detail: null, status: "missing", error: "run_path_unavailable" };
    return { detail: null, status: "loading", error: null };
  });

  useEffect(() => {
    if (!runId) return;
    if (!run?.path) {
      setState({ detail: null, status: "missing", error: "run_path_unavailable" });
      return;
    }
    if (_cache.has(runId)) {
      setState({ detail: _cache.get(runId), status: "ready", error: null });
      return;
    }

    let cancelled = false;
    setState({ detail: null, status: "loading", error: null });

    (async () => {
      try {
        const detail = await loadRunDetailNative(run);
        if (detail.report) {
          if (_cache.size >= CACHE_MAX) _cache.delete(_cache.keys().next().value);
          _cache.set(runId, detail);
        }
        if (!cancelled) setState({ detail, status: "ready", error: null });
      } catch (err) {
        if (!cancelled) setState({ detail: null, status: "missing", error: err.message || "run_path_unavailable" });
      }
    })();

    return () => { cancelled = true; };
  }, [runId, run?.path, run]);

  return state;
}

