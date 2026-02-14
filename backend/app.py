# backend/app.py
import os
import re
import subprocess
import tempfile
from pathlib import Path
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------
# Tool paths (Windows)
# ---------------------------
PDFLATEX = r"C:\Users\Aagam\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe"
XELATEX = r"C:\Users\Aagam\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe"
PANDOC = r"C:\Program Files\Pandoc\pandoc.exe"

assert os.path.exists(PDFLATEX), f"PDFLATEX not found: {PDFLATEX}"
assert os.path.exists(XELATEX), f"XELATEX not found: {XELATEX}"
assert os.path.exists(PANDOC), f"PANDOC not found: {PANDOC}"

# ---------------------------
# App setup
# ---------------------------
app = FastAPI(title="Mini Overleaf (Local, Windows)")

static_dir = Path(__file__).resolve().parent / "static" / "frontend"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return HTMLResponse(index_file.read_text(encoding="utf8"))
    return HTMLResponse("<h2>Mini Overleaf backend running. Put UI in backend/static/frontend/</h2>")


# ---------------------------
# Helpers
# ---------------------------
def run_cmd(cmd: list[str], cwd: str, timeout_s: int = 240) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_s,
    )


def extract_latex_error(log_path: Path, context_chars: int = 5000) -> str:
    """
    TeX fatal errors in the .log are lines starting with '!'.
    Return the first such error plus some context after it.
    If none found, return the last chunk of the log.
    """
    if not log_path.exists():
        return ""
    txt = log_path.read_text(encoding="utf8", errors="ignore")

    idx = txt.find("\n!")
    if idx == -1:
        if txt.startswith("!"):
            idx = 0
        else:
            return txt[-8000:]

    return txt[idx: idx + context_chars]


def snippet_around_error(tex_path: Path, log_path: Path, radius: int = 4) -> str:
    """
    Parses the .log for 'l.<num>' (error line), then returns tex lines around it.
    """
    if not (tex_path.exists() and log_path.exists()):
        return ""

    log_txt = log_path.read_text(encoding="utf8", errors="ignore")
    m = re.search(r"\nl\.(\d+)\b", log_txt)  # finds l.20, l.64, etc.
    if not m:
        return ""

    line_no = int(m.group(1))
    tex_lines = tex_path.read_text(encoding="utf8", errors="ignore").splitlines()

    start = max(1, line_no - radius)
    end = min(len(tex_lines), line_no + radius)

    out = [f"(showing lines {start}-{end}, error at line {line_no})"]
    for i in range(start, end + 1):
        out.append(f"{i:04d}: {tex_lines[i-1]}")
    return "\n".join(out)


def compile_pdf_with_xelatex(workdir: str, mainfile: str) -> tuple[int, str, str]:
    """
    Runs xelatex twice to resolve refs. Returns (rc, stdout, stderr).
    """
    cmd = [XELATEX, "-interaction=nonstopmode", "-halt-on-error", mainfile]

    last = None
    for _ in range(2):
        last = run_cmd(cmd, cwd=workdir, timeout_s=240)
        if last.returncode != 0:
            break

    if last is None:
        return 1, "", "xelatex did not run"
    return last.returncode, last.stdout, last.stderr


def export_docx_with_pandoc(workdir: str, mainfile: str) -> tuple[int, str, str]:
    """
    Converts .tex to .docx via pandoc.
    """
    cmd = [PANDOC, mainfile, "-s", "-o", "output.docx"]
    p = run_cmd(cmd, cwd=workdir, timeout_s=240)
    return p.returncode, p.stdout, p.stderr


# ---------------------------
# Routes
# ---------------------------
@app.post("/compile/pdf")
async def compile_pdf(tex_text: str = Form(...), main: str = Form("main.tex")):
    tmpdir = tempfile.mkdtemp(prefix="compile_")
    tmp_path = Path(tmpdir)

    try:
        tex_path = tmp_path / main
        tex_path.write_text(tex_text, encoding="utf8")

        rc, out, err = compile_pdf_with_xelatex(tmpdir, main)

        pdf_path = tmp_path / (Path(main).stem + ".pdf")
        log_path = tmp_path / (Path(main).stem + ".log")

        if rc != 0 or not pdf_path.exists():
            latex_err = extract_latex_error(log_path, context_chars=5000)
            tex_snip = snippet_around_error(tex_path, log_path, radius=5)

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Compile failed (rc={rc}).\n\n"
                    f"LATEX ERROR (from .log):\n{latex_err}\n\n"
                    f"TEX SNIPPET:\n{tex_snip}\n\n"
                    f"FILES:\n{[p.name for p in tmp_path.glob('*')]}\n\n"
                    f"STDOUT TAIL:\n{out[-1200:]}\n\n"
                    f"STDERR TAIL:\n{err[-1200:]}"
                ),
            )

        return FileResponse(
            str(pdf_path),
            filename="output.pdf",
            media_type="application/pdf",
        )

    finally:
        # NOTE: FileResponse streams; deleting immediately can break it on Windows.
        # For local dev it's OK to leave temp folders.
        pass


@app.post("/compile/docx")
async def compile_docx(tex_text: str = Form(...), main: str = Form("main.tex")):
    tmpdir = tempfile.mkdtemp(prefix="compile_")
    tmp_path = Path(tmpdir)

    try:
        tex_path = tmp_path / main
        tex_path.write_text(tex_text, encoding="utf8")

        rc, out, err = export_docx_with_pandoc(tmpdir, main)

        docx_path = tmp_path / "output.docx"
        if rc != 0 or not docx_path.exists():
            raise HTTPException(
                status_code=400,
                detail=(
                    f"DOCX export failed (rc={rc}).\n\n"
                    f"STDERR:\n{err[-6000:]}\n\n"
                    f"STDOUT:\n{out[-6000:]}\n\n"
                    f"FILES:\n{[p.name for p in tmp_path.glob('*')]}"
                ),
            )

        return FileResponse(
            str(docx_path),
            filename="output.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    finally:
        pass
