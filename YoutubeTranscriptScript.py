from youtube_transcript_api import YouTubeTranscriptApi
import requests
from bs4 import BeautifulSoup
import random
import re


def get_title(youtube_url):
    response = requests.get(youtube_url)

    soup = BeautifulSoup(response.content, 'html.parser')

    title_html = soup.find('title')

    title = title_html.string[:-10]

    return title if title_html is not None else str(random.randint(1000, 10000))


def sanitize_filename(filename):
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return sanitized


def get_transcript(youtube_url):
    id = youtube_url[32:]
    transcript = YouTubeTranscriptApi.get_transcript(id, languages=['tr'])
    transcript_text = [entry['text'] for entry in transcript]
    return transcript_text if transcript_text is not None else ''

while True:
    print('For quitting, press "q".\n')
    url = input("Please paste the youtube url: ")

    if url == 'q':
        break

    title = get_title(url)
    title = sanitize_filename(title)
    transcripts = get_transcript(url)

    with open(f'Datas/{title}.csv', 'w') as file:
        file.write('Content, Sentiment\n')
        for transcript in transcripts:
            file.write(transcript + ',\n')

    print(f'File has been saved successfully as "{title}.csv".\n\n\n')