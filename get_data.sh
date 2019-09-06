#!/bin/bash

# Get datasets
mkdir -p data/licenses_by_year

# MJ business licenses data
curl https://data.colorado.gov/api/views/sqs8-2un5/rows.csv?accessType=DOWNLOAD -o ./data/licensed_mj_biz.csv

# MJ tax revenue by county
curl https://data.colorado.gov/api/views/3sm5-jtur/rows.csv?accessType=DOWNLOAD -o ./data/monthly_tx_revenue.csv

# MJ sales revenue
curl https://data.colorado.gov/api/views/j7a3-jgd3/rows.csv?accessType=DOWNLOAD -o ./data/mj_sales_revenue.csv

# County Population by age and year
curl https://data.colorado.gov/api/views/q5vp-adf3/rows.csv?accessType=DOWNLOAD -o ./data/pop_by_age_and_year.csv

# Personal Income by County
curl https://data.colorado.gov/api/views/2cpa-vbur/rows.csv?accessType=DOWNLOAD -o ./data/personal_income.csv

# Unemployment by geographic area
curl https://data.colorado.gov/api/views/4e3w-qire/rows.csv?accessType=DOWNLOAD -o ./data/unemployment_rates.csv

# Dean Runyon industry report pdf
curl https://industry.colorado.com/sites/default/files/DeanRunyan%20EconomicImpact2017.pdf -o ./data/runyon.pdf

# get yearly licenses
# 2019 to august
curl https://www.colorado.gov/pacific/sites/default/files/190801%20Stores_0.xlsx -o ./data/licenses_by_year/retail_aug_2019.xlsx
curl https://www.colorado.gov/pacific/sites/default/files/190801%20Centers.xlsx -o ./data/licenses_by_year/med_aug_2019.xlsx

# 2018
curl https://www.colorado.gov/pacific/sites/default/files/Stores%2012032018.xlsx -o ./data/licenses_by_year/rec_2018.xlsx
curl https://www.colorado.gov/pacific/sites/default/files/Centers%2012032018.xlsx -o ./data/licenses_by_year/med_2018.xlsx

# 2017
curl https://www.colorado.gov/pacific/sites/default/files/Stores%2011012017_1.xlsx -o ./data/licenses_by_year/rec_2017.xlsx
curl https://www.colorado.gov/pacific/sites/default/files/Centers%2012012017_1.xlsx -o ./data/licenses_by_year/med_2017.xlsx

# 2016
curl https://www.colorado.gov/pacific/sites/default/files/Stores%2012012016.xlsx -o ./data/licenses_by_year/rec_2016.xlsx
curl https://www.colorado.gov/pacific/sites/default/files/Centers%2012012016_1.xlsx -o ./data/licenses_by_year/med_2016.xlsx

# 2015
curl https://www.colorado.gov/pacific/sites/default/files/Stores%2012012015_1.pdf -o ./data/licenses_by_year/rec_2015.pdf
curl https://www.colorado.gov/pacific/sites/default/files/Centers%2012012015_1.pdf -o ./data/licenses_by_year/med_2015.pdf

# 2014
curl https://www.colorado.gov/pacific/sites/default/files/Retail%20Stores%2012012014.pdf -o ./data/licenses_by_year/rec_2014.pdf
curl https://www.colorado.gov/pacific/sites/default/files/Centers%2012012014.pdf -o ./data/licenses_by_year/med_2014.pdf
