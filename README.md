# Hashicorp-get
Tool to get latest or 'x' version of Hashicorps tools

## Description
Downloads and installs x version (or latest version of supported hashicorp tools - see help])

## Usage
```
usage: hashicorp-get [-h] [-y] [-q] [-v] product version installpath

Custom installer for getting latest or specified version of script supported
Hashicorp tools. To see list of supported tools see help below under 'product'
arg.

positional arguments:
  product        Product to install/download. Currently supported :
                 ('terraform,packer,vault')
  version        Version to install (e.g. '0.9.0', 'latest')
  installpath    Path to install tool to (e.g. '/usr/bin/',
                 '/home/someuser/bin/')

optional arguments:
  -h, --help     show this help message and exit
  -y, --yes      Suppress confirmation prompt. If you want total silence use
                 in conjunction with -q
  -q, --quiet    Suppress all messages (quiet mode). Useful for automated
                 installs.
  -v, --version  show program's version number and exit


```

### NOTE: Trailing slash is currently required on "installpath" parameter!

## Initial Setup
You will need the following third party modules, just pip3 install them as needed or use the requirements.txt file as noted below:
- requests: http://docs.python-requests.org/en/master/

Example pip3 install the requirements:
```
pip3 install -r requirements.txt

```

Note: Tested and developed on python 3.6.5 on Linux (Fedora)

### The following settings must be manually preconfigured in 'hashicorp-get.py'

There are also a few other settings you may wish to set. Those are located in the following section in 'hashicorp-get':
```
##########################################
#- Modify the options below as needed
##########################################

 ...settings here...

##########################################
#- END - Do not modify below here!!!
##########################################
```

##### NOTE: This code was tested on Fedora Linux (python 3.6.5) - there are no guarantees it will work on other platforms.  It should but YMMV.


## Thanks
- requests: http://docs.python-requests.org/en/master/

