#!/usr/bin/python3

"""This simple script is used to grab latest or version of choice - see CONSTs below for details

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
TODO - refactor this using classes as an exercise; this grew into a serious procedural mess

BJP original 2/21/18"""

# Check : This seems cheeseball but I don't know of another way to do it in scope
# 3rd party : not standard python module (must install via pip); 
# Many linux distros however include this by default
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

# Adjust these vars as needed for your environment
# #########################################################################
# Path to location to place the binaries - include the trailing slash!
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
    parser.add_argument("installpath", type=str, help="Path to install tool to " \
                        "(e.g. '/usr/bin', '/home/someuser/bin')")                     
    parser.add_argument("-y", "--yes", action="store_true", help="Suppress confirmation prompt. " \
                        "If you want total silence use in conjunction with -q")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress all messages " \
                        "(quiet mode). Useful for automated installs.")
    parser.add_argument("-v", "--version", action="version", version="1.6")

    args = parser.parse_args()
    requestedProductToInstall = args.product.lstrip()
    requestedProductVersion = args.version.lstrip()
    requestedInstallPath = args.installpath.strip()

    try:
        CheckCompat()
        if (requestedProductToInstall in SUPPORTED_HASHICORPTOOLS):
            quietMode = False
            if args.quiet:
                quietMode = True
            if args.yes:
               Run(requestedProductToInstall,requestedInstallPath,requestedProductVersion,quietMode)
            else:
                answer = input(PromptQuestion(requestedProductToInstall,requestedInstallPath))
                answer = True if answer.lstrip() in ('yes', 'y') else False
                if answer:
                    Run(requestedProductToInstall,requestedInstallPath,requestedProductVersion,quietMode)
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


def CheckCompat():
    """ check requirements """
    if not ((sys.version_info.major == 3) and (sys.version_info.minor >= 6)):
        raise ValueError("You must be using Python 3.6 to use this utility")
    if not ((platform.machine() == "x86_64") and (platform.system() == "Linux")):
        raise ValueError("You must be running Linux x86_64 to use this utility")


def GetVersions(url, requestedProduct, requestedVersion):
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


def Unzip(fullPath,installDirectory, quietMode):
    """ Unzip file and place in tools path location """
    with zipfile.ZipFile(fullPath, 'r') as zip:
        # TODO - check zipfile contents for file number;
        # should always be 1 binary file unless Hashicorp jumps the shark on the build
        extractedFile = zip.namelist()[0]
        if not quietMode:
            print("[-] - Extracting (unzip) -> [{0}] ...".format(extractedFile))
        zip.extractall(installDirectory)
    return extractedFile


def DownloadFile(url, theFile, quietMode):
    """ Download/save the file from Hashicorp servers """
    # open in binary mode
    with open(theFile, "wb") as file:
        if not quietMode:
            print("[-] - Downloading -> [{0}] ...".format(url))
        response = requests.get(url)
        if not quietMode:
            print("[-] - Saving -> [{0}] ...".format(theFile))
        file.write(response.content)


def PromptQuestion(requestedProduct, downloadLocation):
    """ Prompt user to confirm and continue"""
    question = "\n {0} selected!!: Are you sure you wish to download the latest " \
               "version of '{0}' to {1} ?: ".format(requestedProduct.upper(), downloadLocation)
    return question


def Run(requestedProduct, toolInstallPath, version, quietMode):
    fullDownloadURL = ""
    zipfile = ""
    dictValidReleasesSorted = GetVersions(HASHICORP_ALLRELEASES,requestedProduct,version)

    if (version == "latest"):
        version = list(dictValidReleasesSorted.keys())[-1] #this sucks, but no dict.first(),last() in python 3

    if(dictValidReleasesSorted.get(version) != None):
        fullDownloadURL = dictValidReleasesSorted.get(version)
        zipfile = fullDownloadURL.split("/")[-1]  
    else:
        raise ValueError("Version specified was not found.  Try again")

    fullPathToZipfile = (toolInstallPath + zipfile)
    DownloadFile(fullDownloadURL,fullPathToZipfile,quietMode)
    extractedFile = Unzip(fullPathToZipfile,toolInstallPath,quietMode)
    # Finally make the file 775
    # TODO - this would need to be updated to support Windows (unix-like systems such as )
    # MacOS, Linux etc are OK with os.chmod() 
    os.chmod((toolInstallPath + extractedFile),0o775)

    #cleanup
    Clean(fullPathToZipfile,quietMode)
    if not quietMode:
        print("[-] - Done!!")

def Clean(theZipFile,quietMode):
    """ Clean up old zip file, etc after download """
    previousZip = Path(theZipFile)
    if previousZip.is_file():
        previousZip.unlink()
        if not quietMode:
            print("[-] - Cleaning up (Deleting zipfile) -> [{0}]".format(theZipFile))

if __name__ == '__main__':
    Main()