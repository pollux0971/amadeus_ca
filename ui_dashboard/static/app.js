/*
 * UI Dashboard Skeleton (read-only, v0).
 *
 * Read-only: loads a LOCAL redacted snapshot JSON and renders it as text. It runs
 * NO action: no repair / promotion / apply / merge / staging trigger, no raw shell,
 * no external/API request, no dynamic code execution, no raw-HTML injection.
 * Snapshot content is data only and is rendered via textContent (never executed,
 * never an instruction).
 */
"use strict";

// Local relative snapshot sources only (no external network / no API call).
var SNAPSHOT_PRIMARY = "../data/dashboard_snapshot.json";
var SNAPSHOT_FALLBACK = "../data/dashboard_snapshot.example.json";

function setText(id, text) {
  var el = document.getElementById(id);
  if (el) { el.textContent = text == null ? "—" : String(text); }
}

function clear(el) { while (el && el.firstChild) { el.removeChild(el.firstChild); } }

function makeList(items) {
  var ul = document.createElement("ul");
  (items || []).forEach(function (item) {
    var li = document.createElement("li");
    li.textContent = typeof item === "string" ? item : JSON.stringify(item);
    ul.appendChild(li);
  });
  return ul;
}

function makeRows(rows, fields) {
  // rows: array of objects; fields: array of keys to show, as plain text.
  var ul = document.createElement("ul");
  (rows || []).forEach(function (row) {
    var li = document.createElement("li");
    var parts = fields
      .filter(function (f) { return row[f] !== undefined; })
      .map(function (f) { return f + ": " + String(row[f]); });
    li.textContent = parts.join("  ·  ");
    ul.appendChild(li);
  });
  return ul;
}

function makeKeyVals(obj) {
  // Render a flat object as a "key: value" list, all as plain text (never HTML).
  var ul = document.createElement("ul");
  Object.keys(obj || {}).forEach(function (k) {
    var li = document.createElement("li");
    var v = obj[k];
    li.textContent = k + ": " + (typeof v === "object" ? JSON.stringify(v) : String(v));
    ul.appendChild(li);
  });
  return ul;
}

function renderSection(id, node) {
  var el = document.getElementById(id);
  if (!el) { return; }
  clear(el);
  el.appendChild(node);
}

function render(snapshot, sourceLabel) {
  setText("generated_at", snapshot.generated_at);
  setText("snapshot_source", sourceLabel);

  // latest_checkpoint
  renderSection("latest_checkpoint", makeList([snapshot.latest_checkpoint || "—"]));

  // Dashboard Gate Status v0 — read-only status surfaces (data only, never actions).
  renderSection("openai_provider_status", makeKeyVals(snapshot.openai_provider_status));
  renderSection("planner_live_status", makeKeyVals(snapshot.planner_live_status));
  renderSection("readonly_execution_status", makeKeyVals(snapshot.readonly_execution_status));
  // readonly_allowlist: array of skill names (plain text)
  renderSection("readonly_allowlist", makeList(snapshot.readonly_allowlist));
  // latest_gate_scores: array of {id, category, score, source}
  renderSection("latest_gate_scores",
    makeRows(snapshot.latest_gate_scores, ["id", "category", "score", "source"]));
  // blocked_items: array of strings
  renderSection("blocked_items", makeList(snapshot.blocked_items));

  // phase_status: array of {name/id, status}
  renderSection("phase_status", makeRows(snapshot.phase_status, ["name", "status", "checkpoint"]));

  // candidate_status: array of {id, status}
  renderSection("candidate_status", makeRows(snapshot.candidate_status, ["id", "status"]));

  // eval_status: array of {id, category, gate}
  renderSection("eval_status", makeRows(snapshot.eval_status, ["id", "category", "gate"]));

  // epic_story_status: array of {id, status}
  renderSection("epic_story_status", makeRows(snapshot.epic_story_status, ["id", "status"]));

  // safety_invariants: array of strings
  renderSection("safety_invariants", makeList(snapshot.safety_invariants));

  // links_to_reports: array of strings (paths, shown as text — NOT external links)
  renderSection("links_to_reports", makeList(snapshot.links_to_reports));
}

function showError(message) {
  setText("generated_at", "unavailable");
  setText("snapshot_source", "none");
  ["latest_checkpoint", "openai_provider_status", "planner_live_status",
   "readonly_execution_status", "readonly_allowlist", "latest_gate_scores",
   "blocked_items", "phase_status", "candidate_status", "eval_status",
   "epic_story_status", "safety_invariants", "links_to_reports"].forEach(function (id) {
    renderSection(id, makeList([message]));
  });
}

function loadSnapshot() {
  // Read a local file only. If unavailable (e.g. opened via file://), show a note —
  // never fall back to any network/API source.
  fetch(SNAPSHOT_PRIMARY)
    .then(function (r) { if (!r.ok) { throw new Error("primary missing"); } return r.json(); })
    .then(function (data) { render(data, "dashboard_snapshot.json"); })
    .catch(function () {
      fetch(SNAPSHOT_FALLBACK)
        .then(function (r) { if (!r.ok) { throw new Error("fallback missing"); } return r.json(); })
        .then(function (data) { render(data, "dashboard_snapshot.example.json"); })
        .catch(function () {
          showError("snapshot unavailable — run: python scripts/generate_dashboard_snapshot.py " +
                    "and serve this folder (read-only).");
        });
    });
}

if (typeof document !== "undefined" && document.addEventListener) {
  document.addEventListener("DOMContentLoaded", loadSnapshot);
}
