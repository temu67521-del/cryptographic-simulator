/* Cryptographic Systems Simulator - Frontend Controller & 3D Physics */

const ALGO_META = {
  caesar: {
    name: "Caesar Cipher",
    subtitle: "Monoalphabetic shift mapping (0–25)",
    keyType: "range",
    min: 0,
    max: 25,
    defaultKey: 7,
    keyLabel: "Shift Offset",
    sample: "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
  },
  playfair: {
    name: "Playfair Cipher",
    subtitle: "5×5 I/J matrix digraph substitution with X filler",
    keyType: "text",
    defaultKey: "MONARCHY",
    keyLabel: "Matrix Keyword",
    sample: "HIDETHEGOLDINTHETREESTUMP",
  },
  vigenere: {
    name: "Vigenère Cipher",
    subtitle: "Polyalphabetic repeating keyword stream",
    keyType: "text",
    defaultKey: "QUANTUM",
    keyLabel: "Alphabetic Keyword",
    sample: "ATTACKATDAWNWITHFULLFORCE",
  },
  rail_fence: {
    name: "Rail Fence Cipher",
    subtitle: "2D zig-zag transposition across rails (2–10)",
    keyType: "range",
    min: 2,
    max: 10,
    defaultKey: 4,
    keyLabel: "Rail Depth",
    sample: "WEAREDISCOVEREDFLEEATONCE",
  },
  columnar: {
    name: "Columnar Transposition",
    subtitle: "Keyword column permutation with X padding",
    keyType: "text",
    defaultKey: "ZEBRAS",
    keyLabel: "Permutation Keyword",
    sample: "WEAREDISCOVEREDFLEEATONCE",
  },
};

const state = {
  algorithm: "playfair",
  mode: "encrypt",
  keys: {
    caesar: 7,
    playfair: "MONARCHY",
    vigenere: "QUANTUM",
    rail_fence: 4,
    columnar: "ZEBRAS",
  },
  lastResult: null,
  activeDigraphIdx: 0,
  charts: {
    latency: null,
    throughput: null,
    frequency: null,
  },
};

const els = {};

document.addEventListener("DOMContentLoaded", () => {
  cacheElements();
  initTiltPhysics();
  bindControls();
  renderKeyControl();
  executeTransform();
  runBenchmark();
});

function cacheElements() {
  els.algoSelector = document.getElementById("algo-selector");
  els.modeToggle = document.getElementById("mode-toggle");
  els.modePill = document.getElementById("mode-pill");
  els.activeAlgoBadge = document.getElementById("active-algo-badge");
  els.statusBadge = document.getElementById("status-badge");
  els.keyContainer = document.getElementById("key-control-container");
  els.inputText = document.getElementById("input-text");
  els.sampleBtn = document.getElementById("sample-btn");
  els.swapBtn = document.getElementById("swap-btn");
  els.executeBtn = document.getElementById("execute-btn");
  els.replayBtn = document.getElementById("replay-btn");
  els.copyBtn = document.getElementById("copy-btn");
  els.errorBanner = document.getElementById("error-banner");
  els.visTitle = document.getElementById("vis-title");
  els.visSubtitle = document.getElementById("vis-subtitle");
  els.visStage = document.getElementById("visualizer-stage");
  els.outputBox = document.getElementById("output-box");
  els.outputLengthBadge = document.getElementById("output-length-badge");
  els.benchmarkBtn = document.getElementById("benchmark-btn");
  els.plainEntropy = document.getElementById("plain-entropy");
  els.cipherEntropy = document.getElementById("cipher-entropy");
}

function initTiltPhysics() {
  const cards = document.querySelectorAll("[data-tilt]");
  cards.forEach((card) => {
    card.addEventListener("pointermove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;
      const rx = ((0.5 - y) * 5).toFixed(2);
      const ry = ((x - 0.5) * 5).toFixed(2);
      card.style.setProperty("--rx", `${rx}deg`);
      card.style.setProperty("--ry", `${ry}deg`);
    });

    card.addEventListener("pointerleave", () => {
      card.style.setProperty("--rx", "0deg");
      card.style.setProperty("--ry", "0deg");
    });
  });
}

