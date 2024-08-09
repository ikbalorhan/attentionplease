Attention Please: Turkish NLP Project
This repository contains the code and notebooks related to the "Attention Please" project, which is focused on Turkish Natural Language Processing (NLP). The project involves tasks such as sentiment analysis, named entity recognition (NER), and syntactic analysis using various models and tools.

Project Structure
web_service_attention_please.py: This is the main Python script that runs a FastAPI web service for performing sentiment analysis and named entity recognition on Turkish text. It integrates the Zemberek library for morphological analysis and uses Hugging Face Transformers for sentiment and NER tasks.

semisupervised_dataset.ipynb: A Jupyter Notebook that involves creating and processing a semi-supervised dataset for Turkish NLP tasks.

sentiment_analysis.ipynb: A Jupyter Notebook that details the sentiment analysis pipeline, including data preprocessing, model training, and evaluation.

ner.ipynb: Jupyter Notebooks (multiple versions) that describe the Named Entity Recognition (NER) pipeline, including model training and evaluation specific to Turkish text.

companies.csv: A CSV file containing a list of company names, used in the NER task to identify and tag company entities in Turkish text.

To install the required library Zemberek: https://drive.google.com/drive/u/0/folders/0B9TrB39LQKZWX1RSang3M1VkYjQ?resourcekey=0-uFoTlb0PoP0otWan6JkCLg
Select the latest version from this link and download or save the zemberek-full.jar file to your drive (don't forget to rename it back to zemberek-full.jar if you change the name).
