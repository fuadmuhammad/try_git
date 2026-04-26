from __future__ import annotations

import io
import re
from dataclasses import asdict, dataclass
from typing import Iterable, List

import pdfplumber
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI(title="Core Analysis PDF Analyzer", version="0.2.0")


@dataclass
class CoreAnalysisRow:
    borehole_name: str | None = None
    formation: str | None = None
    lithology: str | None = None
    sample_depth_m: float | None = None
    permeability_to_air_md: float | None = None
    porosity_pct: float | None = None
    initial_water_saturation_pct: float | None = None
    irreducible_water_saturation_pct: float | None = None
    water_recovery_pct: float | None = None
    residual_oil_saturation_pct: float | None = None
    oil_recovery_pct: float | None = None


COLUMN_PATTERNS = {
    "borehole_name": [r"borehole\s*name", r"well\s*name"],
    "formation": [r"formation"],
    "lithology": [r"lithology"],
    "sample_depth_m": [r"sample[_\s-]*depth\s*\(m\)", r"depth\s*\(m\)"],
    "permeability_to_air_md": [r"permeability\s*to\s*air\s*\(md\)", r"kair\s*\(md\)"],
    "porosity_pct": [r"porosity\s*\(%\)"],
    "initial_water_saturation_pct": [r"initial\s*water\s*saturation\s*\(%\)", r"swi\s*\(%\)"],
    "irreducible_water_saturation_pct": [r"irreducible\s*water\s*saturation\s*\(%\)", r"swirr\s*\(%\)"],
    "water_recovery_pct": [r"water\s*recovery\s*\(%\)"],
    "residual_oil_saturation_pct": [r"residual\s*oil\s*saturation\s*\(%\)", r"sor\s*\(%\)"],
    "oil_recovery_pct": [r"oil\s*recovery\s*\(%\)"],
}

DISPLAY_COLUMNS = [
    ("borehole_name", "Borehole Name"),
    ("formation", "Formation"),
    ("lithology", "Lithology"),
    ("sample_depth_m", "Sample Depth (m)"),
    ("permeability_to_air_md", "Permeability to Air (mD)"),
    ("porosity_pct", "Porosity (%)"),
    ("initial_water_saturation_pct", "Initial Water Saturation (%)"),
    ("irreducible_water_saturation_pct", "Irreducible Water Saturation (%)"),
    ("water_recovery_pct", "Water Recovery (%)"),
    ("residual_oil_saturation_pct", "Residual Oil Saturation (%)"),
    ("oil_recovery_pct", "Oil Recovery (%)"),
]


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _to_float(value: str | None) -> float | None:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9.+-]", "", value)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _find_header_indexes(header: Iterable[str]) -> dict[str, int]:
    indexes: dict[str, int] = {}
    header_cells = [_clean_text(c).lower() for c in header]

    for col_name, patterns in COLUMN_PATTERNS.items():
        for idx, cell in enumerate(header_cells):
            if any(re.search(pattern, cell) for pattern in patterns):
                indexes[col_name] = idx
                break

    return indexes


