const state = {
  checklist: [],
  drawingFile: null,
  selectedId: null,
  zoom: 1,
};

const sampleChecklist = [
  { id: "CL-001", standard: "ISO 1101", checklist: "Feature control frame contains characteristic symbol, tolerance value, and required datum references.", severity: "High" },
  { id: "CL-002", standard: "ISO 5459", checklist: "All datum references used by GD&T frames are defined on the drawing before use.", severity: "High" },
  { id: "CL-003", standard: "ISO 129-1", checklist: "Critical dimensions have explicit tolerance or title-block general tolerance.", severity: "High" },
  { id: "CL-004", standard: "ISO 21920", checklist: "Surface texture callouts use valid parameter syntax such as Ra or Rz with numeric value.", severity: "Medium" },
  { id: "CL-005", standard: "Internal MD", checklist: "Notes avoid ambiguous language such as typical, approximate, TBD, or as required.", severity: "Medium" },
];

const els = {
  drawingInput: document.querySelector("#drawingInput"),
  checklistInput: document.querySelector("#checklistInput"),
  drawingDropzone: document.querySelector("#drawingDropzone"),
  checklistDropzone: document.querySelector("#checklistDropzone"),
  drawingTitle: document.querySelector("#drawingTitle"),
  previewFrame: document.querySelector("#previewFrame"),
  checklistBody: document.querySelector("#checklistBody"),
  evidenceBox: document.querySelector("#evidenceBox"),
  totalCount: document.querySelector("#totalCount"),
  passCount: document.querySelector("#passCount"),
  failCount: document.querySelector("#failCount"),
  openCount: document.querySelector("#openCount"),
  loadSampleButton: document.querySelector("#loadSampleButton"),
  runButton: document.querySelector("#runButton"),
  clearButton: document.querySelector("#clearButton"),
  exportCsvButton: document.querySelector("#exportCsvButton"),
  exportJsonButton: document.querySelector("#exportJsonButton"),
  fitButton: document.querySelector("#fitButton"),
  zoomInButton: document.querySelector("#zoomInButton"),
  zoomOutButton: document.querySelector("#zoomOutButton"),
};

function normalizeRow(row, index) {
  const lower = Object.fromEntries(Object.entries(row).map(([key, value]) => [key.trim().toLowerCase(), value]));
  return {
    id: lower.id || lower.item || lower.no || lower["check id"] || `CL-${String(index + 1).padStart(3, "0")}`,
    standard: lower.standard || lower.iso || lower.reference || "",
    checklist: lower.checklist || lower.description || lower.requirement || lower.item || "",
    severity: lower.severity || lower.priority || "Medium",
    status: lower.status || "Open",
    confidence: lower.confidence || "",
    evidence: lower.evidence || "",
    comment: lower.comment || lower.remark || "",
  };
}

function parseTable(text, fileName = "") {
  const delimiter = fileName.toLowerCase().endsWith(".tsv") || text.includes("\t") ? "\t" : ",";
  const lines = text.split(/\r?\n/).filter((line) => line.trim());
  if (!lines.length) return [];
  const headers = splitDelimitedLine(lines[0], delimiter);
  return lines.slice(1).map((line, index) => {
    const cells = splitDelimitedLine(line, delimiter);
    const row = {};
    headers.forEach((header, headerIndex) => { row[header] = cells[headerIndex] || ""; });
    return normalizeRow(row, index);
  });
}

function splitDelimitedLine(line, delimiter) {
  const cells = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    const next = line[i + 1];
    if (char === '"' && next === '"') { current += '"'; i += 1; }
    else if (char === '"') quoted = !quoted;
    else if (char === delimiter && !quoted) { cells.push(current.trim()); current = ""; }
    else current += char;
  }
  cells.push(current.trim());
  return cells;
}

function renderDrawing(file) {
  state.drawingFile = file;
  els.drawingTitle.textContent = file.name;
  const url = URL.createObjectURL(file);
  els.previewFrame.innerHTML = "";
  const extension = file.name.split(".").pop().toLowerCase();
  const node = extension === "pdf" ? document.createElement("embed") : document.createElement("img");
  node.src = url;
  if (extension === "pdf") node.type = "application/pdf";
  node.alt = file.name;
  node.style.setProperty("--zoom", state.zoom);
  els.previewFrame.appendChild(node);
}

