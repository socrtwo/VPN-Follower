"use strict";

const $ = (id) => document.getElementById(id);
const form = $("form");
const statusEl = $("status");
const verdictEl = $("verdict");
const layersEl = $("layers");

function setStatus(html, isError) {
  statusEl.hidden = !html;
  statusEl.className = "status" + (isError ? " error" : "");
  statusEl.innerHTML = html || "";
}

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

// Flatten a nested data object into [key, value] rows for display.
function flatten(obj, prefix, out) {
  out = out || [];
  for (const [k, v] of Object.entries(obj || {})) {
    const path = prefix ? `${prefix}.${k}` : k;
    if (v == null || v === "" || (Array.isArray(v) && v.length === 0)) continue;
    if (Array.isArray(v)) {
      if (v.every((x) => typeof x !== "object")) out.push([path, v.join(", ")]);
      else v.forEach((x, i) => (typeof x === "object"
        ? flatten(x, `${path}[${i}]`, out) : out.push([`${path}[${i}]`, String(x)])));
    } else if (typeof v === "object") {
      flatten(v, path, out);
    } else {
      out.push([path, String(v)]);
    }
  }
  return out;
}

function renderVerdict(target, verdict) {
  verdictEl.hidden = false;
  verdictEl.innerHTML = "";
  verdictEl.appendChild(el("h2", null, verdict.summary || "Result"));

  const meta = el("div", "meta");
  const likelihood = verdict.concealment_likelihood;
  if (likelihood) {
    const b = el("span", `badge ${likelihood}`, likelihood);
    meta.append("Concealment: ", b);
  }
  if (verdict.network) meta.append(`  ·  ${verdict.network}`);
  if (verdict.asn) meta.append(`  ·  ${verdict.asn}`);
  if (verdict.tor_exit) meta.append("  ·  Tor exit");
  verdictEl.appendChild(meta);

  const signals = verdict.signals || [];
  if (signals.length) {
    const ul = el("ul");
    signals.forEach((s) => ul.appendChild(el("li", null, s)));
    verdictEl.appendChild(ul);
  }
}

function renderLayers(layers) {
  layersEl.innerHTML = "";
  (layers || []).forEach((layer) => {
    const card = el("div", "layer" + (layer.ok ? "" : " bad"));
    card.appendChild(el("h3", null, layer.name));
    if (!layer.ok) {
      card.appendChild(el("div", "note", `unavailable: ${layer.error}`));
      layersEl.appendChild(card);
      return;
    }
    (layer.notes || []).forEach((n) => card.appendChild(el("div", "note", "• " + n)));
    const rows = flatten(layer.data);
    if (rows.length) {
      const table = el("table");
      rows.forEach(([k, v]) => {
        const tr = el("tr");
        tr.appendChild(el("td", "k", k));
        tr.appendChild(el("td", "v", v));
        table.appendChild(tr);
      });
      card.appendChild(table);
    }
    layersEl.appendChild(card);
  });
}

async function run(target) {
  const params = new URLSearchParams({
    target: target || "self",
    rdap: $("opt-rdap").checked ? "1" : "0",
    tor: $("opt-tor").checked ? "1" : "0",
    dnsbl: $("opt-dnsbl").checked ? "1" : "0",
    scan: $("opt-scan").checked ? "1" : "0",
  });
  setStatus('<span class="spinner"></span>Following the trail…');
  verdictEl.hidden = true;
  layersEl.innerHTML = "";
  try {
    const res = await fetch(`api/investigate?${params.toString()}`);
    const data = await res.json();
    if (data.error) { setStatus(data.error, true); return; }
    setStatus("");
    renderVerdict(data.target, data.verdict || {});
    renderLayers(data.layers);
  } catch (err) {
    setStatus(`Request failed: ${err.message}. Is the VPN-Follower server running?`, true);
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  run($("target").value.trim());
});

// --- PWA install prompt -------------------------------------------------
let deferredPrompt = null;
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredPrompt = e;
  $("install").hidden = false;
});
$("install").addEventListener("click", async () => {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
  $("install").hidden = true;
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () =>
    navigator.serviceWorker.register("service-worker.js").catch(() => {}));
}
