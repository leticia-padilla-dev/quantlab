import { useState, useEffect, useCallback, useRef } from "react";
import { basenamePath, parseCsvRows } from "../modules/utils.js";

const EXPERIMENTS_CONFIG_DIR = "configs/experiments";
const SWEEPS_OUTPUT_DIR = "outputs/sweeps";
const MAX_CONFIGS = 12;
const MAX_SWEEPS = 8;
const MAX_SWEEP_ROWS = 5;
const PREVIEW_LINES = 48;

function coerceNumber(value) {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const parsed = Number(String(value ?? "").trim());
  return Number.isFinite(parsed) ? parsed : null;
}

function inferSweepModeFromName(name) {
  const normalized = String(name || "").toLowerCase();
  if (normalized.includes("walkforward")) return "walkforward";
  if (normalized.includes("grid")) return "grid";
  return "sweep";
}

function buildSweepDecisionRows(sweepRunId, configPath, rows) {
  return (rows || []).map((row, index) => ({
    entry_id: `${sweepRunId}:leaderboard:${index}`,
    sweep_run_id: sweepRunId,
    source: "leaderboard",
    row_index: index,
    config_path: configPath || "",
    total_return: coerceNumber(row?.total_return),
    sharpe_simple: coerceNumber(row?.sharpe_simple ?? row?.best_test_sharpe),
    max_drawdown: coerceNumber(row?.max_drawdown),
    trades: coerceNumber(row?.trades ?? row?.n_test_runs),
    label: `Row #${index + 1}`,
    row_snapshot: row,
  }));
}

async function readOptionalJson(path) {
  try {
    return await window.quantlabDesktop.readProjectJson(path);
  } catch (_) {
    return null;
  }
}

async function readOptionalText(path) {
  try {
    return await window.quantlabDesktop.readProjectText(path);
  } catch (_) {
    return "";
  }
}

async function buildConfigEntry(entry) {
  const raw = await readOptionalText(entry.path);
  const previewText = raw ? raw.split(/\r?\n/).slice(0, PREVIEW_LINES).join("\n") : "";
  return {
    name: entry.name,
    path: entry.path,
    relativePath: entry.relative_path || entry.name,
    modifiedAt: entry.modified_at,
    sizeBytes: entry.size_bytes,
    previewText,
  };
}

async function buildSweepSummary(entry) {
  const rootPath = entry.path;
  const fileListing = await window.quantlabDesktop
    .listDirectory(rootPath, 0)
    .catch(() => ({ entries: [], truncated: false }));
  const files = fileListing.entries || [];
  const hasFile = (name) => files.some((f) => f.name === name);

  const sep = rootPath.includes("\\") ? "\\" : "/";
  const metaPath = `${rootPath}${sep}meta.json`;
  const leaderboardPath = `${rootPath}${sep}leaderboard.csv`;
  const experimentsPath = `${rootPath}${sep}experiments.csv`;
  const walkforwardSummaryPath = `${rootPath}${sep}walkforward_summary.csv`;
  const configResolvedPath = `${rootPath}${sep}config_resolved.yaml`;

  const [meta, leaderboardText, experimentsText, walkforwardText] = await Promise.all([
    hasFile("meta.json") ? readOptionalJson(metaPath) : Promise.resolve(null),
    hasFile("leaderboard.csv") ? readOptionalText(leaderboardPath) : Promise.resolve(""),
    hasFile("experiments.csv") ? readOptionalText(experimentsPath) : Promise.resolve(""),
    hasFile("walkforward_summary.csv") ? readOptionalText(walkforwardSummaryPath) : Promise.resolve(""),
  ]);

  const leaderboardRows = parseCsvRows(leaderboardText, MAX_SWEEP_ROWS);
  const walkforwardRows = parseCsvRows(walkforwardText, MAX_SWEEP_ROWS);
  const experimentsRows = parseCsvRows(experimentsText, 1);
  const firstRow = leaderboardRows[0] || experimentsRows[0] || null;

  const runId = meta?.run_id || basenamePath(rootPath);
  const configPath = meta?.config_path || "";
  const decisionRows = buildSweepDecisionRows(
    runId,
    configPath,
    Array.isArray(meta?.top10) && meta.top10.length
      ? meta.top10.slice(0, MAX_SWEEP_ROWS)
      : leaderboardRows,
  );

  return {
    run_id: runId,
    path: rootPath,
    modifiedAt: entry.modified_at,
    createdAt: meta?.created_at || entry.modified_at,
    mode: meta?.mode || inferSweepModeFromName(entry.name),
    configPath,
    configName: basenamePath(configPath),
    nRuns: meta?.n_runs ?? meta?.n_train_runs ?? null,
    nSelected: meta?.n_selected ?? null,
    nTrainRuns: meta?.n_train_runs ?? null,
    nTestRuns: meta?.n_test_runs ?? null,
    topResults: Array.isArray(meta?.top10) ? meta.top10.slice(0, MAX_SWEEP_ROWS) : [],
    decisionRows,
    leaderboardRows,
    walkforwardRows,
    files,
    filesTruncated: Boolean(fileListing.truncated),
    metaPath,
    leaderboardPath,
    experimentsPath,
    walkforwardSummaryPath,
    configResolvedPath,
    hasStructuredData: Boolean(
      leaderboardRows.length ||
      walkforwardRows.length ||
      experimentsRows.length ||
      decisionRows.length ||
      (Array.isArray(meta?.top10) && meta.top10.length),
    ),
    headlineReturn: coerceNumber(firstRow?.total_return),
    headlineSharpe: coerceNumber(firstRow?.sharpe_simple || firstRow?.best_test_sharpe),
    headlineDrawdown: coerceNumber(firstRow?.max_drawdown),
  };
}

