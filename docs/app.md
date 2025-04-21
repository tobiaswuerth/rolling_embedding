# Building an App
The experiments in the Jupyter notebooks are okay, but I felt like to actually get the best results, I needed a better way to interact with the data.
I decided on building a web-based frontend for it using the following setup:

![diagram drawio](https://github.com/user-attachments/assets/be7dff91-e070-4200-b1fc-757112ffe362)

This allows me to build an app using the full capabilities of HTML, CSS and JavaScript and utilize powerful functions in the [Python backend](../web_backend.py).
Note that in the meantime, there is also a local Ollama instance running to use full-fletched LLMs where necessary instead of just the embedding model.

---

## Search Capabilities

To start, I implemented `match_phrase` (search by text) and `KNN query` (search by embedding) search capabilities.
This allows me to find papers (based on arXiv metadata) that include the exact phrasing as well as ones that are semantically similar.

![search capabilities](https://github.com/user-attachments/assets/9c224b69-b30e-49c9-86a3-7233dbe76e31)

One has the option to open a link to arXiv directly or open the details page.

---

## Similarity Graph

I then added a graph to visualize the most similar papers for any given one:

![similarity graph](https://github.com/user-attachments/assets/776eaeba-8b0d-4ff1-b184-a09162b74385)

It offers a preview of the abstract when hovering over the individual nodes.
One can also click on a node to fetch more data. Each request yields 10 more nearest neighbors using KNN algorithm on the abstract embedding.

---

## Downloading and Processing arXiv PDFs

To provide further information, I added the ability to download and process the PDFs.
This starts a whole series of individual steps, like:
1. download paper from arXiv
2. process the PDF using AI
3. try to figure out header hierarchy using AI

![processing paper](https://github.com/user-attachments/assets/98557d66-1503-4418-a132-1a22d6a81b1f)

---

## Tree Structure

Once the text has been extracted and structured, I use it to display the chapters of the PDF as a tree:

![tree structure](https://github.com/user-attachments/assets/4f6bffc6-90f5-485d-9100-1c376281352a)

The hierarchy can be navigated to show the section of the paper.
It also supports LaTeX equations and images. Tables are also shown as images, as long as MinerU was able to extract them.
I further added the ability to summarize chapters (including subchapters) using AI.

---

## Content Map

Given the content, I further tried to visualize it by creating a map:

![content map](https://github.com/user-attachments/assets/3e554921-db6d-4d48-85e5-f2991fa52b85)

Each block is representative of the amount of text in that section.
Each color represents one of the main chapters.
One can highlight a block to get a tooltip with some information or click on it to jump directly into the tree.

---

## Image & Table Overview

Since, at this point, I also had the images and tables extracted, I decided to create an overview for them:

![figure overview](https://github.com/user-attachments/assets/c3108c9b-0b05-4e25-8ace-7e25cc0c316e)

One can also click on them to open them in a separate tab to inspect them more closely.

---

I had a lot of fun building a web app - it's been a while.
Maybe I further extend the capabilities.
Now that I can download and process full-text PDFs I have some ideas to maybe extend the search capability to allow for section matching, or reference linking would also be nice, or maybe a timeline of paper dependencies for a certain topic.
We'll see...

# Known Issues

- The extraction of the information from the PDF using MinerU does not always reliably work. Especially, recognizing all the chapters correctly is apparently a challenge.
- The header hierarchy structure is built using a locally run LLM and might also be faulty.
- Currently, not all LaTeX equation code is displayed correctly.
- Sometimes, when navigating, the active tab indicator does not get updated.
- Certain edge cases might cause content update issues, requiring a full page reload.
- Currently the AI summaries are not persisted
