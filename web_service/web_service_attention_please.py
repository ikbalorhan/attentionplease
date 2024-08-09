import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from jpype import JClass, JString, startJVM, getDefaultJVMPath, shutdownJVM
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline, AutoModelForTokenClassification
import re
import nltk
from nltk.util import ngrams
import jpype
import jpype.imports
from jpype.types import *
import os
import pandas as pd
import numpy as np
import string

nltk.download('punkt')


app = FastAPI()


jpype.startJVM('-ea', '-Djava.class.path=./zemberek-full.jar')

TurkishMorphology = JClass('zemberek.morphology.TurkishMorphology')
TurkishTokenizer = JClass('zemberek.tokenization.TurkishTokenizer')
morphology = TurkishMorphology.createWithDefaults()
sentence_tokenizer = TurkishTokenizer.DEFAULT

sentiment_model = AutoModelForSequenceClassification.from_pretrained("ikball/turkish-sentiment", from_tf=True)
sentiment_tokenizer = AutoTokenizer.from_pretrained("ikball/turkish-sentiment")
sentiment_pipeline = pipeline("sentiment-analysis", tokenizer=sentiment_tokenizer, model=sentiment_model)


ner_model = AutoModelForTokenClassification.from_pretrained("mext741/turkish-ner-company")
ner_tokenizer = AutoTokenizer.from_pretrained("mext741/turkish-ner-company")
ner_pipeline = pipeline("ner", tokenizer=ner_tokenizer, model=ner_model)

class Item(BaseModel):
    text: str = Field()

def pos_tagging(text):
    analysis_results = morphology.analyzeSentence(JString(text))
    pos_tags = []
    for result in analysis_results:
        for analysis in result.getAnalysisResults():
            pos_tags.append(str(analysis.getPos().shortForm))
    return pos_tags

def stem_word(word):

    stems = ''
    # Analyze and disambiguate the word
    analysis = morphology.analyzeSentence(JString(word))
    best = morphology.disambiguate(JString(word), analysis).bestAnalysis()

        # Extract the lemma for each analysis result
    for parse in best:
        stems = parse.getLemmas()[0]

    return stems

df = pd.read_csv('C:/Users/mehme/Desktop/companies.csv')
company_names = df['company'].str.lower().unique().tolist()

def is_punctuation_only(s):
    return all(char in string.punctuation for char in s)

conjuctions = ['ve', 'ama', 'fakat', 'ancak', 'çünkü', 'lakin', 'sonra', 'bu nedenle', 'bu yüzden', 'acaba']


def find_syntagma(word):
    pos = pos_tagging(word)
    print(pos)
    if not isinstance(word, str):
            word = str(word)

    if word != stem_word(word):
        if (word.endswith('i') or word.endswith('ı')) and (not word.endswith('di') or not word.endswith('dı')):
            return 'BN'  # Belirtili Nesne
        elif word.endswith('e') or word.endswith('a') or word.endswith('den') or word.endswith('dan'):
            return 'DT'  # Dolaylı Tümleç
        elif word.endswith('le') or word.endswith('la'):
            return 'I'  # Araç Tümleci
    return None

def find_completion(word1, word2):
    words = []

    if not isinstance(word1, str):
        words.append(str(word1))
    else:
        words.append(word1)
    if not isinstance(word2, str):
        words.append(str(word2))
    else:
        words.append(word2)


    check = 0
    if words[0].endswith('in') or words[0].endswith('ın') or words[0].endswith('un') or words[0].endswith('ün'):
         check += 1

    if words[1].endswith('e') or words[1].endswith('a'):
         check += 1

    if check == 2:
         return True

    return False

def contains_verb(tokens, is_completion=False):
    for token in tokens:
        if not isinstance(token, str):
            token = str(token)
        analysis = morphology.analyze(JString(token))
        for result in analysis:
            if result.getPos().getStringForm() == "Verb":
              if is_completion == False:
                return True
              else:
                if not find_completion(tokens[0], tokens[1]):
                  print('ha')
                  return True
    return False

def contains_noun_or_adj(tokens, posit=False):
    i = 0
    for token in tokens:
      if find_syntagma(token) is None:
        analysis = morphology.analyze(JString(token))
        for result in analysis:
            if result.getPos().getStringForm() in ["Noun", "Adj"]:
                if posit:
                    return i
                return True
        i += 1
    return False

def contains_company_names(tokens):
  i = 0

  tokens = tokens.split()

  for company_name in company_names:
    for token in tokens:
      if token.startswith(company_name):
        
        return True


