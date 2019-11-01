#!/usr/bin/env python3

"""This simple script is used to grab latest or version of choice - see CONSTs below for details

This script assumes AMD64 for simplicity and the fact that is all I use currently on my dev laptop / servers.  
I may later update for Windows, and  choose arch as well.

This attempts to extend this simple "get latest" bash script:
echo "https://releases.hashicorp.com/terraform/$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r -M '.current_version')/terraform_$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r -M '.current_version')_darwin_amd64.zip"

Usage:
hashicorp-get <specific-toolname> <version> <installpath>

Example - get latest for terraform:
>hashicorp-get terraform latest /usr/bin/

Example - get 0.9.0 for terraform:
>hashicorp-get terraform 0.9.0 /home/myuser/bin/

NOTE: trailing slash on installpath is needed!

TODO - support "all" for grabbing all script supported requested_products
TODO - support vagrant (download only - do not auto install since it is a rpm/deb/pkg)
TODO - add additional sanity checks
TODO - support various archs
TODO - support checksum checks on the downloaded file
TODO - support check current installed version / option to confirm overwrite/upgrade

BJP original 2/21/18"""
#third-party
import requests

import zipfile
import re
import platform
import argparse
import os
import sys
from distutils.version import LooseVersion
from subprocess import call
from pathlib import Path

##########################################
#- Modify the options below as needed (but probably shouldnt unless supported
##########################################
# Path to location to place the binaries - include the trailing slash!
# API shows all versions for all requested_products (entire history)
HASHICORP_ALLRELEASES = "https://releases.hashicorp.com/index.json"
SUPPORTED_ARCH = "amd64"
SUPPORTED_HASHICORPTOOLS = "terraform,packer,vault"
##########################################
#- END - Do not modify below here!!!
##########################################


def main():
    """ main()"""
    parser = argparse.ArgumentParser(prog="hashicorp-get", description="Custom " \
                        "installer for getting latest or specified version of script supported Hashicorp tools. " \
                        "To see list of supported tools see help below under 'product' arg.")
    parser.add_argument("product", type=str,  help="Product to install/download.  " \
                        "Currently supported : ('{0}')".format(SUPPORTED_HASHICORPTOOLS))
    parser.add_argument("version", type=str, help="Version to install " \
                        "(e.g. '0.9.0', 'latest')")
    parser.add_argument("-p","--path", type=str, help="Path to install tool to " \
                        "(e.g. '/usr/bin/', '/home/someuser/bin/') - if not specified defaults to '~/bin'")
    parser.add_argument("-y", "--yes", action="store_true", help="Suppress confirmation prompt. " \
                        "If you want total silence use in conjunction with -q")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress all messages " \
                        "(quiet mode). Useful for automated installs.")
    parser.add_argument("-v", "--version", action="version", version="2.0")

    args = parser.parse_args()
    product = args.product.lstrip()
    version = args.version.lstrip()
    if args.path:
        requested_installpath = args.path.strip()
    else:
        requested_installpath = os.path.expanduser("~/bin/")

    try:
        check()
        installpath = requested_installpath if(requested_installpath.endswith("/")) else (requested_installpath + "/")
        if (product in SUPPORTED_HASHICORPTOOLS):
            quiet_mode = False
            if args.quiet:
                quiet_mode = True
            if args.yes:
                valid_versions = get_versions(HASHICORP_ALLRELEASES,product,version)
                run(product,installpath,version, valid_versions, quiet_mode)
            else:
                answer = input(prompt_question(product,installpath, version))
                answer = True if answer.lstrip() in ('yes', 'y') else False
                if answer:
                    valid_versions = get_versions(HASHICORP_ALLRELEASES,product,version)
                    run(product,installpath,version, valid_versions, quiet_mode)
        elif product == "all":
            #stub
            raise NotImplementedError("Installing 'all' is not supported currently")
        else:
            raise ValueError("You must enter either '{0}' "
                  "for program to install.  "
                  "Other product installs are not supported at this time".format(SUPPORTED_HASHICORPTOOLS))
    except ValueError as ve:
        print(str(ve))
    except ConnectionError as ce:
        print("There was an error attempting to reach the Hashicorp servers - REASON [{0}] \n"
              .format(ce))
    except (zipfile.BadZipFile, zipfile.BadZipfile) as bze:
        print("There was an error attempting to decompress the zipfile - REASON [{0}] \n"
              .format(bze))
    except TimeoutError as te:
        print("Request timed out trying to reach Hashicorp servers - REASON [{0}]".format(te))
    except Exception as e:
            print("Unknown error - REASON [{0}]".format(e))


