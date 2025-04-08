The goal is to analyse texts by generating embeddings in different ways and using those to compare and connect different sources.
This is currently an idea and WIP.

I explore different approaches.
1. downloading PDFs from arXiv archive to perform full text analysis
2. download only arXiv metadata and use title+abstract to analyse

I locally setup a Elastic search database to persist the processed metadata (2.7mio records atm, ~4.5GB)


# Setup on Linux
```bash
python3 -m venv .venv
chmod +x .venv/bin/activate
source .venv/bin/activate
pip3 install -r requirements.txt
```

---

# Run Web-Backend
```bash
.\.venv\Scripts\activate
py .\web_backend.py
```

This should start the backend server on http://localhost:3001

---

# Run Web-Frontend
```bash
cd .\web_frontend\
npm install
npm run dev
```
This should open locally on http://localhost:3000/

and to build a distributable
```bash
npm run build
```
