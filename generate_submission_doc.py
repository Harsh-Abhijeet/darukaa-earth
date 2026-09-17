"""Generate the submission Word document for Darukaa.Earth Hackathon."""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

def set_cell_bg(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)

def heading(doc, text, level=1, color_hex="1B5E20"):
    h = doc.add_heading(text, level=level)
    r = h.runs[0]
    r.font.color.rgb = RGBColor(
        int(color_hex[0:2], 16),
        int(color_hex[2:4], 16),
        int(color_hex[4:6], 16)
    )
    return h

def body(doc, text, bold=False, italic=False, size=10.5):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.size = Pt(size)
    return p

def bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.add_run(text).font.size = Pt(10.5)
    return p

def code_para(doc, text):
    p = doc.add_paragraph()
    p.style = doc.styles["Normal"]
    r = p.add_run(text)
    r.font.name = "Courier New"
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)
    p.paragraph_format.left_indent = Inches(0.3)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "EEF2FF")
    pPr.append(shd)
    return p

doc = Document()

# ── Page margins ─────────────────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)

# ═══════════════════════════════════════════════════════════════════════════
# TITLE BLOCK
# ═══════════════════════════════════════════════════════════════════════════
t = doc.add_heading("Darukaa.Earth – AI Biodiversity Intelligence Chatbot", 0)
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
t.runs[0].font.color.rgb = RGBColor(0x1B, 0x5E, 0x20)

sub = doc.add_paragraph("Hackathon Submission Document")
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.runs[0].font.size = Pt(12)
sub.runs[0].font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

date_p = doc.add_paragraph(f"Date: {datetime.date.today().strftime('%B %d, %Y')}")
date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
date_p.runs[0].font.size = Pt(10)
date_p.runs[0].italic = True

doc.add_paragraph()

# ── Divider table ─────────────────────────────────────────────────────────────
div = doc.add_table(rows=1, cols=1)
div.rows[0].height = Cm(0.15)
set_cell_bg(div.rows[0].cells[0], "2E7D32")
div.rows[0].cells[0].text = ""
doc.add_paragraph()

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1 – GITHUB REPOSITORY
# ═══════════════════════════════════════════════════════════════════════════
heading(doc, "1.  GitHub Repository", level=1)

body(doc, (
    "The complete production-quality prototype is hosted on GitHub. "
    "The repository contains the full backend, frontend, RAG knowledge base, "
    "evaluation framework, automated tests, Docker configuration, and GitHub Actions CI/CD pipeline."
))

doc.add_paragraph()
body(doc, "Repository Link:", bold=True)
code_para(doc, "https://github.com/YOUR_USERNAME/darukaa-earth-biodiversity-intelligence")

doc.add_paragraph()
body(doc, "Repository Visibility:", bold=True)
body(doc, (
    "The repository is PUBLIC. No access invitations are required. "
    "Simply open the link above to view the full codebase."
))

body(doc, (
    "  (If you set it to private before submitting, grant access to: "
    "ankita.dasgupta@darukaa.com, harsh.kumar@darukaa.com, "
    "utkarsh.gauniyal@darukaa.com, guneet.mutreja@darukaa.com)"
), italic=True)

doc.add_paragraph()

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2 – LIVE DEMO
# ═══════════════════════════════════════════════════════════════════════════
heading(doc, "2.  Live Demo URL", level=1)

body(doc, (
    "The application is designed to run locally via Docker Compose "
    "(see Section 4 – Local Setup). A live cloud deployment can be added "
    "on request (Render / Railway / Google Cloud Run)."
))

doc.add_paragraph()
body(doc, "Local Demo Endpoints (after docker compose up):", bold=True)
for row in [
    ("Streamlit Frontend (UI)", "http://localhost:8501"),
    ("FastAPI Backend API",     "http://localhost:8000"),
    ("Swagger / OpenAPI Docs",  "http://localhost:8000/docs"),
    ("ReDoc API Reference",     "http://localhost:8000/redoc"),
]:
    p = doc.add_paragraph(style="List Bullet")
    r1 = p.add_run(f"{row[0]}: ")
    r1.bold = True
    r1.font.size = Pt(10.5)
    r2 = p.add_run(row[1])
    r2.font.size = Pt(10.5)
    r2.font.color.rgb = RGBColor(0x15, 0x65, 0xC0)

doc.add_paragraph()

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3 – README OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
heading(doc, "3.  README Overview", level=1)

# ── 3a. Problem Statement ──────────────────────────────────────────────────
heading(doc, "3a.  Problem Statement", level=2, color_hex="2E7D32")
body(doc, (
    "Generic LLMs hallucinate environmental statistics and provide vague advice "
    "(e.g., "practice sustainable farming"). Real agricultural ecosystems are governed "
    "by non-linear bio-physical feedback loops. This system acts as an AI Environmental "
    "Scientist, reasoning across multiple simultaneous variables: "
    "Soil Organic Carbon ↔ Rainfall ↔ Temperature ↔ Land Use ↔ Biodiversity."
))

