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
