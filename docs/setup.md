# Setup
> Tested on Windows.

## Python
Install [python](https://www.python.org/downloads/), then:
```bash
py -m venv .venv
.\.venv\Scripts\activate
pip3 install -r .\requirements.txt
```

To properly use NVIDIA GPUs it is advisable to make sure the correct [PyTorch](https://pytorch.org/get-started/locally/) version is downloaded. For example:
```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

For processing PDFs I use [MinerU](https://github.com/opendatalab/MinerU). The python library should already be installed but the setup further requires downloading the models. They provide the following setup commands:

```bash
wget https://github.com/opendatalab/MinerU/raw/master/scripts/download_models_hf.py -O download_models_hf.py
py download_models_hf.py
del download_models_hf.py
```

---

## Elasticsearch

To store the arXiv metadata I setup a local [Docker](https://www.docker.com/get-started/) instance of [Elasticsearch](https://www.elastic.co/downloads/elasticsearch).

1. install Docker
2. open WSL shell in this directory and execute:
    ```bash
    curl -fsSL https://elastic.co/start-local | sh
    ```

After running the script, you can access Elastic services at the following endpoints:
- Elasticsearch: http://localhost:9200
- Kibana: http://localhost:5601

The script generates a random password for the `elastic` user, and an API key, stored in the [.env file](../elastic-start-local/.env).

---

## Ollama

For a lot of functionality I use [Ollama](https://ollama.com/download) with different models.

Before you can use a specific model, you need to download it using the command:
```bash
ollama pull <modelname>
```

Make sure you have your server running locally:
```bash
ollama serve
```

This should start the web service on http://localhost:11434

---

## Web-Backend
```bash
.\.venv\Scripts\activate
py .\web_backend.py
```

This should start the backend server on http://localhost:3001

---

## Web-Frontend
Requires [NodeJS](https://nodejs.org/en/download).
```bash
cd .\web_frontend\
npm install
npm run dev
```
This should open locally on http://localhost:3000/

To build a distributable you can run the following command.
```bash
npm run build
```
This will create the `../web_frontend/dist/` folder with the files for deployment.