# Building an App
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