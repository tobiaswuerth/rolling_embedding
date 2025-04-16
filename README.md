The goal is to analyse texts by generating vector embeddings using AI. I'd like to search and compare different sources to uncover similarities.

> I'm working on this just for fun and the repo is a work-in-progress.

---
# Overview

- [Setup](#setup)

Documentation:
- [Generating Text Embeddings](#generate_text_embedding)
- [Getting Data](#getting_data)
- [Initial Testing](#initial_testing)
- [Building an App](#building_app)
- [Different Approaches to Generating Embeddings ](#embedding_approaches)
- [Different Chunk Sizes](#different-chunk-sizes)
- [Data Quality Issue](#data_quality_issue)
- [Best Chunk Size for Embedding Generation](#best_chunk_size)

---

## <a id="generate_text_embedding"></a>Generating Text Embeddings

> Text embeddings are vector representations of text that map the original text into a mathematical space where words or sentences with similar meanings are located near each other. <sup>[src](https://www.geeksforgeeks.org/what-is-text-embedding/)</sup>

I mostly use the [Alibaba-NLP/gte-multilingual-base](https://huggingface.co/Alibaba-NLP/gte-multilingual-base) model to generate embeddings unless otherwise stated.
See [playground_0_embedding.ipynb](playground_0_embedding.ipynb) for an example.

---

## <a id="getting_data"></a>Getting Data
I explore different approaches to get large amounts of data.

1. downloading arXiv PDFs to perform full text analysis. See:
    - [playground_1_arxiv_download.ipynb](playground_1_arxiv_download.ipynb), some utilities for me to bulk download arXiv PDFs
    - [playground_2_paper.ipynb](playground_2_paper.ipynb), full text processing, splitting a PDF into multiple embeddings
    - [playground_3_process_pdf.ipynb](playground_3_process_pdf.ipynb), some utilities to process a directory full of PDFs.
2. download only arXiv metadata and use `title+abstract` to analyse. See:
    - [playground_5_elastic_metadata.ipynb](playground_5_elastic_metadata.ipynb), showcasing the process of locally setting up a Elastic search database to persist the processed metadata (2.7mio records atm, ~4.5GB)

---

## <a id="initial_testing"></a>Initial Testing
Once I have the data I can start with some initial tests.
To process the data I generate an embedding of the combined text `Title+Abstract`

For example, in [playground_4a_comparison.ipynb](playground_4a_comparison.ipynb) I calculate 1 embedding for each paper and use this for plotting to see which papers are similar.

![3d_embedding_plot](https://github.com/user-attachments/assets/77dd532c-e92e-4ccb-9c5d-9dd3dd404a98)

In [playground_4b_similarity_search.ipynb](playground_4b_similarity_search.ipynb) I used this to search papers that match my query.

---

## <a id="building_app"></a>Building an App
All the experiments worked more or less good but I felt like to actually get the best results I
1. need way more data, and
2. need a better way to interact with it

I ended up with the following setup:

![diagram drawio](https://github.com/user-attachments/assets/be7dff91-e070-4200-b1fc-757112ffe362)

This allows me to build an app using the full capabilities of HTML, CSS and JavaScript and utilize powerful functions in the [Python backend](web_backend.py).

To start, I implemented `match_phrase` (search by text) and `KNN query` (search by embedding) search capabilities. This allows me to find papers that include the exact phrasing as well as ones that are semantically similar.
I then added a graph to visualize the most similar papers for a given one, with abstract preview and the ability to expand nodes as desired:

![frontend_showcase](https://github.com/user-attachments/assets/3060781e-485b-4756-8057-bfc133c1ef3d)

I have plans to build upon this and add more novel functionality to explore the arXiv papers.

---

## <a id="embedding_approaches"></a>Different Approaches to Generating Embeddings 

I was wondering if value were to be gained by normalizing paper abstracts into a fixed form.
See: [playground_6a_abstract_summary.ipynb](playground_6a_abstract_summary.ipynb).
For this I defiend a JSON layout of what information I'd like to have and in what order for each paper, like this:
```json
{
    "title": "...",
    "contributions": [ ... ],
    "problems_or_goals": [ ... ],
}
```

The model used for this task was [gemma3:latest](https://ollama.com/library/gemma3:4b) (4b params) inferenced locally using ollama. This is a relatively small model but the results were okay. Processing 1 paper took ~1.5 sec. Processing all of arXiv like this (~2.7mio papers atm) would take ~1.5 months - a commitment I'm not willing to make as of writing.

So, to see if it would be worthwhile I processed ~500 papers to see how different the resulting embeddings actually were:

![histogram_abstract_summary](https://github.com/user-attachments/assets/14633fa9-2a3b-48a0-9bdd-c18ab41b559a)

Now, with most of them being ~90% similar on average, I'm still not willing to process 2.7mio papers...

Also, note that similarity is not indicative of quality in this case, because we have no objective measure. This just shows me that it does not really matter which approach you use. 

---

I'm curious how differently the AI model would summarize a paper if it had more than just the abstract. For this experiment I fed the complete text of the paper into [gemma3:27b](https://ollama.com/library/gemma3:27b) and later [gemma3:latest](https://ollama.com/library/gemma3:4b) (4b). I started with the larger model and noticed that given a larger context window (max. 128K) the inference time increases drastically. After letting it run over night and seeing it getting stuck inbetween I decided to switch to the smaller model, which had a processing time of around ~4s per paper.

I analyzed the papers I had downloaded previously and got the following word counts:

![paper_word_count](https://github.com/user-attachments/assets/bd5926e9-aec5-4b17-a2d3-2acc540bd213)

Since calling ollama with a different context window size redeploys the model every time I decided to fix it at 36000 tokens (~20K words), which should be enough to cover most papers. Paper with more words I just skipped.

The quality of the summaries generated were mixed. Sometimes the model decided to output only very short sentences or use only keywords to summarize, and other times it hallucinated and reprinted a whole bunch of the same sentences. I decided to clean up the data and only consider results that had `contributions` and `problems_or_goals` sentence count and length within ±1.5σ of the mean. 

Given those summaries I again created am embedding for it and compared it to the embedding of the abstract:

![histogram_paper_summary](https://github.com/user-attachments/assets/98141492-28a6-47c6-a336-42fc49bfafc8)

Compared to the experiment before, this one shows a lower mean similarity with a wider spread. This makes sense I guess since the AI digests much more information in the full text version comared to the abstract only one and can therefore produce more distinct embeddings.

---

Furthermore, I tried comparing:
a) embeddings generated just using the abstract, vs.
b) chunking the full paper, calculating the embeddings for all chunks, then taking the mean of those.

See: [playground_6c_abstract_vs_paper.ipynb](playground_6c_abstract_vs_paper.ipynb)

![histogram_abstract_vs_paper](https://github.com/user-attachments/assets/dac386ac-f878-4f2c-8140-305f5911c356)

For this batch the result indicates a lower mean similarity with a wider spread. This means that, compared to the AI abstract summary embedding, the mean full paper chunk embedding is more different to the reference (the embedding generated using just the abstract). 

This also makes sense, I guess. This full text version most certainly includes information that was not present in the abstract, it is therefore clear that it should result in different embeddings. I'm still surprised by how similar they are overall. I guess them being so similar means that (most) scientific authors are relatively good at summarizing their works in the abstract.

Comparing this similarity chart with the chart from the previous experiment, where an AI was used to summarize the full text paper, they appear to be quite similar. For me this indicates that both approaches tend towards the same results, regardless if you chunk the full text and take the mean of those embeddings or if you use an AI to summarize the paper and generate just one embedding for the summary. I guess to speaks to the AIs ability to extract and summarize the gist of a paper. Using different models most certainly would give different results though. One must also consider the amount of compute it takes. Chunking and generating a batch of embeddings is much faster than summarizing using an AI.

Again, embeddings being similar says nothing about the quality though - I really should think about how I can test which one is better, i.e. captures the essence of the texts best.

---

# <a id="different-chunk-sizes"></a>Different Chunk Sizes

Since chunking the text has proven to be efficient I was wondering what the ideal chunk size is. For this I've done some experiments in [playground_7a_chunk_sizes.ipynb](playground_7a_chunk_sizes.ipynb).

When a sentence is converted into an embedding, how different will the embedding become if I add another word? I did a test for a text of ~9500 words and plotted the change that occurs to the embedding each time I append another word to it:

![embedding_saturation](https://github.com/user-attachments/assets/cefe85c9-ae00-46b3-9a1f-b326258a9cd7)

As expected, initially each word contributes a lot to the nature of the embedding, but the longer the text, the more saturated the embedding becomes and the less important individual words are. There are certain parts of the text though that cause more change even later on, probably when the authors of a paper dive into a new line of thought. So, too much text for an embedding and important content might get lost, too little text for an embedding (e.g. single words) and the embedding essentially becomes a dictionary which is not of any use in capturing wider semantic meaning.

I conclude from this that if one wants more nuanced representations, it is advisable to chunk the text and generate multiple embeddings. The question again is, what is a good chunk size?

For the next test, I gathered 20 papers, 10 for one topic (red) and 10 for another topic (blue). To start, I generated 1 embedding per paper by splitting its full text into chunks of length ~1024 (soft-cut) and then taking the mean per paper:

![PCA two topics](https://github.com/user-attachments/assets/58429109-3086-4cd3-ac45-ec1b313902c9)

As expected, the 2D PCA reduction clearly separates the two groups of topics. This is a good sign that the embedding model is effective in capturing semantic differences.

Next, I wondered what would happen when I started changing the chunk size. For this, I ran several iterations, starting with chunk size 8192 (hard-cut) and going down to chunk size 1 (hard-cut). Naturally, this will generate a growing number of embeddings per paper. I do not take the mean of those for the following graphics, but instead show them all at once:

![embedding_evolution_over_chunksize](https://github.com/user-attachments/assets/63188f83-b535-4276-b172-0aafa59b2091)

This illustrates clearly that the two-topic separation starts to break down once the chunk size becomes too small. This can be explained due to the fact that natural language reuses a lot of its phrases, regardless of the topic, leaving only specialized domain vocabulary to distinguish one from the other. 

I also created a visualization with the mean chunked full text paper embedding:

![mean_embedding_evolution_over_chunksize](https://github.com/user-attachments/assets/46b6bfea-1915-479f-b905-2463a93c660f)

As you see here, the separation between the topics becomes less clear the smaller the chunks get. In the end, they just occupy the same region as the word/character vectors get averaged out.

---
# <a id="data_quality_issue"></a>Data Quality Issue

I was wondering why some papers were located at a different spot on the PCA reduced plane. For this, I reconstructed the last frame with chunk size 1 (single character, hard cut) and clustered it:

![paper_character_clusters](https://github.com/user-attachments/assets/9e94296e-6a0f-4e7a-a72a-c9b5bfd66060)

I performed some analysis and found that Cluster 1 (in orange) has a lot more whitespace:

![whitespace_ratio](https://github.com/user-attachments/assets/0b295ce4-398e-41bb-91cf-784a64b6410d)

Digging into why this is I found that the PDF is formatted in such a way that the PDF Reader returns the text weirdly populated with whitespaces, for example:
```plaintext
Thi s c onc l us i on was al r e ady r e ac he d by M ar c hant & Shapi r o ( 1979) ,t hough t he y m ode l l e d s ys t e m swi t h a c or e r adi usi nde pe nde nt of t hebl ac k hol em as s .
```
I already noticed that it is still somewhat difficult to get good quality data from PDFs. arXiv does provide the paper `.tar.gz` though which contains (if present) the LaTeX. That might resolve some of the issues of parsing PDF files, I guess.

I tried different PDF Readers and some return better results but none were perfect. Inspecting the PDF manually I can even see the issue in formatting. Going back to the source of `export.arxiv.org` the issue was present there as well. However, when checking the main domain on `arxiv.org` it all seemed good:

![good_bad_pdf](https://github.com/user-attachments/assets/8f751827-0a02-446b-8845-b3ea9a668340)

I opened a bug report.

Noticing this, I learned 2 things:
1. This issue certainly influenced other parts of this project too
2. It's surprising that, regardless of how unreadable the text might be for us humans, the embedding model and the LLMs in general, for that matter, are still very capable of understanding some things.

I haven't figured out what the other cluster represents that's off to the side, but I assume it must have something todo with the character distribution... 

---

# <a id="best_chunk_size"></a>Best Chunk Size for Embedding Generation

In my attempt to find a good way of finding out what the best chunk size is for embedding generation, I came up with a test that measures the rate of change for decreasing chunk sizes. For this I processed some data in [playground_7b_chunk_size_distance.ipynb](playground_7b_chunk_size_distance.ipynb).

The idea is that the size of a chunk is good as long as it captures the semantic meaning of the text. Meaning, as long as the location of the embedding does not change much, one can make the chunk size smaller. A smaller chunk size has the benefit of resulting in more embeddings for a given text, allowing potentially for more granular searches on specific topics.

To start I loaded ~1000 full text papers I had downloaded before, calculated a mean embedding for them with a chunk size of ~1024 (soft-cut) and clustered them. I then selected the two points which were the furthest apart from each other and gathered ~100 of their neighbors. This gave me two distinct clusters of papers covering different topics:

![2D PCA Plot with two clusters](https://github.com/user-attachments/assets/17edc8e6-78a7-4458-899c-717a59849e07)

I continued by combining all the texts of the respective chunks into one large text and hard-cut it at 1'000'000 characters. These two texts are the base data for further chunking and plotting. For example, chunking with size 4096 with 50% overlap would give me ~490 embeddings for one text. I then take the mean of those embeddings and plot it. In the next round, I reduce the size to say 2048, take the mean again and plot it again. What I'm interested in here is the change in distance between those two locations. Letting this run, the result looks like this:

![embedding centroid_evolution](https://github.com/user-attachments/assets/72dcdb12-bf95-466a-9f42-4c60b5f6bb80)

Moving from larger to smaller chunk sizes initially reduces the relative change. I assume this has to do with the saturation of the embeddings. In the middle, they stabilize, resulting in very little change. And on the right, with very small chunks, the delta starts to increase exponentially, indicating that the embedding can no longer hold on to the semantic meaning that differentiated the text initially.

Taking a moving average and identifying the smallest value shows that the chunk size with the smallest relative change is around 1024 characters. This must not mean that this is the ideal size though. The delta between the location of the centroid at that timestep with the earlier ones is apparent. One can argue that a good chunk size might as well be around 2048 characters. I think going too big or too small does not make much sense.

All of this applies only to this model. Other embedding models generate larger embedding vectors and have different properties. Further tests are needed.

---
# <a id="setup"></a>Setup
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