# ── 3b. Architecture ──────────────────────────────────────────────────────
heading(doc, "3b.  Architecture", level=2, color_hex="2E7D32")
body(doc, "The system is composed of three tiers:")
for t_name, t_desc in [
    ("Presentation Tier",   "Streamlit interactive UI (Port 8501). Chat, Structured Input, Metrics Dashboard, Recommendation Cards, Citation Inspector."),
    ("Application Tier",    "FastAPI backend (Port 8000) powered by a LangGraph 11-step agentic decision engine, multi-metric reasoning rules, hybrid RAG retrieval, and transparent confidence scoring."),
    ("Data Persistence Tier","PostgreSQL 16 + pgvector (Port 5432) storing 14 relational tables including vector-embedded document chunks from FAO, IPCC, UNEP, ISRIC SoilGrids, and GBIF."),
]:
    p = doc.add_paragraph(style="List Bullet")
    p.add_run(f"{t_name}: ").bold = True
    p.add_run(t_desc).font.size = Pt(10.5)

doc.add_paragraph()
heading(doc, "3c.  LangGraph Agentic Workflow (11 Steps)", level=2, color_hex="2E7D32")

steps = [
    "Intent Detection",
    "Environmental Variable Extraction (NLP + Structured Profile)",
    "Missing Data Check",
    "Clarification Node → slot-fill missing variables (multi-turn memory)",
    "Environmental Data Enrichment (ISRIC SoilGrids, NASA POWER, GBIF)",
    "Hybrid Knowledge Retrieval (pgvector + BM25 + Reciprocal Rank Fusion)",
    "Multi-Metric Reasoning Engine (evaluates ≥ 3 simultaneous variables)",
    "Structured Recommendation Generation (strictly bound to literature)",
    "Evidence Validation & Hallucination Guard",
    "Query Rewriting & Deep Retrieval (if evidence is weak → loops back)",
    "Response Formatter & Mathematical Confidence Scoring",
]
for i, s in enumerate(steps, 1):
    bullet(doc, f"Step {i}: {s}")

# ── 3d. Hybrid RAG ──────────────────────────────────────────────────────
doc.add_paragraph()
heading(doc, "3d.  Hybrid RAG Pipeline", level=2, color_hex="2E7D32")
body(doc, (
    "The retrieval pipeline combines Dense Semantic Embeddings (384-dimensional "
    "sentence-transformers/all-MiniLM-L6-v2) with Sparse BM25 Lexical Matching, "
    "fused via Reciprocal Rank Fusion (RRF, k=60) with authority multipliers "
    "for FAO (×1.25), IPCC (×1.25), UNEP/ISRIC/GBIF (×1.18)."
))

code_para(doc, "RRF_Score(d) = Σ [ 1 / (k + rank_dense) + 1 / (k + rank_sparse) ] × Authority_Multiplier(d)")

# ── 3e. Database Schema ──────────────────────────────────────────────────
doc.add_paragraph()
heading(doc, "3e.  Database Schema (PostgreSQL + pgvector)", level=2, color_hex="2E7D32")
body(doc, "14 relational tables conforming to Requirement #14:")

tables = [
    ("users",                "User identity and tenant metadata"),
    ("conversations",        "Multi-turn session state"),
    ("messages",             "Chat turns with extracted state snapshots"),
    ("environmental_profiles","Location, biome, and eco-region data"),
    ("soil_metrics",         "pH, SOC %, moisture, bulk density, sand/clay"),
    ("climate_metrics",      "Annual rainfall, temperature, drought index"),
    ("land_use_metrics",     "Land-use type, crop, buffer strip width"),
    ("biodiversity_metrics", "Species richness, pollinator score, habitat diversity"),
    ("human_impact_metrics", "Fertilizer rate, pesticide applications, erosion risk"),
    ("documents",            "Ingested authoritative source metadata"),
    ("document_chunks",      "Text chunks with pgvector embeddings (Vector(384))"),
    ("citations",            "Formal citation metadata per chunk (Requirement #20)"),
    ("recommendations",      "Structured interventions linked to profiles"),
    ("recommendation_evidence","Junction table linking recommendations to evidence chunks"),
]

tbl = doc.add_table(rows=1, cols=2)
tbl.style = "Table Grid"
hdr = tbl.rows[0].cells
hdr[0].text = "Table"
hdr[1].text = "Description"
for cell in hdr:
    set_cell_bg(cell, "C8E6C9")
    cell.paragraphs[0].runs[0].bold = True
    cell.paragraphs[0].runs[0].font.size = Pt(10)

