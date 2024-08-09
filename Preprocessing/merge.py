import pandas as pd
import os

names = os.listdir('Cleaned Datas/')
df = pd.DataFrame()

for name in names:
    temp_df = pd.read_csv(f'Cleaned Datas/{name}')
    df = pd.concat([df, temp_df], ignore_index=True)

df.drop(axis=1, columns=['Season', 'Time'], inplace=True)
df.dropna(subset=['Content'], inplace=True)

df.to_csv('Outputs/merge.csv', index=False)