import csv
import json
import os
import threading
from datetime import datetime

import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from webdriver_manager.chrome import ChromeDriverManager

BASE_PATH = '' # Enter path of base folder containing KBAs folder
KBA_DIRECTORY = BASE_PATH + '/KBAs'
KBA_CSV = BASE_PATH + '/CEC pending.csv'
COOKIE = ''
TODAY_DATE = datetime.now().strftime('%Y%m%d')


def save_pdfs_from_urls(urls):
    chrome_options = Options()
    chrome_options.add_argument('--kiosk-printing')
    prefs = {
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'plugins.always_open_pdf_externally': True,
        'printing.print_preview_sticky_settings.appState': json.dumps({
            'recentDestinations': [{
                'id': 'Save as PDF',
                'origin': 'local',
                'account': ''
            }],
            'selectedDestinationId': 'Save as PDF',
            'version': 2
        })
    }
    chrome_options.add_experimental_option('prefs', prefs)
    # svc = Service(executable_path=binary_path)
    # driver = webdriver.Chrome(service=svc, options=chrome_options)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    try:
        for url in urls:
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            driver.execute_script('window.print();')
            time.sleep(5)  # Adjust this time as needed
            print(f'PDF saved for {url}')
    except Exception as e:
        print(f'An error occurred: {str(e)}')
    finally:
        driver.quit()


def get_note_print_urls(base_url, api_key, note_ids):
    print_urls = []
    headers = {
        # Add cookie from Network tab of any note URL below. Don't refresh the page till script is running as cookie
        # gets updated on page refresh. If page is refreshed, change the cookie here and rerun the script.
        'Cookie': COOKIE
    }
    for note_id in note_ids:
        url = f'{base_url}?q={note_id}&isFromCoveo=false'
        response = requests.get(url, headers=headers)
        try:
            print_url = response.json()['Response']['SAPNote']['Actions']['Print']['url']
            print_urls.append(print_url)
            print(f'Print URL fetched for note {note_id}')
        except KeyError:
            print(f'Error fetching URL for note ID {note_id}')
    return print_urls


def get_note_ids_from_csv(file_path, count):
    note_ids = []
    try:
        with open(file_path, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader, None)  # Skip header row
            for row in csv_reader:
                if row:
                    note_id = row[1].strip()
                    downloaded = row[8].strip().lower() == 'true'
                    if note_id and not downloaded:
                        note_ids.append(note_id)
                    if len(note_ids) == count:
                        return note_ids
    except FileNotFoundError:
        print(f'Error: The file {file_path} was not found.')
    except csv.Error as e:
        print(f'Error reading CSV file: {e}')
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
    return note_ids


def update_downloaded_status(file_path, note_ids):
    updated_rows = []
    try:
        with open(file_path, 'r', newline='') as csvfile:
            csv_reader = list(csv.reader(csvfile))
            for row in csv_reader:
                if row[1] in note_ids:
                    row[8] = 'True'
                updated_rows.append(row)
        with open(file_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerows(updated_rows)
    except Exception as e:
        print(f'Error updating CSV: {e}')


def process_chunk(base_url, api_key, note_ids):
    print_urls = get_note_print_urls(base_url, api_key, note_ids)
    save_pdfs_from_urls(print_urls)


def update_csv_based_on_file_existence(csv_path, download_dir):
    updated_rows = []
    try:
        with open(csv_path, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row_number, row in enumerate(csv_reader, start=1):
                if row[8].strip().lower() == 'true':
                    note_id = row[1].strip()
                    filename = f'{note_id}_E_{TODAY_DATE}.pdf'
                    file_path = os.path.join(download_dir, filename)
                    if not os.path.exists(file_path):
                        row[8] = 'False'
                        print(f'{row_number} : {note_id}')
                updated_rows.append(row)

        with open(csv_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerows(updated_rows)
    except Exception as e:
        print(f'Error updating CSV: {e}')


def delete_duplicate_files(directory):
    for filename in os.listdir(directory):
        if '(' in filename or ')' in filename:
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                print(f'Deleted file: {file_path}')
            except Exception as e:
                print(f'Error deleting file {file_path}: {e}')


def sanitize():
    update_csv_based_on_file_existence(KBA_CSV, KBA_DIRECTORY)
    delete_duplicate_files(KBA_DIRECTORY)


def rename():
    for filename in os.listdir(KBA_DIRECTORY):
        if filename.endswith('.pdf'):
            parts = filename.split('.pdf')
            base_name = parts[0]
            parts = base_name.split('_')
            new_filename = f'{parts[0]}.pdf'
            old_file = os.path.join(KBA_DIRECTORY, filename)
            new_file = os.path.join(KBA_DIRECTORY, new_filename)
            if old_file != new_file:
                os.rename(old_file, new_file)
                print(f'Renamed: {old_file} to {new_file}')


def main():
    if not COOKIE:
        print('''COOKIE NOT SET! SET IT FROM HEADERS OF NOTE DETAILS API:
https://me.sap.com/backend/raw/sapnotes/Detail?q={noteId}&isFromCoveo={bool}''')
        return
    batch_size, iterations, thread_chunk_size = 120, 12, 20
    base_url = 'https://me.sap.com/backend/raw/sapnotes/Detail'
    api_key = ''
    note_ids = get_note_ids_from_csv(KBA_CSV, batch_size)
    while len(note_ids) > 0 and iterations > 0:
        print(
            f'-------------------------------------------------------{iterations} ITERATIONS REMAINING!-------------------------------------------------------\n')
        note_id_chunks = [note_ids[i:i + thread_chunk_size] for i in range(0, len(note_ids), thread_chunk_size)]
        threads = []
        for chunk in note_id_chunks:
            t = threading.Thread(target=process_chunk, args=(base_url, api_key, chunk))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        update_downloaded_status(KBA_CSV, note_ids)
        note_ids = get_note_ids_from_csv(KBA_CSV, batch_size)
        iterations -= 1


# Run below methods in order, keep only one method uncommented at once.
# main()
# sanitize()
# rename()

# Instructions: Install below libraries
# pip install requests
# pip install chromedriver-py
# pip install selenium
# pip install webdriver_manager


def update_downloaded_status(csv_file, directory):
    df = pd.read_csv(csv_file)
    for index, row in df.iterrows():
        file_number = row['Number']
        file_name = f"{file_number}.pdf"  # Assuming the file extension is .pdf
        file_path = os.path.join(directory, file_name)
        if os.path.isfile(file_path):
            df.at[index, 'Downloaded'] = True
        else:
            df.at[index, 'Downloaded'] = ""  # Leave the column empty
            print(f"File not found: {file_name}")
    df.to_csv(csv_file, index=False)


# update_downloaded_status(KBA_CSV, KBA_DIRECTORY)