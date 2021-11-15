
## Raid 6 (A proof of concept implementation) 

This repo is for the purpose of CE7490 project 2. Raid 6 configuration is implemented with dummy storage system.

## Install requirements
`pip install -r requirements.txt` 

## Download source code 

*  Download the source code from [here](https://github.com/iReivax1/CE7490_Raid6)

## Quick start

* Running main will run all 7 failure scenerios that raid 6 can handle.
* Raid settings dictionary in main file contains all the variables that can be changed. i.e number of data disks , which disk failed etc.
* stripe size is preferably kept at 4 for most optimal working.

## Logging
All information will be logged into unit_test.log file for further inspection of results.