def tokenize_sentence(text):
    # Metin girişinin bir string olduğundan emin olun
    if not isinstance(text, str):
        raise TypeError("Input text must be a string")

    tokens = sentence_tokenizer.tokenizeToStrings(JString(text))
    sentences = []
    current_sentence = []
    completions = []
    posis = []
    start_of_current_sentence = 0

    for i, token in enumerate(tokens):
        token_text = str(token)
        current_sentence.append(token_text)

        print(current_sentence)

        print(completions)

        if len(current_sentence) >= 2 and find_completion(tokens[i-1], tokens[i]):
            completions.append(''.join(current_sentence[-2] + ' ' + current_sentence[-1]))
            posis.append(int(len(current_sentence) - 2))
            current_sentence.pop()
            current_sentence.pop()
            start_of_current_sentence = i + 1
            continue

        if token_text in ['.', '!', '?']:
            for completion, pos in zip(completions, posis):
                    current_sentence.insert(pos, completion)

            completions.clear()
            posis.clear()
            sentences.append(' '.join(current_sentence).strip())
            current_sentence = []
            start_of_current_sentence = i + 1
        elif token_text in conjuctions:
            if (contains_verb(current_sentence) and \
                contains_verb(tokens[i+1:])) or len(tokens[i+1:]) == 0:
                for completion, pos in zip(completions, posis):
                    current_sentence.insert(pos, completion)

                completions.clear()
                posis.clear()
                sentences.append(' '.join(current_sentence[:-1]).strip())
                current_sentence = [token_text]
                start_of_current_sentence = i
            elif i > 0 and (contains_verb([tokens[i-1]]) and contains_noun_or_adj(tokens[i+1:])) or (contains_verb([tokens[i+1:]]) and contains_noun_or_adj(tokens[i-1])):
                sentences.append(' '.join(current_sentence[:-1]).strip())
                current_sentence = [token_text]
                start_of_current_sentence = i
        elif i != len(tokens) - 1:
            if len(current_sentence) > 1 and contains_verb(current_sentence) and contains_noun_or_adj(current_sentence) and \
                find_syntagma(tokens[i+1]) is None and tokens[i+1] not in conjuctions:
                    for completion, pos in zip(completions, posis):
                        current_sentence.insert(pos, completion)

                    completions.clear()
                    print(current_sentence)
                    posis.clear()
                    sentences.append(' '.join(current_sentence).strip())
                    current_sentence = []
                    start_of_current_sentence = i + 1
 

    if current_sentence:
        for completion, pos in zip(completions, posis):
                  current_sentence.insert(pos, completion)

        completions.clear()
        posis.clear()
        sentences.append(' '.join(current_sentence).strip())

    return sentences


texts = []

sentences_list = []


sentences = []
for sentence in sentences:
    if is_punctuation_only(sentence) == False:
      sentences.append(sentence)

sentences_list.append(sentences)

def merge_texts(tokens):
  merge_sentences = []
  merge_sentence = []
  company_count = 0
  for token in tokens:
    if contains_company_names(token):
      company_count += 1

    if not token.endswith('.') and not sentence.endswith('!') and not token.endswith('?'):
      if company_count < 2 and merge_sentence:
        
        merge_sentence.append(token)
      elif company_count == 1 and not merge_sentence:
        
        merge_sentence.append(token)
      elif company_count > 1:
        
        merge_sentences.append(' '.join(merge_sentence))
        merge_sentence = [token]
        company_count = 0
        if contains_company_names(token):
          company_count = 1
      elif company_count < 2 and not merge_sentence:
        
        merge_sentence.append(token)

    else:
      merge_sentences.append(token)

    print(merge_sentence)

  if merge_sentence:
    
    merge_sentences.append(' '.join(merge_sentence))
    merge_sentence.clear()

  return merge_sentences

new_sentences = []
for sentence in sentences:
    new_sentences.append(merge_texts(sentences))

def convert_to_float(d):
    if isinstance(d, dict):
        return {k: convert_to_float(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [convert_to_float(x) for x in d]
    elif isinstance(d, np.float32):
        return float(d)
    else:
        return d

def merge_entities(ner_results):
    entities = []
    current_entity = ""
    for sentence_results in ner_results:
        for result in sentence_results:
            if result['word'].startswith("##"):
                current_entity += result['word'][2:]
            else:
                if current_entity:
                    entities.append(current_entity)
                current_entity = result['word']
        if current_entity:
            entities.append(current_entity)
            current_entity = ""
    return list(set(entities))

@app.post("/predict/", response_model=dict)
async def predict(item: Item):
    text = item.text
    sentences = tokenize_sentence(text)

    entity_list = []
    results = []

    for sentence in sentences:
        sentiment_result = sentiment_pipeline(sentence)
        ner_result = ner_pipeline(sentence)
        
        entities = merge_entities([ner_result])
        sentiment_label = sentiment_result[0]['label']
        
        if sentiment_label == 'LABEL_1':
            sentiment = 'nötr'
        elif sentiment_label == 'LABEL_2':
            sentiment = 'olumlu'
        else:
            sentiment = 'olumsuz'
        
        for entity in entities:
            entity_list.append(entity)
            results.append({
                'entity': entity,
                'sentiment': sentiment
            })
        print(text)
        print((list(set(entity_list))))
        print(results)
    return {
        'entity_list': list(set(entity_list)),
        'results': results
        
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)