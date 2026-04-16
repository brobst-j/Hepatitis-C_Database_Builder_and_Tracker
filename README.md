# About

*Originally created by Joshua Brobst (Roux Institute at Northeastern University) and Chloe Manchester (Maine Center for Disease Control)*

This public repository is the source for a program developed by the Roux Institute at Northeastern University and the Maine CDC. Its use is for the cleaning and analysis of HCV cases at the state level for reporting and seeing trends over time.

The original analyis on the clearance cascade contains private information, so this repository was created so that the public (and other epidemiologists) would have access.

# This Repository

## Setup
Included are three Python files that are readily repoducible: merge_records.py (which takes data provided by the CDC and cleans it for analysis), gen_patient_status.py (which takes the output from merge_records and creates status tables for a clearance cascade analysis), and hcv_data_gen.py (which combines the previous two into a single file). However, if you do not have a Python enviroment or even programming experience, the dist .zip file is all you need. All Python files included are for the purpose of extra reproducibility and expansion on this work by other users.

The How To section below goes over how to get the needed source data into the data folder so that the .exe file can run, and how to best use the program provided. This is the recomended method, although hcv_data_gen exists and is reproducible from the command line (provided it is run from a folder that contains /data/source and /data/output) if desired or if changes are needed.

## Data (Folder)

### Source
As later explained in the How-To, the source folder should contain two files added by the user; coded_all_cases_combined.xlsx and coded_all_labs_combined.xlsx. These are needed to generate two the two .csv files used as the new database, which is in turn used to perform the analysis. The expected columns for each file are as follows:


| **Cases**                        |Definition                                
|:----                             |:--                                      |
| Disease                          | Disease status, either acute or chronic |
| HCV_Genotype                     | Genotype test result (genotype)         |
| HCV_Genotype_Detected            | Genotype test result (Y/N)              | 
| HCV_RNA                          | RNA test result                         |
| HCV_RNA_Date                     | RNA test collection date                |
| Investigation_Case_Status	       | Probable/Confirmed Status               |
| Year	                           | Year of Investigation                   |
| Patient_State                    | State, should be Maine                  | 
| Specimen_Collection_Date__HCV_Ge | Genotype test collection date           |
| total_anti_HCV                   | Anti-HCV test result                    |
| total_anti_HCV_Date              | Anti-HCV test collection date           |
| County                           | Patient County                          |
| Patient ID (encoded)             | Encoded Patient Tracker                 |

| **Labs**                         |                                         |
|:----                             |:--                                      |
| Coded_Result                     | Lab Result                              |
| Date_Specimen_Collected          | Specimen collection date                |
| Numeric_Results                  | Lab Result                              |
| Resulted_Test_Name               | Name of test performed                  |
| Test_Result_Code                 | Lab Result                              |
| Text_Result                      | Lab Result                              |
| Reporting_Facility               | Facility that submitted the lab         |
| Patient ID (encoded)             | Encoded Patient Tracker                 |

Additionally, two files are in this folder already. bad_test_names_lower.csv is a required file for the database generation portion, as it is the list of labs that were identified as erroneously identified as associated with HCV. They were kept as a seperate .csv file, rather than harcoded into the program, so that if needed new labs types could easily be addded at the end. The other is population estimate data taken from [census.gov](https://www.census.gov/data/datasets/time-series/demo/popest/2020s-counties-total.html) and [census.gov](https://www.census.gov/data/datasets/time-series/demo/popest/2020s-counties-total.html) and [maine.gov](https://www.maine.gov/dafs/economist/census-information). Other than being combined directly (as they are the same format) and the indexes renamed to remove the state name, no data has been changed or altared in any way from what was available on those websites as of October 24th, 2025. This file is *not* required for any programs to be run, but is kept as a suggestion for what work can be done with the cleaned data.

### Output
Initially, this folder is empty (other than a text file saving its place). Once the program has run, the following files should populate it:

* hcv_labs_long.csv
* hcv_labs_wide.csv
* patient_status_table.csv
* patient_status_table_w_county.csv
* patient_status_now.csv
* value_counts.csv
* value_counts_w_county.csv

The first two files, the long and wide labs, are the output from the first part of the program that are used in the second. The following five are from the second part, and are set up in a way that makes several types of clearance cascade analyses easier.

# How-To
This section is meant to help anyone that needs to reproduce the data and files do so. Specifically, this documents pertains to the contents in the source and dist folders, as well as anythig in data/output.

There are two primary ways this repository can have its two main functions (creating a patientbase and then tracking patient status over time) performed, the simplier way (utilizing /dist running the .exe file) and the more complex way (using the Python files directly). These will be referred to as **Method 1** and **Method 2** respectively. 

## Method 1

### Running
1. Download dist.zip and unzip it to wherever you would like.
2. Move the source data into data/source.
3. Double- or right-click the .exe files to run it.

## Method 2

### Data Sourcing
The data sourcing for this method is the exact same as method 1, however instead of putting the files inside ../dist/data/source, they are instead put in thisrepo/data/source. 

### Running
First, make sure your working directory is the repository folder itself, and then use

`pip install -r ./requirements.txt` 

to install all the dependecies required for this repository, if you don't alerady have them. From there, you can run

`./hcv_data_gen,py`

## Output
For both methods, the output will be in their respective data folder and will be the same either way and they will be in the format of a .csv file

## Updating the .exe
To re-run pyinstaller and create a new .exe file, use the following command:
`pyinstaller --hiddenimport openpyxl  hcv_data_gen.py`

# Contributers

*Lead Student Data Scientist* - Joshua Brobst

Joshua Brobst is a Master's in Data Science student at the Roux Institute, and who studied Applied Mathematics and Statistic at the University of Southern Maine. Even before they had COVID-19 alter the outcome of their last two years of high school, the statistical part of epidemiology has fascinated them. They first started exploring the subject with their school's Science Olympiad team, and did some tracking work with COVID-19. Since then, most of their work has been with mathematics education including their first publication through their alma mater. 

They currently work as a part of UNUM Group's CX Analytics team, although they spent the first two years of the company working in small case renewals underwriting.

*Primary Stakeholer and Epidemologist* - Chloe Manchester