function renderChecklist() {
  if (!state.checklist.length) {
    els.checklistBody.innerHTML = '<tr class="empty-row"><td colspan="7">Upload a checklist or load the sample to start.</td></tr>';
    updateSummary();
    return;
  }
  els.checklistBody.innerHTML = state.checklist.map((item) => `
    <tr data-id="${escapeHtml(item.id)}" class="${item.id === state.selectedId ? "selected" : ""}">
      <td><span class="item-id">${escapeHtml(item.id)}</span><br><small>${escapeHtml(item.severity)}</small></td>
      <td>${escapeHtml(item.standard)}</td>
      <td>${escapeHtml(item.checklist)}</td>
      <td><select class="status-select ${statusClass(item.status)}" data-field="status" aria-label="Status for ${escapeHtml(item.id)}">
        ${["Open", "Pass", "Fail"].map((status) => `<option value="${status}" ${item.status === status ? "selected" : ""}>${status}</option>`).join("")}
      </select></td>
      <td><span class="confidence">${escapeHtml(item.confidence || "-")}</span></td>
      <td><input class="evidence-input" data-field="evidence" value="${escapeAttribute(item.evidence)}" placeholder="bbox / text evidence" /></td>
      <td><textarea data-field="comment" placeholder="Reviewer note">${escapeHtml(item.comment)}</textarea></td>
    </tr>`).join("");
  updateSummary();
  renderEvidence();
}

function statusClass(status) {
  if (status === "Pass") return "status-pass";
  if (status === "Fail") return "status-fail";
  return "status-open";
}

function updateSummary() {
  const pass = state.checklist.filter((item) => item.status === "Pass").length;
  const fail = state.checklist.filter((item) => item.status === "Fail").length;
  const open = state.checklist.length - pass - fail;
  els.totalCount.textContent = state.checklist.length;
  els.passCount.textContent = pass;
  els.failCount.textContent = fail;
  els.openCount.textContent = open;
}

function renderEvidence() {
  const item = state.checklist.find((row) => row.id === state.selectedId);
  if (!item) {
    els.evidenceBox.innerHTML = "<span>Select a checklist row to inspect evidence, status, and comments.</span>";
    return;
  }
  els.evidenceBox.innerHTML = `
    <div><strong>${escapeHtml(item.id)} - ${escapeHtml(item.status)}</strong>${escapeHtml(item.checklist)}</div>
    <div><strong>Standard</strong>${escapeHtml(item.standard || "-")}</div>
    <div><strong>Evidence</strong>${escapeHtml(item.evidence || "-")}</div>
    <div><strong>Comment</strong>${escapeHtml(item.comment || "-")}</div>`;
}

function runMockReview() {
  state.checklist = state.checklist.map((item, index) => {
    const text = `${item.standard} ${item.checklist}`.toLowerCase();
    let status = "Pass";
    let evidence = "Detected matching callout in drawing region";
    let confidence = `${92 - (index % 5) * 4}%`;
    let comment = "Auto check completed. MD engineer should confirm evidence crop.";
    if (text.includes("datum") || text.includes("surface") || text.includes("ambiguous")) {
      status = index % 2 === 0 ? "Fail" : "Open";
      confidence = status === "Fail" ? "78%" : "61%";
      evidence = status === "Fail" ? "Potential missing or inconsistent notation" : "Needs visual confirmation";
      comment = status === "Fail" ? "Review suggested because the required pattern was not confidently found." : "Model confidence is below release threshold.";
    }
    return { ...item, status, confidence, evidence, comment };
  });
  state.selectedId = state.checklist[0]?.id || null;
  renderChecklist();
}