def check():
    """ check requirements """
    if not ((sys.version_info.major == 3) and (sys.version_info.minor >= 6)):
        raise ValueError("You must be using Python 3.6 to use this utility")
    if not ((platform.machine() == "x86_64")):
        raise ValueError("You must be running an x86_64 arch to use this utility")



def get_versions(url, requested_product, requested_version):
    """ get dict of GA release versions with download url (version,url) """
    valid_releasessorted = {}
    response = requests.get(url)
    if response.status_code == 200:
        json_result = response.json()
        versions = json_result[requested_product]["versions"]
        valid_releases = {}
        # do not want pre-releases; filter them out
        for item in versions.items():
            for build in item[1]["builds"]:
                if (build["os"].casefold() == platform.system().casefold()):
                    if (build["arch"] == SUPPORTED_ARCH):
                        if not (re.search('[a-zA-Z]', item[1]["version"])):
                            valid_releases[item[1]["version"]] = build["url"]

        for key in sorted(valid_releases,key=LooseVersion):
            valid_releasessorted[key] = valid_releases[key]
    else:
        raise requests.ConnectionError("Server did not return status 200 - returned {0}".format(response.status_code))

    return valid_releasessorted


def unzip(fullPath,installDirectory, quiet_mode):
    """ unzip file and place in tools path location """
    with zipfile.ZipFile(fullPath, 'r') as zip:
        # TODO - check zipfile contents for file number;
        # should always be 1 binary file unless Hashicorp jumps the shark on the build
        extracted_file = zip.namelist()[0]
        if not quiet_mode:
            print("[-] - Extracting (unzip) -> [{0}] ...".format(extracted_file))
        zip.extractall(installDirectory)
    return extracted_file


def download_file(url, afile, quiet_mode):
    """ Download/save the file from Hashicorp servers """
    # open in binary mode
    with open(afile, "wb") as file:
        if not quiet_mode:
            print("[-] - Downloading -> [{0}] ...".format(url))
        response = requests.get(url)
        if not quiet_mode:
            print("[-] - Saving -> [{0}] ...".format(afile))
        file.write(response.content)


def prompt_question(requested_product, downloadLocation, requested_version):
    """ Prompt user to confirm and continue"""
    question = "\n {0} selected!!: Are you sure you wish to download the {2} " \
               "version of '{0}' to {1} ?: ".format(requested_product.upper(), downloadLocation, requested_version)
    return question


def run(requested_product, install_path, requested_version, valid_versions, quiet_mode):
    full_download = ""
    zipfile = ""

    if (requested_version == "latest"):
        requested_version = list(valid_versions.keys())[-1] #this sucks, but no dict.first(),last() in python 3

    if(valid_versions.get(requested_version) != None):
        full_download = valid_versions.get(requested_version)
        zipfile = full_download.split("/")[-1]
    else:
        raise ValueError("Version specified was not found.  Try again")

    fullpath_to_zipfile = (install_path + zipfile)
    download_file(full_download,fullpath_to_zipfile,quiet_mode)
    extracted_file = unzip(fullpath_to_zipfile,install_path,quiet_mode)
    # TODO - this would need to be updated to support Windows (unix-like systems such as )
    # MacOS, Linux etc are OK with os.chmod()
    os.chmod((install_path + extracted_file),0o755)
    clean(fullpath_to_zipfile,quiet_mode)
    if not quiet_mode:
        print("[-] - Done!!")

def clean(zip_file,quiet_mode):
    """ clean up old zip file, etc after download """
    previous_zip = Path(zip_file)
    if previous_zip.is_file():
        previous_zip.unlink()
        if not quiet_mode:
            print("[-] - cleaning up (Deleting zipfile) -> [{0}]".format(zip_file))

if __name__ == '__main__':
    main()
