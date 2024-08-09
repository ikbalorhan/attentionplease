import requests
from bs4 import BeautifulSoup
import time
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36 OPR/38.0.2220.41'}

def get_title(page_url):
    response = requests.get(page_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve page: {page_url}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    title_element = soup.find('h1', id='title')
    title_text = title_element.find('span').text if title_element else 'No Title'

    return title_text


def month_analyzer(raw_time):
    if re.search(r"\.0[1-2]\.", raw_time) or re.search(r"\.12\.", raw_time):
        return "Kış"
    elif re.search(r"\.0[3-5]\.", raw_time):
        return "İlkbahar"
    elif re.search(r"\.0[6-8]\.", raw_time):
        return "Yaz"
    elif re.search(r"\.09\.", raw_time) or re.search(r"\.1[0-1]\.", raw_time):
        return "Sonbahar"
    else:
        print("Error in catching date.")
        return None

def time_analyzer(raw_time):
    if re.search(r"0[0-6]:", raw_time): # Between 00:00 and 06:59
        return "Gece"
    elif re.search(r"0[7-9]:", raw_time) or re.search(r"1[0-2]:", raw_time): # Between 07:00 and 12:59
        return "Sabah"
    elif re.search(r"1[3-8]:", raw_time): # Between 13:00 and 18:59
        return "Öğlen"
    elif re.search(r"19:", raw_time) or re.search(r"2[0-3]:", raw_time): # Between 19:00 and 23:59
        return "Akşam"
    else:
        print("Error in catching time.")
        return None

def scrape_page(page_number):
    page_url = f"{base_url}?p={page_number}"
    response = requests.get(page_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve page: {page_url}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    entries = soup.find_all('div', class_='content')
    entry_texts = [entry.text.strip() for entry in entries]

    dates = soup.find_all('a', class_='entry-date permalink')
    date_texts = [date.text.strip() for date in dates]

    # Add a delay to mimic human behavior
    time.sleep(random.randint(2, 5))

    return entry_texts, date_texts

def save_to_csv(data, filename):
    with open(f'Datas/{filename}', mode='w', newline='', encoding='utf-8') as file:
        file.write('Season,Time,Content,Sentiment\n')
        for entry in data:
            file.write(f"{entry[0]},{entry[1]},{entry[2]},\n")


print(53*'-')
print(10*'-', 'Ekşi Sözlük Data Scraper Script', 10*'-')
print(15*'-', 'Developer: Mert Özek', 16*'-')
print(53*'-', '\n')

while True:

    scraped_data = []
    entry_count = 0
    max_entries = 15000  # Adjust this number based on your needs
    max_workers = 10

    print('Correct url: "https://eksisozluk.com/entry"\nWrong url: "https://eksisozluk.com/entry?p=1", "https://eksisozluk.com/entry?p=5"\n')
    print('Press "q" to quit.\n')
    base_url = input('Please enter the Ekşi Sözlük url: ')

    if base_url == 'q':
        print('Quitting the program.')
        break
    elif 'eksisozluk.com' not in base_url:
        print('\nWrong url. Please enter a valid eksisozluk url.\n')
        continue

    try:
        last_page_text = input('Please enter the page amount: ')
        if last_page_text == 'q':
            print('Quitting the program.')
            break

        last_page = int(last_page_text)
    except Exception as e:
        print('Please enter an integer value.')
        continue

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_page, page_number): page_number for page_number in
                   range(1, int(last_page) + 1)}

        for future in as_completed(futures):
            page_number = futures[future]
            try:
                result = future.result()
                if result is None:
                    break
                elif result:
                        entries, dates = result
                        for entry, date in zip(entries, dates):
                            season = month_analyzer(date)
                            time_date = time_analyzer(date)
                            scraped_data.append([season, time_date, entry])
                            entry_count += 1

                            print(f'Entries scrapped: {entry_count}', end='\r')

                            if entry_count >= max_entries:
                                break
            except Exception as e:
                print(f"Exception for page {page_number}: {e}")

            if entry_count >= max_entries:
                break

    title = get_title(base_url)

    # Save the scraped data to a CSV file
    save_to_csv(scraped_data, f'{title}.csv')

    print(f"Scraping completed. Total entries scraped: {entry_count}\n\n")