function bindControls() {
  els.algoSelector.addEventListener("click", (e) => {
    const btn = e.target.closest(".algo-btn");
    if (!btn) return;
    state.algorithm = btn.dataset.algo;
    els.algoSelector.querySelectorAll(".algo-btn").forEach((b) => b.classList.toggle("active", b === btn));
    els.activeAlgoBadge.textContent = ALGO_META[state.algorithm].name;
    renderKeyControl();
    executeTransform();
  });

  els.modeToggle.addEventListener("click", (e) => {
    const btn = e.target.closest(".mode-btn");
    if (!btn) return;
    state.mode = btn.dataset.mode;
    els.modeToggle.querySelectorAll(".mode-btn").forEach((b) => b.classList.toggle("active", b === btn));
    els.modePill.textContent = state.mode.toUpperCase();
    executeTransform();
  });

  els.sampleBtn.addEventListener("click", () => {
    els.inputText.value = ALGO_META[state.algorithm].sample;
    executeTransform();
  });

  els.swapBtn.addEventListener("click", () => {
    const out = els.outputBox.textContent.trim();
    if (!out) return;
    els.inputText.value = out;
    state.mode = state.mode === "encrypt" ? "decrypt" : "encrypt";
    els.modeToggle.querySelectorAll(".mode-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.mode === state.mode);
    });
    els.modePill.textContent = state.mode.toUpperCase();
    executeTransform();
  });

  els.executeBtn.addEventListener("click", executeTransform);
  els.replayBtn.addEventListener("click", trigger3DFlipWave);

  els.copyBtn.addEventListener("click", async () => {
    const text = els.outputBox.textContent;
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      els.copyBtn.textContent = "Copied!";
      setTimeout(() => {
        els.copyBtn.textContent = "Copy";
      }, 1400);
    } catch {
      els.copyBtn.textContent = "Failed";
    }
  });

  els.benchmarkBtn.addEventListener("click", runBenchmark);
}

function renderKeyControl() {
  const meta = ALGO_META[state.algorithm];
  const currentKey = state.keys[state.algorithm];

  if (meta.keyType === "range") {
    els.keyContainer.innerHTML = `
      <label class="field-label" for="key-range-input">${meta.keyLabel} (${meta.min}–${meta.max})</label>
      <div class="range-row">
        <input id="key-range-input" class="cyber-range" type="range" min="${meta.min}" max="${meta.max}" value="${currentKey}" />
        <span class="range-value" id="key-range-value">${currentKey}</span>
      </div>
    `;
    const rangeInput = document.getElementById("key-range-input");
    const rangeVal = document.getElementById("key-range-value");
    rangeInput.addEventListener("input", () => {
      state.keys[state.algorithm] = Number(rangeInput.value);
      rangeVal.textContent = rangeInput.value;
    });
    rangeInput.addEventListener("change", executeTransform);
  } else {
    els.keyContainer.innerHTML = `
      <label class="field-label" for="key-text-input">${meta.keyLabel}</label>
      <input id="key-text-input" class="cyber-input" type="text" value="${escapeHtml(String(currentKey))}" placeholder="Enter alphabetic key..." />
    `;
    const textInput = document.getElementById("key-text-input");
    textInput.addEventListener("input", () => {
      state.keys[state.algorithm] = textInput.value;
    });
  }
}

async function executeTransform() {
  hideError();
  els.statusBadge.textContent = "Computing...";

  const payload = {
    algorithm: state.algorithm,
    mode: state.mode,
    text: els.inputText.value,
    key: state.keys[state.algorithm],
  };

  try {
    const res = await fetch("/api/transform", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Transformation failed.");
    }

    state.lastResult = data;
    state.activeDigraphIdx = 0;
    els.outputBox.textContent = data.output;
    els.outputLengthBadge.textContent = `${data.output.length} chars`;
    els.statusBadge.textContent = "Trace Ready";
    renderVisualizer(data.trace);
    trigger3DFlipWave();
  } catch (err) {
    showError(err.message);
    els.statusBadge.textContent = "Validation Error";
  }
}

function renderVisualizer(trace) {
  const meta = ALGO_META[state.algorithm];
  els.visTitle.textContent = `${meta.name} — 3D Trace`;
  els.visSubtitle.textContent = meta.subtitle;

  if (!trace || !trace.algorithm) {
    els.visStage.innerHTML = `<p class="vis-subtitle">No trace data available.</p>`;
    return;
  }

  switch (trace.algorithm) {
    case "caesar":
      renderCaesarTrace(trace);
      break;
    case "playfair":
      renderPlayfairTrace(trace);
      break;
    case "vigenere":
      renderVigenereTrace(trace);
      break;
    case "rail_fence":
      renderRailFenceTrace(trace);
      break;
    case "columnar":
      renderColumnarTrace(trace);
      break;
  }
}