for name, desc in tables:
    row = tbl.add_row().cells
    row[0].text = name
    row[1].text = desc
    for cell in row:
        cell.paragraphs[0].runs[0].font.size = Pt(9.5)

doc.add_paragraph()

# ── 3f. Evidence Scoring ──────────────────────────────────────────────────
heading(doc, "3f.  Evidence & Confidence Scoring Methodology", level=2, color_hex="2E7D32")
body(doc, "Transparent composite formula (Requirement #19):")
code_para(doc, "Confidence = 0.30 × Source_Authority + 0.30 × Retrieval_Relevance + 0.25 × Data_Completeness + 0.15 × Cross_Source_Concordance")
for label, detail in [
    ("Source Authority (0.30)", "FAO/IPCC = 0.95 | UNEP/ISRIC/GBIF = 0.85 | General = 0.60"),
    ("Retrieval Relevance (0.30)", "Mean cosine similarity of retrieved chunks (0.3–1.0)"),
    ("Data Completeness (0.25)", "Fraction of 5 core environmental axes provided"),
    ("Cross-Source Concordance (0.15)", "≥3 independent sources = 0.95 | 2 sources = 0.80 | 1 = 0.60"),
]:
    p = doc.add_paragraph(style="List Bullet")
    p.add_run(f"{label}: ").bold = True
    p.add_run(detail).font.size = Pt(10.5)

doc.add_paragraph()

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4 – LOCAL SETUP
# ═══════════════════════════════════════════════════════════════════════════
heading(doc, "4.  Local Setup Instructions", level=1)

heading(doc, "Option A: Docker Compose (Recommended – Full PostgreSQL + pgvector Stack)", level=2, color_hex="2E7D32")
for cmd in [
    "git clone https://github.com/YOUR_USERNAME/darukaa-earth-biodiversity-intelligence.git",
    "cd darukaa-earth",
    "cp .env.example .env",
    "docker compose up --build -d",
]:
    code_para(doc, cmd)

doc.add_paragraph()
body(doc, "Then open:")
for label, url in [
    ("Frontend", "http://localhost:8501"),
    ("API Docs", "http://localhost:8000/docs"),
]:
    bullet(doc, f"{label}: {url}")

doc.add_paragraph()
heading(doc, "Option B: Standalone Python (No Docker)", level=2, color_hex="2E7D32")
for cmd in [
    "# Requires uv installed: winget install astral-sh.uv",
    "uv venv && uv pip install -r backend/requirements.txt -r frontend/requirements.txt",
    "",
    "# Terminal 1 – FastAPI Backend",
    ".venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000",
    "",
    "# Terminal 2 – Streamlit Frontend",
    ".venv/Scripts/python.exe -m streamlit run frontend/app.py",
]:
    code_para(doc, cmd) if cmd else doc.add_paragraph()

doc.add_paragraph()
heading(doc, "Environment Variables (.env.example)", level=2, color_hex="2E7D32")
body(doc, "Copy .env.example → .env. All API keys are optional; the system operates fully offline using authoritative regional baselines when external APIs are unavailable.")

for line in [
    "DATABASE_SYNC_URL=postgresql+psycopg2://darukaa:darukaa_earth_secret@localhost:5432/darukaa_earth",
    "ENABLE_SQLITE_FALLBACK=true   # Automatic fallback to SQLite when PostgreSQL is unavailable",
    "OPENAI_API_KEY=               # Optional – system works without LLM API keys",
    "GEMINI_API_KEY=               # Optional",
    "SOILGRIDS_API_URL=https://rest.isric.org/soilgrids/v2.0/properties/query",
    "NASA_POWER_API_URL=https://power.larc.nasa.gov/api/temporal/climatology/point",
    "GBIF_API_URL=https://api.gbif.org/v1/occurrence/search",
]:
    code_para(doc, line)

doc.add_paragraph()

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5 – CI/CD
# ═══════════════════════════════════════════════════════════════════════════
heading(doc, "5.  CI/CD Pipeline (GitHub Actions)", level=1)

body(doc, "Defined in .github/workflows/ci.yml. Triggers on every push and pull request to main/master.")
doc.add_paragraph()
body(doc, "Pipeline Steps:", bold=True)

for step in [
    "Checkout Code",
    "Set up Python 3.11",
    "Install backend and frontend dependencies",
    "Lint with Flake8 (syntax errors and undefined names)",
    "Run Pytest test suite (26 unit, API, RAG, reasoning, and schema tests)",
    "Run 20-Scenario Environmental Evaluation Framework (100% pass rate verified)",
    "Build Backend Docker image (Dockerfile.backend)",
    "Build Frontend Docker image (Dockerfile.frontend)",
]:
    bullet(doc, step)

