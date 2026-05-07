import { buildRunArtifactHref } from "./utils.js";

const DETAIL_ARTIFACTS = ["report.json", "run_report.json"];

function joinPath(base, leaf) {
  return `${String(base || "").replace(/[\\/]+$/, "")}/${leaf}`;
}

/**
 * Native run detail loader via IPC.
 * Replaces the legacy app-legacy.js::loadRunDetail logic.
 *
 * @param {Object} run The run object containing `path`
 * @returns {Promise<Object>} The run detail object
 */
export async function loadRunDetailNative(run) {
  if (!run?.path) {
    throw new Error("run_path_unavailable");
  }

  let detail = {
    report: null,
    reportPath: null,
    reportUrl: null,
    directoryEntries: [],
    directoryTruncated: false,
  };

  for (const artifact of DETAIL_ARTIFACTS) {
    const localPath = joinPath(run.path, artifact);
    const href = buildRunArtifactHref(run.path, artifact);
    try {
      const report = await window.quantlabDesktop.readProjectJson(localPath);
      detail = { ...detail, report, reportPath: localPath, reportUrl: href || localPath };
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

  return detail;
}