function downloadFile(name, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

function exportJson() {
  const payload = { drawing: state.drawingFile?.name || "", project: collectProjectFields(), checklist: state.checklist, exportedAt: new Date().toISOString() };
  downloadFile("cdcopilot-review.json", JSON.stringify(payload, null, 2), "application/json");
}

function exportCsv() {
  const headers = ["id", "standard", "checklist", "severity", "status", "confidence", "evidence", "comment"];
  const rows = state.checklist.map((item) => headers.map((key) => csvCell(item[key] || "")).join(","));
  downloadFile("cdcopilot-review.csv", [headers.join(","), ...rows].join("\n"), "text/csv;charset=utf-8");
}

function collectProjectFields() {
  return {
    partNumber: document.querySelector("#partNumber").value,
    revision: document.querySelector("#revision").value,
    reviewer: document.querySelector("#reviewer").value,
    standard: document.querySelector("#standard").value,
  };
}

function csvCell(value) { return `"${String(value).replaceAll('"', '""')}"`; }
function escapeHtml(value) { return String(value || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;"); }
function escapeAttribute(value) { return escapeHtml(value).replaceAll("\n", " "); }

function setChecklist(rows) {
  state.checklist = rows.map((row, index) => normalizeRow(row, index));
  state.selectedId = state.checklist[0]?.id || null;
  renderChecklist();
}

function wireDropzone(dropzone, input, callback) {
  input.addEventListener("change", () => { const file = input.files?.[0]; if (file) callback(file); });
  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => { event.preventDefault(); dropzone.classList.add("dragging"); });
  });
  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => { event.preventDefault(); dropzone.classList.remove("dragging"); });
  });
  dropzone.addEventListener("drop", (event) => { const file = event.dataTransfer.files?.[0]; if (file) callback(file); });
}

wireDropzone(els.drawingDropzone, els.drawingInput, renderDrawing);
wireDropzone(els.checklistDropzone, els.checklistInput, (file) => { file.text().then((text) => setChecklist(parseTable(text, file.name))); });
els.loadSampleButton.addEventListener("click", () => setChecklist(sampleChecklist));
els.runButton.addEventListener("click", runMockReview);
els.exportCsvButton.addEventListener("click", exportCsv);
els.exportJsonButton.addEventListener("click", exportJson);
els.clearButton.addEventListener("click", () => {
  state.checklist = [];
  state.drawingFile = null;
  state.selectedId = null;
  state.zoom = 1;
  els.drawingInput.value = "";
  els.checklistInput.value = "";
  els.drawingTitle.textContent = "No drawing uploaded";
  els.previewFrame.innerHTML = '<div class="empty-preview"><span aria-hidden="true">□</span><p>Drawing preview will appear here</p></div>';
  renderChecklist();
});

els.fitButton.addEventListener("click", () => { state.zoom = 1; els.previewFrame.querySelector("img, embed, iframe")?.style.setProperty("--zoom", state.zoom); });
els.zoomInButton.addEventListener("click", () => { state.zoom = Math.min(2, state.zoom + 0.1); els.previewFrame.querySelector("img, embed, iframe")?.style.setProperty("--zoom", state.zoom); });
els.zoomOutButton.addEventListener("click", () => { state.zoom = Math.max(0.5, state.zoom - 0.1); els.previewFrame.querySelector("img, embed, iframe")?.style.setProperty("--zoom", state.zoom); });

els.checklistBody.addEventListener("change", (event) => {
  const row = event.target.closest("tr[data-id]");
  if (!row) return;
  const item = state.checklist.find((entry) => entry.id === row.dataset.id);
  if (!item) return;
  item[event.target.dataset.field] = event.target.value;
  if (event.target.dataset.field === "status") event.target.className = `status-select ${statusClass(event.target.value)}`;
  updateSummary();
  renderEvidence();
});

els.checklistBody.addEventListener("input", (event) => {
  const row = event.target.closest("tr[data-id]");
  if (!row) return;
  const item = state.checklist.find((entry) => entry.id === row.dataset.id);
  if (!item) return;
  item[event.target.dataset.field] = event.target.value;
  renderEvidence();
});

els.checklistBody.addEventListener("click", (event) => {
  const row = event.target.closest("tr[data-id]");
  if (!row) return;
  state.selectedId = row.dataset.id;
  document.querySelectorAll("tbody tr").forEach((entry) => entry.classList.remove("selected"));
  row.classList.add("selected");
  renderEvidence();
});

renderChecklist();
