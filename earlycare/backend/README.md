# EarlyCare Backend

## What’s currently going wrong

On this machine, `python3` resolves to Anaconda (`/opt/anaconda3/bin/python3`). In that environment, importing `numpy` / `joblib` is hanging, which prevents the Flask server (`app.py`) from starting (it imports `joblib`, `pandas`, etc. at module import time).

## Recommended setup (macOS)

Create a fresh virtual environment (not the `venv/` folder in this repo) and install dependencies:

```bash
cd earlycare/backend
# IMPORTANT: prefer an arm64 Python (avoid Anaconda x86_64 on Apple Silicon).
# If you have Homebrew Python, it’s typically at /usr/local/bin/python3.
/usr/local/bin/python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the server:

```bash
python app.py
```

The backend listens on port `5001` by default.

## Notes

- `pytesseract` requires the **Tesseract** binary to be installed on your system (separate from Python packages).
- The existing `venv/` folder under `earlycare/backend/venv` appears to be a copied environment and is not suitable for macOS.

