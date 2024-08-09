import requests
import re
from bs4 import BeautifulSoup
import random
from io import StringIO
from html.parser import HTMLParser


def start():
    print(46 * '-')
    print(10 * '-', 'Youtube Comments Scraper', 10 * '-')
    print(12 * '-', 'Developer: Mert Özek', 12 * '-')
    print(46 * '-', '\n')


start()

API_KEY = ''  # YOUR API KEY HERE


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


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def month_analyzer(raw_time):
    if re.search(r"-0[1-2]-", raw_time) or re.search(r"-12-", raw_time):
        return "Kış"
    elif re.search(r"-0[3-5]-", raw_time):
        return "İlkbahar"
    elif re.search(r"-0[6-8]-", raw_time):
        return "Yaz"
    elif re.search(r"-09-", raw_time) or re.search(r"-1[0-1]-", raw_time):
        return "Sonbahar"
    else:
        print("Error in catching date.")
        return None


def time_analyzer(raw_time):
    if re.search(r"T0[0-6]:", raw_time):  # Between 00:00 and 06:59
        return "Gece"
    elif re.search(r"T0[7-9]:", raw_time) or re.search(r"T1[0-2]:", raw_time):  # Between 07:00 and 12:59
        return "Sabah"
    elif re.search(r"T1[3-8]:", raw_time):  # Between 13:00 and 18:59
        return "Öğlen"
    elif re.search(r"T19:", raw_time) or re.search(r"T2[0-3]:", raw_time):  # Between 19:00 and 23:59
        return "Akşam"
    else:
        print("Error in catching time.")
        return None


def get_all_comments(api_key, video_id):
    url = 'https://www.googleapis.com/youtube/v3/commentThreads'
    params = {
        'part': 'snippet',
        'videoId': video_id,
        'key': api_key,
        'maxResults': 100
    }

    comments_data = []
    while True:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            for item in data['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comment = strip_tags(comment)
                date = item['snippet']['topLevelComment']['snippet']['publishedAt']
                season = month_analyzer(date)
                day = time_analyzer(date)
                comments_data.append([season, day, comment])

            if 'nextPageToken' in data:
                params['pageToken'] = data['nextPageToken']
            else:
                break
        elif response.status_code == 403:
            print("Quota exceeded. Please try again later.")
            break
        else:
            print(f"Error: {response.status_code}")
            break
    return comments_data


def save_to_csv(comments_data, filename):
    with open(f'Datas/{filename}', 'w', newline='', encoding='utf-8') as file:
        file.write('Season,Time,Content,Sentiment\n')
        for comment in comments_data:
            file.write(f'{comment[0]},{comment[1]},{comment[2]},\n')


while True:
    print('\nPress "q" to exit the program.\n\n')

    video_link = input("Please enter the target Youtube video's link: ")

    if video_link == 'q':
        print('Quitting the program.')
        break

    VIDEO_ID = video_link[32:]

    title = get_title(video_link)
    title = sanitize_filename(title)

    comments_data = get_all_comments(API_KEY, VIDEO_ID)
    if comments_data:
        save_to_csv(comments_data, f'{title}.csv')
        print(f"Saved {len(comments_data)} comments to {title}.csv")
    else:
        print("No comments to save.")