doc.add_paragraph()

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6 – TEST RESULTS
# ═══════════════════════════════════════════════════════════════════════════
heading(doc, "6.  Test Results Summary", level=1)

tbl2 = doc.add_table(rows=1, cols=3)
tbl2.style = "Table Grid"
for i, h in enumerate(["Test Suite", "Tests", "Result"]):
    c = tbl2.rows[0].cells[i]
    c.text = h
    set_cell_bg(c, "C8E6C9")
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(10)

for suite, count, result in [
    ("pytest tests/ -v (automated)",       "26 / 26",  "100% PASSED"),
    ("python -m evaluation.eval_framework", "20 / 20",  "100% PASSED"),
]:
    row = tbl2.add_row().cells
    row[0].text = suite
    row[1].text = count
    row[2].text = result
    for cell in row:
        cell.paragraphs[0].runs[0].font.size = Pt(9.5)

doc.add_paragraph()

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7 – API QUICK REFERENCE
# ═══════════════════════════════════════════════════════════════════════════
heading(doc, "7.  API Quick Reference (Sample Requests)", level=1)

for method, endpoint, description in [
    ("GET",  "/health",                  "System health and database status"),
    ("POST", "/chat",                    "Multi-turn conversational chat with slot-filling memory"),
    ("POST", "/analyze",                 "Full structured multi-metric diagnostic from JSON profile"),
    ("POST", "/environment/profile",     "Create / update environmental parcel profile"),
    ("GET",  "/environment/{id}",        "Retrieve stored profile by ID"),
    ("POST", "/knowledge/ingest",        "Ingest a new scientific document into the vector knowledge base"),
    ("GET",  "/knowledge/search",        "Hybrid semantic + keyword search over authoritative literature"),
    ("GET",  "/recommendations/{id}",    "Retrieve historical recommendations for a profile"),
    ("GET",  "/sources/{id}",            "Retrieve citation details for an authoritative source"),
]:
    p = doc.add_paragraph(style="List Bullet")
    p.add_run(f"{method} {endpoint}").bold = True
    p.add_run(f" – {description}").font.size = Pt(10.5)

doc.add_paragraph()
body(doc, "Sample POST /analyze request body (Requirement #12):", bold=True)
code_para(doc, '{ "location": {"latitude": 19.07, "longitude": 73.00},')
code_para(doc, '  "soil": {"ph": 6.1, "organic_carbon": 0.3, "moisture": 12.0},')
code_para(doc, '  "climate": {"rainfall": 540.0, "temperature": 29.0},')
code_para(doc, '  "land_use": {"type": "monoculture", "crop": "wheat"},')
code_para(doc, '  "biodiversity": {"species_richness": 12} }')

doc.add_paragraph()

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8 – KNOWLEDGE SOURCES
# ═══════════════════════════════════════════════════════════════════════════
heading(doc, "8.  External APIs & Knowledge Sources", level=1)

tbl3 = doc.add_table(rows=1, cols=3)
tbl3.style = "Table Grid"
for i, h in enumerate(["Source", "Type", "Fallback Baseline"]):
    c = tbl3.rows[0].cells[i]
    c.text = h
    set_cell_bg(c, "C8E6C9")
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(10)

for src, kind, fb in [
    ("ISRIC SoilGrids 250m", "Live REST API", "ISRIC Global Pedological Reference Tables"),
    ("NASA POWER Agroclimatology", "Live REST API", "NASA POWER Climatological Normals"),
    ("GBIF Occurrence API", "Live REST API", "GBIF Agro-Ecological Biome Baselines"),
    ("FAO, IPCC, UNEP, Science/Nature", "Curated Markdown Corpus → pgvector", "Embedded Authoritative Knowledge Base"),
]:
    row = tbl3.add_row().cells
    row[0].text = src
    row[1].text = kind
    row[2].text = fb
    for cell in row:
        cell.paragraphs[0].runs[0].font.size = Pt(9.5)

doc.add_paragraph()

# ── Closing note ──────────────────────────────────────────────────────────
doc.add_paragraph()
div2 = doc.add_table(rows=1, cols=1)
div2.rows[0].height = Cm(0.15)
set_cell_bg(div2.rows[0].cells[0], "2E7D32")
div2.rows[0].cells[0].text = ""
doc.add_paragraph()

footer_p = doc.add_paragraph("All test verification output is available in the repository README.md and evaluation/eval_framework.py.")
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer_p.runs[0].italic = True
footer_p.runs[0].font.size = Pt(9.5)
footer_p.runs[0].font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

OUT = r"C:\Users\hp\.gemini\antigravity\scratch\darukaa-earth\Darukaa_Earth_Hackathon_Submission.docx"
doc.save(OUT)
print(f"SUCCESS: Word document saved to:\n{OUT}")
