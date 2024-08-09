import string
import re
import emoji

name = 'turkcell superonline.csv'  # BURAYI DEĞİŞTİR

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

            # Etiketsiz verisetiyse aktifleştir
            second_comma_index = find_second_comma(line)
            before_second_comma = line[:second_comma_index + 1]
            after_second_comma = line[second_comma_index + 1:-2]

            after_second_comma = strip_links(after_second_comma)
            after_second_comma = remove_emojis(after_second_comma)
            after_second_comma = clean_punctuation(after_second_comma)

            before_second_comma = before_second_comma.lower()
            after_second_comma = after_second_comma.lower()
            file2.write(f'{before_second_comma}{after_second_comma}{line[-2:]}')

            # Semi-supervise için etiketli verisetini temizle
            """
            before_comma = line[:line.rfind(',')]
            after_comma = line[line.rfind(','):]

            before_comma = strip_links(before_comma)
            before_comma = remove_emojis(before_comma)
            before_comma = clean_punctuation(before_comma)
            file2.write(f'{before_comma}{after_comma}')
            """