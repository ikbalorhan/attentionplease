import pandas as pd

name = 'magaza_yorumlari_duygu_analizi.csv'


def preprocess_sentiment(sentiment):
    if sentiment == 'Olumlu':
        return '1'
    elif sentiment == 'Olumsuz':
        return '0'
    elif sentiment == 'Tarafsız' or sentiment == 'Tarafsiz':
        return '2'


df = pd.read_csv(f'Datas/{name}')

# df['Duygu'] = df['Duygu'].apply(preprocess_sentiment)
df['Durum'] = df['Durum'].apply(preprocess_sentiment)

df.to_csv(f'Outputs/{name}', index=False)

print(df.head())
