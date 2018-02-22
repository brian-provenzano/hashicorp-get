#!/usr/bin/python3

"""This simple script is used to grab latest or version of choice of any of the following
Hashicorp tools: terraform;packer;vagrant;vault

This script assumes LINUX AMD64 for simplicity and the fact that is all I use currently on my dev laptop / servers.  
I may update latest for Windows, Mac and ability to choose arch as well.

This attempts to extend this simple "get latest" bash script:
echo "https://releases.hashicorp.com/terraform/$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r -M '.current_version')/terraform_$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r -M '.current_version')_darwin_amd64.zip"

Usage:
hashicorp-get <specific-toolname> <version>

Example - get latest for terraform:
>hashicorp-get terraform latest

Example - get 0.9.0 for terraform:
>hashicorp-get terraform 0.9.0

TODO - support "all" for grabbing all script supported requestedProducts
TODO - support vagrant (download only - do not auto install since it is a rpm/deb/pkg)
TODO - add additional sanity checks
TODO - support various archs
TODO - support checksum checks on the downloaded file
TODO - support check current installed version / option to confirm overwrite/upgrade
TODO - refactor this using classes as an exercise; this grew into serious procedural shit...

BJP 2/21/18"""

# 3rd party : not standard python module (must install via pip); 
# Many linux distros however include this by default
import requests 

import zipfile
import re
import argparse
import os
from distutils.version import LooseVersion
from subprocess import call
from pathlib import Path

# Adjust these vars as needed for your environment
# #########################################################################
# Path to location to place the binaries - include the trailing slash!
HASHICORP_TOOLPATH = "/home/brianprovenzano/bin/"
# API shows all versions for all requestedProducts (entire history)
HASHICORP_ALLRELEASES = "https://releases.hashicorp.com/index.json"
SUPPORTED_ARCH = "amd64"
SUPPORTED_OS = "linux"
SUPPORTED_HASHICORPTOOLS = "terraform,packer,vault"
###########################################################################


def Main():
    """ Main()"""
    parser = argparse.ArgumentParser(prog="hashicorp-get", description="Custom " \
                        "installer for getting latest or specified version of script supported Hashicorp tools. " \
                        "To see list of supported tools see help below under 'product' arg.")
    parser.add_argument("product", type=str, help="Product to install/download.  " \
                        "Currently supported : ('{0}')".format(SUPPORTED_HASHICORPTOOLS))
    parser.add_argument("version", type=str, help="Version to install " \
                        "(e.g. '0.9.0', 'latest')")                   
    parser.add_argument("-y", "--yes", action="store_true", help="suppress confirm " \
                        "(quiet mode). Danger Will Robinson!!")
    parser.add_argument("-v", "--version", action="version", version="1.3")
    # parser.add_argument("-v", "--version", action="version", version="%(prog)s 1.2 (Custom " \
    #                     "installer for getting latest version of Hashicorp supported tools)")
    args = parser.parse_args()
    requestedProductToInstall = args.product.lstrip()
    requestedProductVersion = args.version.lstrip()

    try:
        if (requestedProductToInstall in SUPPORTED_HASHICORPTOOLS):
            if args.yes:
               Run(requestedProductToInstall,HASHICORP_TOOLPATH,requestedProductVersion)
            else:
                answer = input(PromptQuestion(requestedProductToInstall,HASHICORP_TOOLPATH))
                answer = True if answer.lstrip() in ('yes', 'y') else False
                if answer:
                    Run(requestedProductToInstall,HASHICORP_TOOLPATH,requestedProductVersion)
        elif requestedProductToInstall == "all":
            #stub
            raise NotImplementedError("Installing 'all' is not supported currently")
        else:
            raise ValueError("You must enter either '{0}' "
                  "for program to install.  "
                  "Other requestedProduct installs are not supported at this time".format(SUPPORTED_HASHICORPTOOLS))
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


def getVersions(url, requestedProduct, requestedVersion):
    """ get dict of GA release versions with download url (version,url) """
    dictValidReleasesSorted = {}
    response = requests.get(url)
    if response.status_code == 200:
        jsonResult = response.json()
        jVersions = jsonResult[requestedProduct]["versions"]
        dictValidReleases = {}
        # do not want pre-releases; filter them out
        for item in jVersions.items():     
            for build in item[1]["builds"]:
                if (build["os"] == SUPPORTED_OS):
                    if (build["arch"] == SUPPORTED_ARCH):
                        if not (re.search('[a-zA-Z]', item[1]["version"])): 
                            dictValidReleases[item[1]["version"]] = build["url"]

        for key in sorted(dictValidReleases,key=LooseVersion):
            dictValidReleasesSorted[key] = dictValidReleases[key]
    else:
        raise requests.ConnectionError("Server did not return status 200 - returned {0}".format(response.status_code))

    return dictValidReleasesSorted


def Unzip(fullPath):
    """ Unzip file and place in tools path location """
    with zipfile.ZipFile(fullPath, 'r') as zip:
        # TODO - check zipfile contents for file number;
        # should always be 1 binary file unless Hashicorp jumps the shark on the build
        extractedFile = zip.namelist()[0]
        print("3 - Extracting (unzip) -> [{0}] ...".format(extractedFile))
        zip.extractall(HASHICORP_TOOLPATH)
    return extractedFile


def DownloadFile(url, theFile):
    """ Download/save the file from Hashicorp servers """
    # open in binary mode
    with open(theFile, "wb") as file:
        print("1 - Downloading -> [{0}] ...".format(url))
        response = requests.get(url)
        print("2 - Saving -> [{0}] ...".format(theFile))
        file.write(response.content)


def PromptQuestion(requestedProduct, downloadLocation):
    """ Prompt user to confirm and continue"""
    question = "\n {0} selected!!: Are you sure you wish to download the latest " \
               "version of '{0}' to {1} ?: ".format(requestedProduct.upper(), downloadLocation)
    return question


def Run(requestedProduct, toolInstallPath, version):
    fullDownloadURL = ""
    zipfile = ""
    dictValidReleasesSorted = getVersions(HASHICORP_ALLRELEASES,requestedProduct,version)

    if (version == "latest"):
        version = list(dictValidReleasesSorted.keys())[-1] #this sucks, but no dict.first(),last() in python 3

    if(dictValidReleasesSorted.get(version) != None):
        fullDownloadURL = dictValidReleasesSorted.get(version)
        zipfile = fullDownloadURL.split("/")[-1]  
    else:
        raise ValueError("Version specified was not found.  Try again")

    fullPathToZipfile = (toolInstallPath + zipfile)
    DownloadFile(fullDownloadURL,fullPathToZipfile)
    extractedFile = Unzip(fullPathToZipfile)
    # Finally make the file 775
    # TODO - this would need to be updated to support Windows (unix-like systems such as )
    # MacOS, Linux etc are OK with os.chmod() 
    os.chmod((toolInstallPath + extractedFile),0o775)

    #cleanup
    Clean(fullPathToZipfile)
    print("6 - Done!!")

def Clean(theZipFile):
    previousZip = Path(theZipFile)
    if previousZip.is_file():
        previousZip.unlink()
        print("5 - Cleaning up (Deleting zipfile) ...")

if __name__ == '__main__':
    Main()