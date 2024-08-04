import pandas as pd
import nltk
from nltk.corpus import stopwords
import string
from jpype import JClass, JString, startJVM, getDefaultJVMPath, shutdownJVM
import os
import re
import emoji

nltk.download('punkt')
nltk.download('stopwords')

# JAVA_HOME ortam değişkenini kontrol et
java_home = os.environ.get('JAVA_HOME')
if not java_home:
    raise EnvironmentError("JAVA_HOME ortam değişkeni ayarlanmamış. Lütfen ayarlayın.")
else:
    print(f"JAVA_HOME is set to: {java_home}")

# JVM yolunu belirle
jvm_path = os.path.join(java_home, 'bin', 'server', 'jvm.dll')

# Zemberek'i kur
startJVM(jvm_path, "-Djava.class.path=zemberek-full.jar", "-ea")
TurkishMorphology = JClass('zemberek.morphology.TurkishMorphology')
TurkishTokenizer = JClass('zemberek.tokenization.TurkishTokenizer')
morphology = TurkishMorphology.createWithDefaults()
tokenizer = TurkishTokenizer.DEFAULT

name = 'dataset for semi-supervise.csv'  # BURAYI DEĞİŞTİR


def find_second_comma(line):
    # İlk virgülün pozisyonunu bul
    first_comma_index = line.find(',')
    if first_comma_index == -1:
        return -1  # Virgül bulunamadı

    # İkinci virgülün pozisyonunu bul
    second_comma_index = line.find(',', first_comma_index + 1)
    return second_comma_index


def clean_punctuation(data):
    metin = data.translate(str.maketrans("", "", string.punctuation))
    return metin


def strip_links(text):
    url_pattern = re.compile(r'http[s]?://\S+|www\.\S+')
    return url_pattern.sub(r'', text)


def remove_emojis(text):
    text = emoji.demojize(text)
    return re.sub(r':[^:]*:', '', text)


with open(f'Datas/{name}', 'r', encoding='utf-8') as file:
    with open(f'Cleaned Datas/{name}', 'w', encoding='utf-8') as file2:
        first = True
        for line in file:
            if first:
                file2.write(f'{line}')
                first = False
                continue
            # Etiketsiz verisetse aktifleştir
            second_comma_index = find_second_comma(line)
            before_second_comma = line[:second_comma_index + 1]
            after_second_comma = line[second_comma_index + 1:-2]

            after_second_comma = strip_links(after_second_comma)
            after_second_comma = remove_emojis(after_second_comma)
            after_second_comma = clean_punctuation(after_second_comma)
            file2.write(f'{before_second_comma}{after_second_comma}{line[-3:]}')

            # Semi-supervise için etiketli verisetini temizle
            """
            before_comma = line[:line.rfind(',')]
            after_comma = line[line.rfind(','):]

            before_comma = strip_links(before_comma)
            before_comma = remove_emojis(before_comma)
            before_comma = clean_punctuation(before_comma)
            file2.write(f'{before_comma}{after_comma}')
            """

# Türkçe stopwords listesini al
stop_words = set(stopwords.words('turkish'))


# Tokenize ve lemmatize fonksiyonu
def tokenize_and_lemmatize(text):
    if not isinstance(text, str):
        text = str(text)
    tokens = tokenizer.tokenize(JString(text))
    results = []
    for token in tokens:
        if not token.getType().name() == 'Punctuation':
            analysis = morphology.analyzeAndDisambiguate(JString(token.getText()))
            best_analysis = analysis.bestAnalysis()
            for result in best_analysis:
                lemmas = result.getLemmas()
                results.append((token.getText(), [str(lemma) for lemma in lemmas]))
    return results


def remove_stopwords(tokens):
    return [word for word in tokens if str(word).lower() not in stop_words]


# POS tagging fonksiyonu
def pos_tagging(text):
    if not isinstance(text, str):
        text = str(text)
    tokens = tokenizer.tokenize(JString(text))
    tagged_tokens = []
    for token in tokens:
        analysis = morphology.analyze(JString(token.getText()))
        if analysis.iterator().hasNext():
            pos = analysis.iterator().next().getPos().name()
            tagged_tokens.append((token.getText(), pos))
        else:
            tagged_tokens.append((token.getText(), 'UNK'))
    return tagged_tokens


# CSV dosyasını oku
df = pd.read_csv(f'Cleaned Datas/{name}')

# 'Content' sütununda null değer içeren satırları kaldır
df = df.dropna(subset=['Content'])

df['lemmatized_content'] = df['Content'].apply(tokenize_and_lemmatize)
df['lemmatized_content'] = df['lemmatized_content'].apply(lambda x: remove_stopwords([lemma for word, lemmas in x for lemma in lemmas]))
df['pos_tagged_content'] = df['Content'].apply(pos_tagging)

# İşlenmiş veri setini kaydet
df.to_csv(f'Outputs/{name}', index=False)

# İşlenmiş veri setini görüntüle
print(df.head())

shutdownJVM()

