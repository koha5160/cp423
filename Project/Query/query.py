"""
Author: Herteg Kohar
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer, sent_tokenize
from dataclasses import dataclass, field
from colorama import Fore, Style
import pandas as pd
import json
import spell_correct

N_DOCUMENTS = 3
# Make a class to hold document path and similarity score
@dataclass
class Document:
    path: str = field(default=None)
    score: float = field(default=None)
    hash_: str = field(default=None)


def preprocess_query(query):
    df = pd.DataFrame({"text": [query]})
    tokenizer = RegexpTokenizer(r"\w+")
    stop_words = set(stopwords.words("english"))
    df["text"] = df["text"].apply(lambda x: tokenizer.tokenize(x.lower()))
    df["text"] = df["text"].apply(lambda x: [w for w in x if not w in stop_words])
    df["text"] = df["text"].apply(lambda x: " ".join(x))
    return df["text"]


def get_docs(query_df, inverted_index):
    docs = []
    for word in query_df[0].split():
        if word in inverted_index:
            docs.append(inverted_index[word])
    return docs


def initialize_documents(docs, reversed_mapping):
    seen = set()
    documents = []
    extension = ".txt"
    for doc in docs:
        for occurence in doc["occurences"]:
            if occurence[0] not in seen:
                document = Document()
                document.path = (
                    f"{occurence[2]}/" + reversed_mapping[occurence[0]] + extension
                )
                document.hash_ = occurence[0]
                documents.append(document)
                seen.add(occurence[0])
    return documents


def compute_similarity(documents, query_df):
    for document in documents:
        with open(document.path, "r", encoding="utf-8") as f:
            text = f.read()
        df = pd.DataFrame({"text": [text]})
        tokenizer = RegexpTokenizer(r"\w+")
        # stop_words = set(stopwords.words("english"))
        df["text"] = df["text"].apply(lambda x: tokenizer.tokenize(x.lower()))
        # df["text"] = df["text"].apply(lambda x: [w for w in x if not w in stop_words])
        df["text"] = df["text"].apply(lambda x: " ".join(x))
        vectorizer = TfidfVectorizer()
        X_train_tfidf = vectorizer.fit_transform(df["text"])
        X_test_tfidf = vectorizer.transform(query_df)
        score = cosine_similarity(X_train_tfidf, X_test_tfidf)
        document.score = score[0][0]
    documents.sort(key=lambda x: x.score, reverse=True)
    # Only return top 3
    return documents[:N_DOCUMENTS]


def get_snippet(text, query_words):
    # Split text into sentences
    sentences = sent_tokenize(text)
    # Find sentences containing query words
    relevant_sentences = [
        s for s in sentences if any(q.lower() in s.lower() for q in query_words)
    ]
    # Join relevant sentences to form snippet
    snippet = "\n\n".join(relevant_sentences)
    return snippet


def display_highlighted_terms(documents, query):
    for document in documents:
        with open(document.path, "r", encoding="utf-8") as f:
            text = f.read()
        query_words = query.split()
        text = get_snippet(text, query_words)
        highlighted_document = text
        for term in query_words:
            highlighted_document = highlighted_document.replace(
                term, f"{Fore.GREEN}{term}{Style.RESET_ALL}"
            )
        print(f"Document: {document.hash_}, Path: {document.path}\n")
        print(f"{highlighted_document}\n")


def query_documents(query):
    query = query.lower()
    query_df = preprocess_query(query)

    with open("inverted_index.json", "r") as f:
        inverted_index = json.load(f)
    with open("mapping.json", "r") as f:
        mapping = json.load(f)
    reversed_mapping = {v: k for k, v in mapping.items()}

    query_df[0] = spell_correct_query(query_df[0], inverted_index)

    documents = get_docs(query_df, inverted_index)

    documents = initialize_documents(documents, reversed_mapping)

    documents = compute_similarity(documents, query_df)

    display_highlighted_terms(documents, query)