def parse_core_table_from_pdf(pdf_bytes: bytes) -> List[CoreAnalysisRow]:
    rows: List[CoreAnalysisRow] = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                if not table or len(table) < 2:
                    continue

                header = table[0]
                indexes = _find_header_indexes(header)
                if "sample_depth_m" not in indexes:
                    continue

                for raw_row in table[1:]:
                    if not raw_row or all(not _clean_text(c) for c in raw_row):
                        continue

                    row = CoreAnalysisRow(
                        borehole_name=_clean_text(raw_row[indexes["borehole_name"]]) if "borehole_name" in indexes else None,
                        formation=_clean_text(raw_row[indexes["formation"]]) if "formation" in indexes else None,
                        lithology=_clean_text(raw_row[indexes["lithology"]]) if "lithology" in indexes else None,
                        sample_depth_m=_to_float(raw_row[indexes["sample_depth_m"]]) if "sample_depth_m" in indexes else None,
                        permeability_to_air_md=_to_float(raw_row[indexes["permeability_to_air_md"]]) if "permeability_to_air_md" in indexes else None,
                        porosity_pct=_to_float(raw_row[indexes["porosity_pct"]]) if "porosity_pct" in indexes else None,
                        initial_water_saturation_pct=_to_float(raw_row[indexes["initial_water_saturation_pct"]]) if "initial_water_saturation_pct" in indexes else None,
                        irreducible_water_saturation_pct=_to_float(raw_row[indexes["irreducible_water_saturation_pct"]]) if "irreducible_water_saturation_pct" in indexes else None,
                        water_recovery_pct=_to_float(raw_row[indexes["water_recovery_pct"]]) if "water_recovery_pct" in indexes else None,
                        residual_oil_saturation_pct=_to_float(raw_row[indexes["residual_oil_saturation_pct"]]) if "residual_oil_saturation_pct" in indexes else None,
                        oil_recovery_pct=_to_float(raw_row[indexes["oil_recovery_pct"]]) if "oil_recovery_pct" in indexes else None,
                    )
                    rows.append(row)

    return rows


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    header_cells = "".join(f"<th>{label}</th>" for _, label in DISPLAY_COLUMNS)
    cols_js = ", ".join(f"'{name}'" for name, _ in DISPLAY_COLUMNS)
    return f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Core Analysis PDF Analyzer</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; background: #f5f7fb; color: #1a1a1a; }}
    .card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
    button {{ background: #0f62fe; color: white; border: 0; border-radius: 6px; padding: 10px 14px; cursor: pointer; }}
    button:disabled {{ background: #9bb6fb; cursor: not-allowed; }}
    .muted {{ color: #666; }}
    .status {{ margin: 12px 0; font-weight: bold; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; background: white; }}
    th, td {{ border: 1px solid #d7dce5; padding: 8px; text-align: left; font-size: 12px; }}
    th {{ background: #edf2ff; }}
    .table-wrap {{ overflow-x: auto; }}
  </style>
</head>
<body>
  <div class=\"card\">
    <h1>Oil & Gas Core Analysis PDF Analyzer</h1>
    <p class=\"muted\">Upload your SCAL PDF report and get structured results in a table.</p>

    <input id=\"pdfFile\" type=\"file\" accept=\"application/pdf\" />
    <button id=\"analyzeBtn\">Analyze PDF</button>
    <div class=\"status\" id=\"status\"></div>

    <div class=\"table-wrap\">
      <table id=\"resultsTable\" hidden>
        <thead>
          <tr>{header_cells}</tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

  <script>
    const cols = [{cols_js}];
    const fileInput = document.getElementById('pdfFile');
    const button = document.getElementById('analyzeBtn');
    const status = document.getElementById('status');
    const table = document.getElementById('resultsTable');
    const tbody = table.querySelector('tbody');

    button.addEventListener('click', async () => {{
      const file = fileInput.files[0];
      if (!file) {{
        status.textContent = 'Please choose a PDF file first.';
        return;
      }}

      button.disabled = true;
      table.hidden = true;
      tbody.innerHTML = '';
      status.textContent = 'Analyzing...';

      const formData = new FormData();
      formData.append('file', file);

      try {{
        const response = await fetch('/analyze', {{ method: 'POST', body: formData }});
        const result = await response.json();

        if (!response.ok) {{
          throw new Error(result.detail || 'Failed to analyze PDF.');
        }}

        status.textContent = `Found ${{result.records_found}} record(s) in ${{result.file_name}}.`;

        for (const record of result.records) {{
          const tr = document.createElement('tr');
          for (const col of cols) {{
            const td = document.createElement('td');
            td.textContent = record[col] ?? '';
            tr.appendChild(td);
          }}
          tbody.appendChild(tr);
        }}

        table.hidden = result.records.length === 0;
      }} catch (err) {{
        status.textContent = err.message;
      }} finally {{
        button.disabled = false;
      }}
    }});
  </script>
</body>
</html>
"""


@app.post("/analyze")
async def analyze_pdf(file: UploadFile = File(...)) -> dict:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

    parsed_rows = parse_core_table_from_pdf(pdf_bytes)
    return {
        "file_name": file.filename,
        "records_found": len(parsed_rows),
        "records": [asdict(r) for r in parsed_rows],
    }
