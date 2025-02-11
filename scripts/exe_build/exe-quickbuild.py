#!/usr/bin/env python3
"""
    FireDM

    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        build an executable (exe) for windows using existing template or download a template from github
        this module can be executed from any operating system e.g. linux, windows, etc..
        to create exe version from scratch use exe_fullbuild.py on windows os
"""

import os
import re
import sys
import json
import shutil

fp = os.path.realpath(os.path.abspath(__file__))
current_folder = os.path.dirname(fp)
project_folder = os.path.dirname(os.path.dirname(current_folder))
sys.path.insert(0,  project_folder)  # for imports to work

from scripts.updatepkg import update_pkg 
from scripts.utils import download, extract, get_pkg_version


APP_NAME = 'FireDM'

build_folder = current_folder
app_folder = os.path.join(build_folder, APP_NAME)

# check for app folder existence, otherwise download latest version from github
if not os.path.isdir(app_folder):
    print('downloading ', APP_NAME)
    data = download('https://api.github.com/repos/firedm/firedm/releases/latest').decode("utf-8")
    # example: "browser_download_url": "https://github.com/firedm/FireDM/releases/download/2021.2.9/FireDM_2021.2.9.zip"
    data = json.loads(data)
    assets = data['assets']

    url = None
    for asset in assets:
        filename = asset.get('name', '')
        if filename.lower().endswith('zip'):  # e.g. FireDM_2021.2.9.zip
            url = asset.get('browser_download_url')
            break

    if url:
        # download file
        z_fp = os.path.join(build_folder, filename)
        if not os.path.isfile(z_fp):
            download(url, z_fp)

        # unzip
        print('extracting, please wait ...')
        extract(z_fp, build_folder)
        os.remove(z_fp)

    else:
        print('Failed to download latest version, download manually '
              'from https://github.com/firedm/FireDM/releases/latest')
        exit(1)

lib_folder = os.path.join(app_folder, 'lib')

# update packages,  ----------------------------------------------------------------------------------------------------
# update firedm pkg
firedm_src = os.path.join(project_folder, 'firedm')
update_pkg('firedm', lib_folder, src_folder=firedm_src, compile=False)

# update other packages
for pkg_name in ['youtube_dl', 'yt_dlp', 'awesometkinter', 'certifi']:
    update_pkg(pkg_name,  lib_folder, compile=False)

# get application version ----------------------------------------------------------------------------------------------
version = get_pkg_version(os.path.join(project_folder, 'firedm', 'version.py'))
        
# create zip file
output_filename = f'{APP_NAME}_{version}'
print(f'prepare final zip filename: {output_filename}.zip')
fname = shutil.make_archive(output_filename, 'zip', base_dir=APP_NAME)

print('Done ...........')