function renderCaesarTrace(trace) {
  const plainRow = trace.plain_alphabet
    .map((ch) => `<div class="alpha-tile tile-3d">${ch}</div>`)
    .join("");
  const shiftedRow = trace.shifted_alphabet
    .map((ch) => `<div class="alpha-tile shifted tile-3d">${ch}</div>`)
    .join("");
  const steps = trace.steps
    .slice(0, 28)
    .map(
      (s) => `
      <div class="step-chip tile-3d">
        <span>${escapeHtml(s.input_char)}</span>
        <span class="arrow">&rarr;</span>
        <span class="out">${escapeHtml(s.output_char)}</span>
      </div>`
    )
    .join("");

  els.visStage.innerHTML = `
    <div class="caesar-strips">
      <div class="alpha-row"><span class="row-tag">Plain</span>${plainRow}</div>
      <div class="alpha-row"><span class="row-tag">+${trace.shift} Shift</span>${shiftedRow}</div>
    </div>
    <div class="step-ribbon">${steps}</div>
  `;
}

function renderPlayfairTrace(trace) {
  const active = trace.digraphs[state.activeDigraphIdx] || null;
  const inCoords = active ? active.coords.map((c) => `${c[0]},${c[1]}`) : [];
  const outCoords = active ? active.result_coords.map((c) => `${c[0]},${c[1]}`) : [];

  const gridHtml = trace.matrix
    .map((row, r) =>
      row
        .map((cell, c) => {
          const key = `${r},${c}`;
          const cls = outCoords.includes(key)
            ? "hl-output"
            : inCoords.includes(key)
              ? "hl-input"
              : "";
          return `<div class="pf-cell cell-3d ${cls}" data-coord="${key}">${escapeHtml(cell)}</div>`;
        })
        .join("")
    )
    .join("");

  const digraphsHtml = trace.digraphs
    .map(
      (d, idx) => `
      <button type="button" class="digraph-pill ${idx === state.activeDigraphIdx ? "active" : ""}" data-didx="${idx}">
        <span>${d.pair} &rarr; <strong>${d.result}</strong></span>
        <span class="rule-tag rule-${d.rule}">${d.rule}</span>
      </button>`
    )
    .join("");

  els.visStage.innerHTML = `
    <div class="playfair-layout">
      <div class="playfair-grid">${gridHtml}</div>
      <div class="digraph-list" id="digraph-list">${digraphsHtml}</div>
    </div>
  `;

  const listEl = document.getElementById("digraph-list");
  if (listEl) {
    listEl.addEventListener("click", (e) => {
      const pill = e.target.closest(".digraph-pill");
      if (!pill) return;
      state.activeDigraphIdx = Number(pill.dataset.didx);
      renderPlayfairTrace(trace);
    });
  }
}

function renderVigenereTrace(trace) {
  const limit = Math.min(trace.plaintext_chars.length, 32);
  const makeRow = (arr, cls = "") =>
    arr
      .slice(0, limit)
      .map((ch) => `<div class="vig-cell tile-3d ${cls}">${escapeHtml(ch)}</div>`)
      .join("");

  els.visStage.innerHTML = `
    <div class="vig-scroll">
      <div class="vig-grid">
        <div class="vig-row"><span class="row-tag">Plain</span>${makeRow(trace.plaintext_chars)}</div>
        <div class="vig-row"><span class="row-tag">Key</span>${makeRow(trace.keystream_chars, "key")}</div>
        <div class="vig-row"><span class="row-tag">Output</span>${makeRow(trace.ciphertext_chars, "out")}</div>
      </div>
    </div>
  `;
}

function renderRailFenceTrace(trace) {
  const rowsHtml = trace.matrix
    .map(
      (row, rIdx) => `
      <div class="rail-row">
        <span class="row-tag">Rail ${rIdx + 1}</span>
        ${row
          .map((ch) =>
            ch !== null
              ? `<div class="rail-node active cell-3d">${escapeHtml(ch)}</div>`
              : `<div class="rail-node empty">&middot;</div>`
          )
          .join("")}
      </div>`
    )
    .join("");

  const railsSummary = trace.rail_strings
    .map((s, idx) => `<span class="step-chip">R${idx + 1}: <strong class="out">${escapeHtml(s)}</strong></span>`)
    .join("");

  els.visStage.innerHTML = `
    <div class="rail-scroll">
      <div class="rail-matrix">${rowsHtml}</div>
    </div>
    <div class="step-ribbon">${railsSummary}</div>
  `;
}

