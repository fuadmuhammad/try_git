# Core Analysis PDF Analyzer (Oil & Gas)

This app receives a laboratory PDF report and extracts special core analysis fields:

- Borehole Name
- Formation
- Lithology
- Sample_Depth (m)
- Permeability to Air (mD)
- Porosity (%)
- Initial Water Saturation (%)
- Irreducible Water Saturation (%)
- Water Recovery (%)
- Residual Oil Saturation (%)
- Oil Recovery (%)

## Run online on GitHub (Codespaces)

You can run this API online directly from your GitHub repository using **GitHub Codespaces**:

1. Push this repository to GitHub.
2. Click **Code** ➜ **Codespaces** ➜ **Create codespace on main**.
3. In the terminal inside Codespaces, run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. Open the forwarded port **8000** in browser.
5. Use `/docs` for Swagger UI and test `POST /analyze`.

The repo includes `.devcontainer/devcontainer.json` so dependencies are installed automatically.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Server runs at `http://127.0.0.1:8000`.

## Run with Docker

```bash
docker build -t core-analysis-api .
docker run --rm -p 8000:8000 core-analysis-api
```


## Web UI (for non-technical users)

Open the app root page in browser:

- `http://127.0.0.1:8000/` (local)
- or your Codespaces forwarded URL

The page provides:

- PDF upload button
- Analyze action
- Results table with all SCAL fields

## API

### `POST /analyze`

- Form-data field: `file` (PDF)
- Returns extracted records as JSON.

Example:

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -F "file=@/path/to/core-analysis.pdf"
```

## Notes

- Parser reads tables from PDF pages using `pdfplumber`.
- It maps column headers using flexible regex patterns (e.g., `Swirr (%)` for irreducible water saturation).
- If your lab template has different header names, extend `COLUMN_PATTERNS` in `app/main.py`.
- CI workflow (`.github/workflows/ci.yml`) validates syntax and Docker build on each push/PR.
