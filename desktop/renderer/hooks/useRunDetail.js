import { useState, useEffect } from "react";
import { buildRunArtifactHref } from "../modules/utils";

const DETAIL_ARTIFACTS = ["report.json", "run_report.json"];
const CACHE_MAX = 50;
const _cache = new Map();

function joinPath(base, leaf) {
  return `${String(base || "").replace(/[\\/]+$/, "")}/${leaf}`;
}

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
      let detail = {
        report: null,
        reportUrl: null,
        directoryEntries: [],
        directoryTruncated: false,
      };

      for (const artifact of DETAIL_ARTIFACTS) {
        const localPath = joinPath(run.path, artifact);
        const href = buildRunArtifactHref(run.path, artifact);
        try {
          const report = await window.quantlabDesktop.readProjectJson(localPath);
          detail = { ...detail, report, reportUrl: href || localPath };
          break;
        } catch (_localErr) {
          if (!href) continue;
          try {
            const report = await window.quantlabDesktop.requestJson(href);
            detail = { ...detail, report, reportUrl: href };
            break;
          } catch (_remoteErr) {
            // Try next artifact name.
          }
        }
      }

      try {
        const listing = await window.quantlabDesktop.listDirectory(run.path, 2);
        detail.directoryEntries = listing.entries || [];
        detail.directoryTruncated = Boolean(listing.truncated);
      } catch (_) {
        // Directory listing is helpful but optional.
      }

      if (detail.report) {
        if (_cache.size >= CACHE_MAX) _cache.delete(_cache.keys().next().value);
        _cache.set(runId, detail);
      }

      if (!cancelled) setState({ detail, status: "ready", error: null });
    })();

    return () => { cancelled = true; };
  }, [runId, run?.path]);

  return state;
}