function renderColumnarTrace(trace) {
  const headerHtml = trace.keyword
    .split("")
    .map(
      (ch, idx) => `
      <th class="col-th tile-3d">
        ${escapeHtml(ch)}
        <span class="col-rank">#${trace.ranks[idx]}</span>
      </th>`
    )
    .join("");

  const rowsHtml = trace.grid
    .map(
      (row) => `
      <tr>
        ${row.map((ch) => `<td class="col-td cell-3d">${escapeHtml(ch)}</td>`).join("")}
      </tr>`
    )
    .join("");

  const readoutHtml = trace.readout_sequence
    .map(
      (item) => `
      <div class="step-chip">
        <span>#${item.rank} (${escapeHtml(item.letter)})</span>
        <span class="arrow">&rarr;</span>
        <span class="out">${escapeHtml(item.chars.join(""))}</span>
      </div>`
    )
    .join("");

  els.visStage.innerHTML = `
    <div class="col-scroll">
      <table class="col-table">
        <thead><tr>${headerHtml}</tr></thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    </div>
    <div class="step-ribbon">${readoutHtml}</div>
  `;
}

function trigger3DFlipWave() {
  const nodes = els.visStage.querySelectorAll(".tile-3d, .cell-3d");
  nodes.forEach((node, idx) => {
    node.classList.remove("is-flipped");
    void node.offsetWidth;
    node.style.animationDelay = `${Math.min(idx * 12, 420)}ms`;
    node.classList.add("is-flipped");
  });
}

async function runBenchmark() {
  els.benchmarkBtn.disabled = true;
  els.benchmarkBtn.querySelector(".btn-text").textContent = "Benchmarking...";

  try {
    const res = await fetch("/api/benchmark", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        runs: 20,
        custom_text: els.inputText.value,
        selected_algorithm: state.algorithm,
        selected_key: state.keys[state.algorithm],
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error("Benchmark failed");

    els.plainEntropy.textContent = `${data.entropy.plaintext} bits`;
    els.cipherEntropy.textContent = `${data.entropy.ciphertext} bits`;
    renderCharts(data);
  } catch (err) {
    showError(err.message);
  } finally {
    els.benchmarkBtn.disabled = false;
    els.benchmarkBtn.querySelector(".btn-text").textContent = "Run Benchmark";
  }
}

function renderCharts(data) {
  const palette = {
    caesar: "#00f5d4",
    playfair: "#8338ec",
    vigenere: "#ffbe0b",
    rail_fence: "#38bdf8",
    columnar: "#fb7185",
  };

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: "#cbd5e1", font: { family: "Inter", size: 11 } },
      },
    },
    scales: {
      x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
      y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.06)" } },
    },
  };

  // 1. Latency Line Chart
  if (state.charts.latency) state.charts.latency.destroy();
  state.charts.latency = new Chart(document.getElementById("latency-chart"), {
    type: "line",
    data: {
      labels: data.payload_labels,
      datasets: data.algorithms.map((algo) => ({
        label: algo.label,
        data: data.latency_ms[algo.id],
        borderColor: palette[algo.id],
        backgroundColor: palette[algo.id],
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 3,
      })),
    },
    options: commonOptions,
  });

  // 2. Throughput Bar Chart (50 KB payload index = 3)
  if (state.charts.throughput) state.charts.throughput.destroy();
  state.charts.throughput = new Chart(document.getElementById("throughput-chart"), {
    type: "bar",
    data: {
      labels: data.algorithms.map((a) => a.label),
      datasets: [
        {
          label: "MB/s @ 50 KB",
          data: data.algorithms.map((a) => data.throughput_mbps[a.id][3]),
          backgroundColor: data.algorithms.map((a) => palette[a.id]),
          borderRadius: 8,
        },
      ],
    },
    options: commonOptions,
  });

  // 3. Frequency Distribution Chart (Plaintext vs Ciphertext)
  const letters = data.frequency_distribution.labels;
  if (state.charts.frequency) state.charts.frequency.destroy();
  state.charts.frequency = new Chart(document.getElementById("frequency-chart"), {
    type: "bar",
    data: {
      labels: letters,
      datasets: [
        {
          label: "Plaintext %",
          data: letters.map((l) => data.frequency_distribution.plaintext[l]),
          backgroundColor: "rgba(0, 245, 212, 0.65)",
          borderRadius: 4,
        },
        {
          label: `${data.entropy.sample_algorithm} Cipher %`,
          data: letters.map((l) => data.frequency_distribution.ciphertext[l]),
          backgroundColor: "rgba(131, 56, 236, 0.72)",
          borderRadius: 4,
        },
      ],
    },
    options: commonOptions,
  });
}

function showError(msg) {
  els.errorBanner.textContent = msg;
  els.errorBanner.hidden = false;
}

function hideError() {
  els.errorBanner.hidden = true;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
