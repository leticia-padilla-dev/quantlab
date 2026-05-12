export function getQuantLabContextContractIssues(ctx) {
  const issues = [];
  if (!ctx || typeof ctx !== "object") {
    return ["context_missing"];
  }

  const requiredFunctions = [
    "navigateToSurface",
    "openTab",
    "closeTab",
    "setActiveTab",
    "toggleRunSelection",
    "refreshRegistry",
    "updateTab",
    "findRun",
    "getRuns",
    "getLatestRun",
  ];

  for (const key of requiredFunctions) {
    if (typeof ctx[key] !== "function") issues.push(`missing_fn:${key}`);
  }

  if (!ctx.state || typeof ctx.state !== "object") {
    issues.push("missing_state");
    return issues;
  }

  const requiredStateKeys = ["tabs", "activeTabId", "selectedRunIds", "isInitialized"];
  for (const key of requiredStateKeys) {
    if (!(key in ctx.state)) issues.push(`missing_state_key:${key}`);
  }

  if (!ctx.decision || typeof ctx.decision !== "object") {
    issues.push("missing_decision");
  }

  return issues;
}
