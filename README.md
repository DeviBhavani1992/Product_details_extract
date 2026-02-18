Product Search — minimal prototype

Quick prototype that provides a searchable product catalogue (backend + frontend).

Usage

1. Create a Python venv and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

2. Initialize the SQLite DB with sample data:

```bash
python3 backend/init_db.py
```

3. Run the backend:

```bash
python3 backend/app.py
```

4. Open `frontend/index.html` in a browser (or serve it via a static file server).
