The goal is to analyse texts by generating vector embeddings using AI. I'd like to search and compare different sources to uncover similarities.

> I'm working on this just for fun and the repo is a work-in-progress.

---
# Overview

## Generating Text Embeddings

> Text embeddings are vector representations of text that map the original text into a mathematical space where words or sentences with similar meanings are located near each other. <sup>[src](https://www.geeksforgeeks.org/what-is-text-embedding/)</sup>

I use the [Alibaba-NLP/gte-multilingual-base](https://huggingface.co/Alibaba-NLP/gte-multilingual-base) model to generate embeddings.
See [playground_0_embedding.ipynb](playground_0_embedding.ipynb) for an example.

## Getting Data
I explore different approaches.

1. downloading arXiv PDFs to perform full text analysis. See:
    - [playground_1_arxiv_download.ipynb](playground_1_arxiv_download.ipynb), some utilities for me to bulk download arXiv PDFs
    - [playground_2_paper.ipynb](playground_2_paper.ipynb), full text processing, splitting a PDF into multiple embeddings
    - [playground_3_process_pdf.ipynb](playground_3_process_pdf.ipynb), some utilities to process a directory full of PDFs.
2. download only arXiv metadata and use `title+abstract` to analyse. See:
    - [playground_5_elastic_metadata.ipynb](playground_5_elastic_metadata.ipynb), showcasing the process of locally setting up a Elastic search database to persist the processed metadata (2.7mio records atm, ~4.5GB)

## Comparing Data
Once I have processed data (Text + Embeddings) I can start comparing and plotting those embeddings to see which texts are similar.

For example, in [playground_4a_comparison.ipynb](playground_4a_comparison.ipynb) I calculate 1 embedding representing the whole paper content and use this for plotting.
![3d_plot](./assets/3d_plot.gif)

In [playground_4b_similarity_search.ipynb](playground_4b_similarity_search.ipynb) I used this search papers matching my query.

## Building an App
All the experiments worked more or less good but I felt like to actually get the best results I
1. need way more data, and
2. need a better way to interact with it to make it

I ended up with the following setup:
![component architecture](./assets/diagram.drawio.png)

This allows me to build an app using the full capabilities of HTML and JavaScript and utilize powerful functions in the [Python backend](web_backend.py).

To start, I implemented `match_phrase` (search by text) and `KNN query by vector` (search by embedding) search capabilities:
![frontend showcase](./assets/frontend_showcase.gif)

I have plans to build upon this and add more novel functionality to explore the arXiv papers.

---
# Setup
Tested on Windows.

## Python
```bash
py -m venv .venv
.\.venv\Scripts\activate
pip3 install -r .\requirements.txt
```

## Web-Backend
```bash
.\.venv\Scripts\activate
py .\web_backend.py
```

This should start the backend server on http://localhost:3001

## Web-Frontend
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

---