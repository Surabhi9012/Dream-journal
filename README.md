**Deployed Version**: https://dream-journal-lunv.onrender.com

I have used these NLP model to analyze the dream entered by the user:
**VADER (Valence Aware Dictionary and sEntiment Reasoner):**

A sentiment analysis tool specifically attuned to social media and informal text
Particularly good at understanding:

Emojis and emoticons 😊
Punctuation emphasis!!!
Word modifiers (very, kind of, extremely)
Slang and informal language


Gives sentiment scores on three dimensions:

Positive (0 to 1)
Negative (0 to 1)
Neutral (0 to 1)


Perfect for dream analysis as it can catch subtle emotional tones in personal narratives

**Punkt Tokenizer:**

A pre-trained model for sentence segmentation
Smartly identifies sentence boundaries by understanding:

Abbreviations (Dr., Mr., etc.)
Numbers and decimal points
Special punctuation


In your dream logger, it helps:

Break down long dream descriptions into individual sentences
Preserve proper sentence structure for analysis
Maintain context when analyzing dream segments

Implemented the following methods for pattern matching:

1. TF-IDF Vectorization
TF-IDF (Term Frequency-Inverse Document Frequency) is a statistical technique used to extract and quantify the importance of words in a collection of text documents.

Purpose: Converts textual data (e.g., dream descriptions) into a numerical format that can be used for machine learning algorithms like clustering.

How it Works:

Term Frequency (TF): Measures how often a word appears in a document relative to the total number of words in that document.
Inverse Document Frequency (IDF): Reduces the weight of terms that appear frequently across all documents (e.g., "the", "and").
TF-IDF(t)=TF(t)⋅IDF(t)
Result: Each document (dream description) is represented as a vector where each dimension corresponds to the importance of a word or phrase.
Example in Dreams: Suppose you have three dreams:

"I was flying over a mountain."

"I saw a beautiful mountain."

"I had a recurring dream of flying."

Common words like "I" will have low importance due to high frequency across all entries.
Unique words like "recurring" or "beautiful" will have higher importance for their respective dreams.
2. KMeans Clustering
KMeans is an unsupervised machine learning algorithm used to group data points into a predefined number of clusters. Here, it groups dreams into thematic clusters based on their textual features.

Purpose: Identifies patterns or themes across the dream entries, grouping similar dreams together.

How it Works:

Initialization:
You specify the number of clusters (k), e.g., k=3 for three themes.
Randomly selects k initial cluster centroids (starting points for the clusters).
Assignment Step:
Each dream's TF-IDF vector is assigned to the nearest cluster centroid based on distance (e.g., Euclidean distance).
Update Step:
The centroids are recalculated as the mean of all points in their respective clusters.
Repeat: Steps 2 and 3 are repeated until the centroids stabilize (converge).
Result:

Each dream is assigned to one of the clusters.
The cluster centroids represent the "themes" of the dreams, which can be visualized by identifying the most important terms in each cluster.