async function buildWorkspace() {
  const [configsListing, sweepsListing] = await Promise.all([
    window.quantlabDesktop.listDirectory(EXPERIMENTS_CONFIG_DIR, 0),
    window.quantlabDesktop.listDirectory(SWEEPS_OUTPUT_DIR, 0),
  ]);

  const configEntries = (configsListing.entries || [])
    .filter((e) => e.kind === "file" && /\.ya?ml$/i.test(e.name))
    .sort((a, b) => String(b.modified_at || "").localeCompare(String(a.modified_at || "")))
    .slice(0, MAX_CONFIGS);

  const sweepDirectories = (sweepsListing.entries || [])
    .filter((e) => e.kind === "directory" && e.depth === 0)
    .sort((a, b) => String(b.modified_at || "").localeCompare(String(a.modified_at || "")))
    .slice(0, MAX_SWEEPS);

  const [configs, sweepsRaw] = await Promise.all([
    Promise.all(configEntries.map(buildConfigEntry)),
    Promise.all(sweepDirectories.map(buildSweepSummary)),
  ]);

  return { configs, sweeps: sweepsRaw.filter(Boolean) };
}

/**
 * Lazily builds the experiments workspace via native IPC when legacy has not
 * pre-populated state.experimentsWorkspace.
 *
 * Pass enabled=false to skip all loading (when legacy has already hydrated).
 * Mirrors buildExperimentsWorkspace semantics: same dirs, same shape, no polling.
 */
export function useExperimentsWorkspace(enabled) {
  const [workspace, setWorkspace] = useState({
    status: "idle",
    configs: [],
    sweeps: [],
    error: null,
  });
  const cancelRef = useRef(false);

  const run = useCallback(async () => {
    if (!enabled) return;
    cancelRef.current = false;
    setWorkspace((prev) => ({ ...prev, status: "loading" }));
    try {
      const result = await buildWorkspace();
      if (!cancelRef.current) {
        setWorkspace({ status: "ready", configs: result.configs, sweeps: result.sweeps, error: null });
      }
    } catch (err) {
      if (!cancelRef.current) {
        setWorkspace((prev) => ({
          ...prev,
          status: "error",
          error: err?.message ?? "Failed to read experiment workspace.",
        }));
      }
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) return;
    run();
    return () => {
      cancelRef.current = true;
    };
  }, [enabled, run]);

  return { workspace, refresh: run };
}
