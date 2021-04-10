import os
import urllib3
from urllib.parse import urljoin
from urllib.parse import urlsplit
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
import argparse


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_resonse(url):
    response = requests.get(url, verify=False)
    check_for_redirect(response)
    return response


def download_content(url, filename, folder):
    filename = sanitize_filename(filename)
    filepath = os.path.join(folder, filename)
    response = get_resonse(url)
    with open(f'{filepath}', 'wb') as file:
        file.write(response.content)
    return filepath


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    book_title, book_author = [book_property.strip() for book_property in soup
                               .find('h1')
                               .text
                               .split('::')]
    book_img_src = soup.find('div', class_='bookimage').img['src']
    book_comments = [book_comment.span.text for book_comment in soup
                     .find_all('div', class_='texts')]
    book_genres = [book_genre.text for book_genre in soup
                   .find('span', class_='d_book')
                   .find_all('a')]

    return {'book_title': book_title,
            'book_author': book_author,
            'book_img_src': book_img_src,
            'book_comments': book_comments,
            'book_genres': book_genres}


def check_for_redirect(response):
    if response.url == 'https://tululu.org/':
        raise requests.exceptions.HTTPError(response.url)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s',
                        '--start_id',
                        default='1',
                        type=int,
                        help='С какой страницы скачивать')
    parser.add_argument('-e',
                        '--end_id',
                        default='10',
                        type=int,
                        help='По какую страницу скачивать')
    parser.add_argument('-b',
                        '--book',
                        default='books/',
                        type=str,
                        help='Куда сохранять книги')
    parser.add_argument('-i',
                        '--image',
                        default='images/',
                        type=str,
                        help='Куда сохранять обложки')
    args = parser.parse_args()

    folder_book_name = args.book
    Path(folder_book_name).mkdir(exist_ok=True)
    folder_img_name = args.image
    Path(folder_img_name).mkdir(exist_ok=True)
    page_start_id = args.start_id
    page_end_id = args.end_id

    for page_id in range(page_start_id, page_end_id + 1):
        page_url = f'https://tululu.org/b{page_id}/'
        try:
            response = get_resonse(page_url)
            book_description = parse_book_page(response)

            book_title = book_description['book_title']
            book_author = book_description['book_author']
            book_img_src = book_description['book_img_src']
            book_genres = book_description['book_genres']
            book_comments = book_description['book_comments']

            book_url = f'https://tululu.org/txt.php?id={page_id}'
            book_filename = f'{page_id}.{book_title}.txt'
            book_img_url = urljoin(book_url, book_img_src)
            img_filename = f"{urlsplit(book_img_url).path.split('/')[-1]}"

            book_filepath = download_content(book_url,
                                             book_filename,
                                             folder_book_name)
            img_filepath = download_content(book_img_url,
                                            img_filename,
                                            folder_img_name)

            print('Заголовок: {}\nАвтор: {}\nЖанр: {}\nКомментарии: {}\n'
                  .format(book_title, book_author, book_genres, book_comments))

        except requests.exceptions.HTTPError as redirect_error:
            print(f'{page_url} -> переадресация на {redirect_error}')


if __name__ == '__main__':
    main()
