# Hashicorp-get
Tool to get latest or 'x' version of Hashicorps tools

## Description
Downloads and installs x version (or latest version of supported hashicorp tools - see help]).  Supports pulling the binary for macos and linux (method use should work on other platforms but NOT tested).  Currently only supports the x86_64 arch.

## Usage
```
usage: hashicorp-get [-h] [-p PATH] [-y] [-q] [-v] product version

Custom installer for getting latest or specified version of script supported
Hashicorp tools. To see list of supported tools see help below under 'product'
arg.

positional arguments:
  product               Product to install/download. Currently supported :
                        ('terraform,packer,vault')
  version               Version to install (e.g. '0.9.0', 'latest')

optional arguments:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path to install tool to (e.g. '/usr/bin/',
                        '/home/someuser/bin/') - if not specified defaults to
                        '~/bin'
  -y, --yes             Suppress confirmation prompt. If you want total
                        silence use in conjunction with -q
  -q, --quiet           Suppress all messages (quiet mode). Useful for
                        automated installs.
  -v, --version         show program's version number and exit

```

Example to pull latest version of packer and install to `~/bin/`:

```
hashicorp-get packer latest
```

Example to pull 0.11.14 version of terraform and install to `/usr/local/bin/`:

```
hashicorp-get terraform 0.11.14 /usr/local/bin/
```


### NOTE: Trailing slash is currently required on "installpath" parameter!


## Initial Setup
You will need the following third party modules, just pip3 install them as needed or use the requirements.txt file as noted below:
- requests: http://docs.python-requests.org/en/master/

Example pip3 install the requirements:
```
pip3 install -r requirements.txt

```

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


## Thanks
- requests: http://docs.python-requests.org/en/master/

