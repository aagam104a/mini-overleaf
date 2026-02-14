# Mini Overleaf

Mini Overleaf is a browser-based LaTeX editor that replicates core Overleaf functionality in a fully self-hosted environment. The application provides live LaTeX editing with PDF preview, DOCX export, structured error extraction, and engine switching between XeLaTeX and pdfLaTeX. It is built using FastAPI on the backend and plain HTML/CSS/JavaScript with CodeMirror on the frontend. LaTeX compilation is handled server-side using TeX Live, and DOCX conversion is powered by Pandoc. The system parses LaTeX log files to extract precise error messages and line context, improving debugging clarity compared to standard LaTeX workflows. The entire application is containerized using Docker and can be deployed to Fly.io for production hosting.

---

## Features

- Live LaTeX editor with CodeMirror
- Server-side PDF compilation (XeLaTeX / pdfLaTeX)
- DOCX export via Pandoc
- Structured error parsing with line-aware debugging
- Engine selection (XeLaTeX / pdfLaTeX)
- Split editor + preview UI
- Autosave and keyboard shortcuts
- Dockerized for consistent deployment
- Deployable to Fly.io

---

## Tech Stack

Backend:
- FastAPI
- XeLaTeX / pdfLaTeX (TeX Live)
- Pandoc
- Uvicorn

Frontend:
- HTML / CSS / JavaScript
- CodeMirror (LaTeX mode)

DevOps:
- Docker
- Fly.io

---

## Running Locally

### 1. Install Requirements

Make sure the following are installed:

- Python 3.12+
- TeX Live (with XeLaTeX and pdfLaTeX)
- Pandoc

### 2. Install Python Dependencies

Navigate to the backend directory:

```bash
cd backend
pip install -r requirements.txt

```bash
pip install -r requirements.txt
```

### 3. Start the Development Server

From the project root directory, run:

```bash
uvicorn backend.app:app --reload
```

Then open your browser and navigate to:

```
http://127.0.0.1:8000
```

The editor and live preview interface should load automatically.

---

## Running with Docker

From the project root directory, build the Docker image:

```bash
docker build -t mini-overleaf .
```

Run the container:

```bash
docker run -p 8080:8080 mini-overleaf
```

Then open:

```
http://localhost:8080
```

---

## Deploying to Fly.io

Ensure Fly CLI is installed and authenticated:

```bash
fly auth login
```

Deploy from the project root:

```bash
fly deploy
```

Once deployment completes, open the live application:

```bash
fly open
```

---

## Project Structure

```
mini-overleaf/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── static/
│       └── frontend/
│
├── Dockerfile
├── fly.toml
└── README.md
```

---

## What This Project Demonstrates

- Full-stack application development
- Server-side LaTeX compilation pipelines
- Structured log parsing and contextual error reporting
- Process orchestration and file isolation
- Document generation (PDF + DOCX)
- Containerization with Docker
- Cloud deployment using Fly.io
- Custom UI/UX implementation with split-pane architecture
