# Renesas RA flash tool
Flash tool for the built in ROM bootloader for Renesas RA microcontrollers

## Requirements
- Python >= 3.6
- venv

## Local install
*Strongly Recommended to use venv (https://docs.python.org/3/library/venv.html)*
- python -m venv .venv
- source .venv/bin/activate
- pip install -r requirements.txt
- pip install -e .

## Package
WIP: currently in development mode

## Usage
```
usage: raflash [-h] {write,read,erase,info} ...

RA Flasher Tool

options:
  -h, --help            show this help message and exit

Commands:
  {write,read,erase,info}
    write               Write data to flash
    read                Read data from flash
    erase               Erase sectors
    info                Show flasher information
```
Each command has various options. For example, use RAFlasher write -h to see all write options:
```
usage: raflash write [-h] [--start_address START_ADDRESS] [--size SIZE] [--verify] file_name

positional arguments:
  file_name             File name

options:
  -h, --help            show this help message and exit
  --start_address START_ADDRESS
                        Start address
  --size SIZE           Size in bytes
  --verify              Verify after writing

```

## Dev
 - [X] Pull requests
- [X] Issues

## Supported functionality
- [X] Read
- [X] Write
- [X] Erase / sector erase
- [X] Info / area information
- [ ] ID Authentication
- [ ] Baud rate (only for SCI)

## Supported interfaces
- [X] USB
- [ ] SCI

## Supported MCUs
- [X] RA4 (tested)
- [ ] RA2 (should potentially work)
- [ ] RA6 

*Note: only tested on RA4 hardware*

## Resources
https://www.renesas.com/us/en/document/apn/renesas-ra-family-system-specifications-standard-boot-firmware
