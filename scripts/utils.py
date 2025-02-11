"""
    FireDM

    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        utilities to run build scripts.
"""

import os
import sys
import py_compile
import queue
import shutil
import time
import urllib.request
import zipfile
import re
from threading import Thread


def format_size(size, tail=''):
    try:
        size = int(size)
        if size == 0: return '...'
        unit = [x for x in 'bkmgt' if size >= 1024.0 ** 'bkmgt'.index(x)][-1]
        index = 'bkmgt'.index(unit)
        value = round(size / (1024 ** index), 1)
        return f'{value} {unit.upper() + "B" if index else "Bytes"}{tail}'
    except:
        return size


def download(url, fp=None, return_data=True, overwrite=False):
    if not overwrite and fp and os.path.isfile(fp):
        return

    print('download:', url)
    response = urllib.request.urlopen(url)
    chunk_size = 1024 * 100  # 100 kb
    size = response.getheader('content-length')

    if size:
        size = int(size)
        chunk_size = max(size // 100, chunk_size)
    data = b''
    # done = 0

    while True:
        # start = time.time()
        chunk = response.read(chunk_size)
        if chunk:
            data += chunk

            # done += len(chunk)
           
            # elapsed_time = time.time() - start

            # if elapsed_time:
            #     speed = format_size(round(len(chunk) / elapsed_time, 1), tail='/s')
            # else:
            #     speed = ''
            # percent = done * 100 // size
            # bar_length = percent//10
            # progress_bar = f'[{"="*bar_length}{" "*(10-bar_length)}]'
            # progress = f'{progress_bar} {format_size(done)} of {format_size(size)} - {speed}' \
            #            f' - {percent}%' if size else ''
            # print(f'\r{progress}            ', end='')
        else:
            print('')
            break

    if fp:
        if not os.path.isdir(os.path.dirname(fp)):
            os.makedirs(os.path.dirname(fp))
        with open(fp, 'wb') as f:
            f.write(data)

    if return_data:
        return data
    else:
        return True


def zip_extract(z_fp, extract_folder):
    with zipfile.ZipFile(z_fp, 'r') as z:
        z.extractall(path=extract_folder)


def extract(z_fp, extract_folder):
    # use a thread to show some progress while unzipping
    t = Thread(target=zip_extract, args=(z_fp, extract_folder))
    t.start()
    while t.is_alive():
        print('#', end='')
        time.sleep(0.5)
        sys.stdout.flush()

    print('\n')
    print(f'{os.path.basename(z_fp)} extracted to: {extract_folder}')


def delete_folder(folder, verbose=False):
    try:
        shutil.rmtree(folder)
        if verbose:
            print('deleted:', folder)
    except:
        pass


def create_folder(folder_path):
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)


def bkup(pkg_folder):
    # backup old package folder
    print(f'delete previous backup and backup current {pkg_folder}')
    bkup_path = pkg_folder + '_bkup'
    delete_folder(bkup_path)
    try:
        shutil.move(pkg_folder, bkup_path)
    except:
        pass


def compile_file(q):
    while q.qsize():
        file = q.get()

        if file.endswith('.py'):
            try:
                py_compile.compile(file, cfile=file + 'c')
                os.remove(file)
            except Exception as e:
                print('compile_file()> error', e)


def compile_pkg(pkg_folder):
    compile_q = queue.Queue()

    # add all .py file paths to compile_q
    for root, folders, files in os.walk(pkg_folder):
        for fn in files:
            fp = os.path.join(root, fn)
            compile_q.put(fp)

    # create 10 worker threads
    threads = []
    for _ in range(10):
        t = Thread(target=compile_file, args=(compile_q,), daemon=True)
        threads.append(t)
        t.start()

    # watch threads until finished
    while True:
        live_threads = [t for t in threads if t.is_alive()]
        print('#', end='')

        if not live_threads and not compile_q.qsize():
            print()
            break

        time.sleep(0.3)
    print('Finished compiling to .pyc files')
    

def get_pkg_version(fp):
    """parse version number from a file
    it will search for a date based version number
    can be used with FireDM, youtube-dl, and yt_dlp
    version file can be normal string or compiled, .py or .pyc code
    """
    try:
        with open(fp, 'rb') as f:
            text = f.read()
            match = re.search(rb'\d+\.\d+\.\d+', text)
            return match.group().decode('utf-8')
    except:
        return ''

