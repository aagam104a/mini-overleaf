// ---------- Helpers ----------
const compileBtn = document.getElementById("compileBtn");
const docxBtn = document.getElementById("docxBtn");
const engineSel = document.getElementById("engine");
const statusPill = document.getElementById("statusPill");
const errorPanel = document.getElementById("errorPanel");
const pdfFrame = document.getElementById("pdfPreview");

function setStatus(state, text) {
  statusPill.textContent = text;
  statusPill.classList.remove("ok", "busy", "bad");
  statusPill.classList.add(state);
}

function showError(text) {
  errorPanel.textContent = text || "Unknown error";
  errorPanel.classList.remove("hidden");
}

function hideError() {
  errorPanel.textContent = "";
  errorPanel.classList.add("hidden");
}

function blobToObjectURL(blob) {
  return URL.createObjectURL(blob);
}

// ---------- Editor ----------
const DEFAULT_TEX = `\\documentclass[11pt]{article}
\\usepackage[margin=1in]{geometry}
\\usepackage{amsmath}
\\usepackage{booktabs}
\\usepackage[hidelinks]{hyperref}

\\begin{document}

\\section*{Mini Overleaf — Neobrutal UI}

This is a quick test document.

Inline math: $E = mc^2$.

Displayed math:
\\[
\\int_0^1 x^2\\,dx = \\frac{1}{3}
\\]

\\bigskip

\\begin{tabular}{@{}lrr@{}}
\\toprule
Item & A & B \\\\
\\midrule
Alpha & 10 & 20 \\\\
Beta  & 30 & 40 \\\\
Gamma & 50 & 60 \\\\
\\bottomrule
\\end{tabular}

\\end{document}
`;

const STORAGE_KEY = "mini_overleaf_tex_v1";

const cm = CodeMirror.fromTextArea(document.getElementById("editor"), {
  mode: "stex",
  lineNumbers: true,
  lineWrapping: true,
});

// Load from localStorage
const saved = localStorage.getItem(STORAGE_KEY);
cm.setValue(saved && saved.trim().length ? saved : DEFAULT_TEX);

// Autosave
let saveTimer = null;
cm.on("change", () => {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    localStorage.setItem(STORAGE_KEY, cm.getValue());
  }, 250);
});

// ---------- API Calls ----------
async function compilePdf() {
  setStatus("busy", "COMPILING");
  hideError();

  // Engine is UI-only for now (backend currently compiles with xelatex)
  // You can wire it later by sending engineSel.value to backend.
  const tex = cm.getValue();

  const fd = new FormData();
  fd.append("tex_text", tex);
  fd.append("main", "main.tex");

  try {
    const res = await fetch("/compile/pdf", {
      method: "POST",
      body: fd
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      showError(err.detail || `Compile failed (${res.status})`);
      setStatus("bad", "FAILED");
      return;
    }

    const blob = await res.blob();
    const url = blobToObjectURL(blob);
    pdfFrame.src = url;

    setStatus("ok", "SUCCESS");
  } catch (e) {
    showError(String(e));
    setStatus("bad", "ERROR");
  }
}

async function exportDocx() {
  setStatus("busy", "EXPORTING");
  hideError();

  const tex = cm.getValue();

  const fd = new FormData();
  fd.append("tex_text", tex);
  fd.append("main", "main.tex");

  try {
    const res = await fetch("/compile/docx", {
      method: "POST",
      body: fd
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      showError(err.detail || `DOCX export failed (${res.status})`);
      setStatus("bad", "FAILED");
      return;
    }

    const blob = await res.blob();
    const url = blobToObjectURL(blob);

    // trigger download
    const a = document.createElement("a");
    a.href = url;
    a.download = "output.docx";
    document.body.appendChild(a);
    a.click();
    a.remove();

    setStatus("ok", "DONE");
  } catch (e) {
    showError(String(e));
    setStatus("bad", "ERROR");
  }
}

// ---------- Events ----------
compileBtn.addEventListener("click", compilePdf);
docxBtn.addEventListener("click", exportDocx);

// Keyboard shortcuts:
// Ctrl+Enter -> compile PDF
// Ctrl+S -> export DOCX
window.addEventListener("keydown", (e) => {
  const isMac = navigator.platform.toLowerCase().includes("mac");
  const ctrlOrCmd = isMac ? e.metaKey : e.ctrlKey;

  if (!ctrlOrCmd) return;

  if (e.key === "Enter") {
    e.preventDefault();
    compilePdf();
  }

  if (e.key.toLowerCase() === "s") {
    e.preventDefault();
    exportDocx();
  }
});

// Initial status
setStatus("ok", "IDLE");