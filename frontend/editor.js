// frontend/editor.js
const editor = CodeMirror(document.getElementById("editor"), {
  mode: "stex",
  lineNumbers: true,
  value: `\\documentclass{article}
\\begin{document}
Hello, world. This is a small LaTeX document.
\\section{Test}
Math: $E = mc^2$.
\\end{document}
`
});

async function postTextToEndpoint(url, filename) {
  const tex = editor.getValue();
  const form = new FormData();
  form.append("tex_text", tex);
  form.append("main", filename);
  const resp = await fetch(url, { method: "POST", body: form });
  return resp;
}

document.getElementById("compilePdf").addEventListener("click", async () => {
  const filename = document.getElementById("filename").value || "main.tex";
  const resp = await postTextToEndpoint("/compile/pdf", filename);
  if (!resp.ok) {
    const txt = await resp.text();
    alert("Compile failed: " + txt);
    return;
  }
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  document.getElementById("pdfPreview").src = url;
});

document.getElementById("compileDocx").addEventListener("click", async () => {
  const filename = document.getElementById("filename").value || "main.tex";
  const resp = await postTextToEndpoint("/compile/docx", filename);
  if (!resp.ok) {
    const txt = await resp.text();
    alert("DOCX failed: " + txt);
    return;
  }
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "output.docx";
  a.textContent = "Download DOCX";
  const container = document.getElementById("docxLink");
  container.innerHTML = "";
  container.appendChild(a);
});