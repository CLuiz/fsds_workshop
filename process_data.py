import os
from glob import glob

from bs4 import BeautifulSoup
from camelot import read_pdf
import numpy as np
import pandas as pd
import requests


def load_csvs(data_dir):
    csv_files = glob(os.path.join(data_dir, '*.csv'))
    df_names = [os.path.splitext(os.path.split(x)[-1])[0] + '_df' for x in csv_files]
    dfs = [pd.read_csv(csv, index_col=False, low_memory=False) for csv in csv_files]
    return {df_name: df for df_name, df in zip(df_names, dfs)}

def prep_revenue_df(df, cash_cols, categorical_cols=False):
    # TODO categorical handling not working properly,  Trace through.
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    # try to send all values to lowercase
    # this will fail due to df having mixed dtypes

    # fix month and year iteratively
    df['month'] = df['month'].astype(str).str.pad(2, 'left', '0')
    df['year'] = df['year'].astype(str)
    # If the slash isn't added in the middle it sets the day to 20 rather than one
    df['date'] = pd.to_datetime(df['month'] + '/'+ df['year'], format='%m/%Y')
    df.drop(['month', 'year'], axis=1, inplace=True)

    # set sales columns as type int. Will need to handle missing values
    # first try without fixing nulls
    #df[['med_sales', 'rec_sales']] = df[['med_sales', 'rec_sales']].astype(int)

    # now look at value counts and do .isnull().sum() to see how many missing

    # fix using fill na and cast as int
    df[cash_cols] = df[cash_cols].fillna(0).astype(int)

    # reference data source documentation to understand codes
    # look at number of null susing Series.isnull().sum()
    # look at value counts of rec_blank_code and med_blacnk_code
    # talk about categoricla data
    # talk about pd.get_dummies vs label encoding

    # not thinking I am going to need these columns.  #TODO delete or keep this part of the work?
    # fill as needed.  One hot encode? or wait for model prep?
    #med_dummies = pd.get_dummies(df['med_blank_code'], prefix='med')
    #rec_dummies = pd.get_dummies(df['rec_blank_code'], prefix='rec')
    if categorical_cols:
        dummy_dfs = []
        for col in categorical_cols:
            dummies = pd.get_dummies(df[col], prefix=col)
            dummy_dfs.append(dummies)

        # drop columns we made dummies from
        df.drop(categorical_cols, axis=1, inplace=True)
        # return merged dataframes
        #return pd.concat([df, rec_dummies, med_dummies], axis=1)
        dummy_dfs.insert(0, df)
        return pd.concat(dummy_dfs, axis=1)
    else:
        df.drop(['med_blank_code', 'rec_blank_code'], axis=1, inplace=True)
        return df

def join_dfs(dfs):
    return dfs

def read_license_files(data_dir='data/licenses_by_year'):
    # TODO parameterize this function
    excel_files = glob(os.path.join(data_dir, '*.xlsx'))
    keys = [os.path.split(x)[-1].split('.')[0] for x in excel_files]
    dfs = {}

    for key, val in zip(keys, excel_files):
        tmp_df = pd.read_excel(val, header=1)
        tmp_df['year'] = key[-4:]
        try:
            tmp_df.drop('License Type ', axis=1, inplace=True)
        except:
            pass
        cols = ['licensee', 'dba', 'license_num', 'address', 'city', 'zip', 'year']
        tmp_df.columns = cols
        dfs[key] = tmp_df

    # now lets read in the pdfs with camelot's read_pdf function
    pdf_dfs = {}
    pdfs = glob(os.path.join(data_dir, '*.pdf'))
    keys = [os.path.split(x)[-1].split('.')[0] for x in pdfs]
    for key, pdf in zip(keys, pdfs):
        tmp_df = read_pdf(pdf)[0].df
        tmp_df['year'] = key[-4:]
        pdf_dfs[key] = tmp_df
    # All of these files read in differently. Clean up, maintaining year and zip
    # at least.
    cols = pdf_dfs['med_2014'].iloc[1].str.lower().tolist()
    cols = ['year' if col == '2014' else col for col in cols]
    pdf_dfs['med_2014'].columns = cols
    pdf_dfs['med_2014'] = pdf_dfs['med_2014'][2:]
    pdf_dfs['rec_2014'].columns = cols
    pdf_dfs['rec_2014'] = pdf_dfs['rec_2014'][1:]

    # for 2015 just get zip and year
    rec_zips_2015 = pdf_dfs['rec_2015'][0].str.extract(r'(?P<zip>\d{5})')
    rec_zips_2015['year'] = 2015

    med_zips_2015 = pdf_dfs['med_2015'][0].str.extract(r'(?P<zip>\d{5})')
    med_zips_2015['year'] = 2015

    pdf_dfs['rec_2015']= rec_zips_2015
    pdf_dfs['med_2015']= med_zips_2015
    dfs.update(pdf_dfs)
    return pd.concat(dfs, sort=False)


def get_zips(source='https://www.zipcodestogo.com/Colorado/'):
    zips = pd.read_html(source, flavor='bs4', skiprows=3)
    zips = zips[0].iloc[:, :2]
    zips.columns = ['zip', 'county']
    return zips


def get_shops_by_year(license_file_dir='data/licenses_by_year/'):
    # now need to map zips to countys and add to the master dataset
    shops_by_year = read_license_files(license_file_dir)
    shops_by_year = (
        shops_by_year.
        reset_index().
        rename(columns={'level_0': 'source'}).
        drop('level_1', axis=1))
    shops_by_year['source'] = shops_by_year['source'].str[:3]
    zips = get_zips()
    zip_shops = pd.merge(shops_by_year, zips, on='zip')
    # there are some errors with how th zip codes are entered and we didn't get
    # them all. I'll leave this as an opportunity to improve on the processing
    # pipeline

    # ok, lets take a look and join to our dataset
    # hmm, we have some weirdness here.  There are now three prefixes - med, rec, and 'ret'
    # use a set comp to look at the index vals
    # {x[0] for x in shops_by_year.index}
    # ah, inconcistent naming on my part.  We can just rename for now.
    zip_shops['source'] = ['rec' if x == 'ret' else x for x in zip_shops['source']
    return zip_shops


def get_dataset():
    # Read csvs into dataframes
    dfs = load_csvs('data/')
    # Look at data structure of each df
    df = dfs['mj_sales_revenue_df']
    # head, tail, describe, info, shape, correlation, covariance, drop_duplicates, drop_na
    # columns, dtypes
    # Begin cleaning things up
    # Talk about vectorized operations
    # Lower case and remove spaces from headers
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    # try to send all values to lowercase
    # this will fail due to df having mixed dtypes
    #df = df.applymap(str.lower)
    # look at dtypes with
    # df.dtypes
    # fix month and year iteratively
    df['month'] = df['month'].astype(str).str.pad(2, 'left', '0')
    df['year'] = df['year'].astype(str)
    # If the slash isn't added in the middle it sets the day to 20 rather than one
    df['date'] = pd.to_datetime(df['month'] + '/'+ df['year'], format='%m/%Y')

    # set sales columns as type int. Will need to handle missing values
    # first try without fixing nulls
    #df[['med_sales', 'rec_sales']] = df[['med_sales', 'rec_sales']].astype(int)

    # now look at value counts and do .isnull().sum() to see how many missing

    # fix using fill na and cast as int
    df[['med_sales', 'rec_sales']] = df[['med_sales', 'rec_sales']].fillna(0).astype(int)

    # reference data source documentation to understand codes
    # look at number of null susing Series.isnull().sum()
    # look at value counts of rec_blank_code and med_blacnk_code
    # talk about categorical data
    # talk about pd.get_dummies vs label encoding

    # fill as needed.  One hot encode? or wait for model prep?
    med_dummies = pd.get_dummies(df['med_blank_code'], prefix='med')
    rec_dummies = pd.get_dummies(df['rec_blank_code'], prefix='red')
    df = pd.concat([df, rec_dummies, med_dummies], axis=1)

    # ok, we have our first df set. Typically I would drop the old columns, but lets leave them in for now.
    # Now we can process the other similar dataset using the same process. Try to abstract as muchas possible here - too much ds work is bound to the dataset.  We want our processing scripts to be as flexible as possible for re-use.
    # TODO Class takes some time to process the the other simialr dataframe (dfs[3])
    # after time I show the abstracted script and let those who haven't finished process with that.

    # TODO remove categorical column handling?
    processed_df1 = prep_revenue_df(dfs['mj_sales_revenue_df'], ['med_sales', 'rec_sales'], ['med_blank_code', 'rec_blank_code'])
    processed_df2 = prep_revenue_df(dfs['monthly_tx_revenue_df'], ['med_tax_rev', 'rec_tax_rev'], ['med_blank_code', 'rec_blank_code'])
    #processed_df1 = prep_revenue_df(dfs['mj_sales_revenue_df'], ['med_sales', 'rec_sales'])
    #processed_df2 = prep_revenue_df(dfs['monthly_tx_revenue_df'], ['med_tax_rev', 'rec_tax_rev'])
    processed_df2.drop(['med_remainderofstate_counties',  'rec_remainderofstate_counties'], axis=1, inplace=True)
    # join first two dfs
    # lots of ways to combine dataframes.  Merge, jon, concat (we allready saw)
    # here, we wnat to use merge, or somethign with similar options.
    merged = pd.merge(processed_df1, processed_df2, on=['county', 'date'])
    # after merge look at shape of all three datasets... we have a problem
    # look at counts of items we merged on counties and dates
    # Looks like all of the counties are not there....could it be that
        # a missing row mean no tax revenue at that time?
        # a missing row means nothing - we just don't have the date
        # a missing row means somethign else.
        # What should we do?  ....
    # since we don't know the meaning yet, lets keep all the rows and figure it out
    # when we know more

    merged = pd.merge(processed_df1, processed_df2, on=['county', 'date'], how='left')

    pop_by_age_df = dfs['pop_by_age_and_year_df']
    # now lets take a look at the dateset of ages in each county.  This dataset is broken
    # up by single years, which is less than ideal for our purposes.  Lets break this up into buckets that better fit.
    # pandas has several functions for the conversion of continuous variables to categorical
    # cut and qcut
    # we are going to use cut to create a new column with labels for each of of age buckets,
    # and then one hot encode them using pd.get_dummies
    # TODO crape this data from the above url
    # but, what ranges should we use?
    #url ='https://www.statista.com/statistics/737849/share-americans-age-group-smokes-marijuana/'
    #text_response = requests.get(url)
    usage_by_age_dict = {'18-29': .24, '30-49': .13, '50-64': .11, '65+': .06}
    # using those values we end up with 5 buckets. Under 18, 18-19, 30-49, 50-64, and 65 +
    # Now, lets cut our values.
    # first, lets add an under 18 bucket to our dictionary keys to create labels
    labels = list(usage_by_age_dict.keys())
    labels.insert(0, '<18')
    #pop_by_age_df['binned_age'] = pd.cut(
    #    pop_by_age_df['age'], [0,18, 29, 49, 65, 120], labels=labels)
    # look at df and realize that 0's ar Nan.  woops...
    pop_by_age_df['binned_age'] = pd.cut(
        pop_by_age_df['age'], [0,18, 29, 49, 65, 120], labels=labels, include_lowest=True)
    # ok, nans fixed.  Now lets group by year, county, and binned_age
    grouped = pop_by_age_df.groupby(['county', 'year', 'binned_age'])[
        'malePopulation', 'femalePopulation', 'totalPopulation'].sum()
    # Look at grouped, ok now we have a multi index, we can pass the arg
    # as_index=False to get back what we want.
    grouped = pop_by_age_df.groupby(['county', 'year', 'binned_age'], as_index=False)[
        'malePopulation', 'femalePopulation', 'totalPopulation'].sum()
    total_pop_by_year = grouped.groupby(
        ['county', 'year'], as_index=False)['totalPopulation'].sum()
    # rename total population column before merging
    cols = total_pop_by_year.columns.tolist()
    cols = cols[:-1] + ['global_total_pop']
    total_pop_by_year.columns = cols

    gmerged = pd.merge(grouped, total_pop_by_year, on=['county', 'year'])
    # next, lets look at how many expected users there are, given the stats we found on the statista site
    # for now, we will ignore that usage chanes over time, and assume that
    # usage would be at current levels in the past, had the laws been different.
    # add entry for under 18
    usage_by_age_dict['<18'] = 0
    # this step should be eliminated
    gmerged['consumer_fraction'] = gmerged['binned_age'].apply(usage_by_age_dict.get)
    gmerged['expected_consumers'] = [
        x * y for x, y in zip(gmerged['consumer_fraction'], gmerged['totalPopulation'])]

    expected_consumers_by_year = gmerged.groupby(
        ['county', 'year'], as_index=False)['expected_consumers'].sum()
    expected_consumers_by_year['expected_consumers'] = expected_consumers_by_year['expected_consumers'].astype(int)

    # plan to go back to calculate the total expected users at +1, +3, +5 , 10 years in the future. #### Don't need to! estiamted pop into future is alread calculated
    # could go back and adjust by usage information across genders

    # ok, now lets reshape the data to have one row per county, per year.
    # We can do this using pandas pivot_table method and some massaging of the multi indices
    # after pivoting.
    # first lets look at what a simple picvot will do

    # ok, so what we need is pivot to index of county and year, the columns to by binned_age
    # and the values are everything except global population, which we can back later
    #
    age_pivot = pd.pivot_table(gmerged, index=['county', 'year'], values=['expected_consumers', 'malePopulation', 'femalePopulation',
        'totalPopulation', 'consumer_fraction'], columns='binned_age')
    # age_pivot.head()
    # now we can see some weirdness here.  There is a both a row and columnar multi-indx that needs to be fixed.
    # The row level is easy, we have done this before. The columns are different though.
    # The easy way to do this (and end up with interpretable headers) is to rename the columns to a single str including both pieces of the index. This is how that can be done
    # first we change the column type from categorical to string as so
    age_pivot = age_pivot.rename(columns=str)
    # next we can join the levels of the column names using a list comprehension
    age_pivot.columns = ['_'.join(col) for col in age_pivot.columns]
    # age_pivot.head()
    # now drop the county/year multi-index
    age_pivot.reset_index(inplace=True)
    # age_pivot.head()
    # now to add back the global popluation numbers
    global_pops = gmerged[['county', 'year', 'global_total_pop']].drop_duplicates()
    age_df = pd.merge(
        age_pivot, global_pops,
        how='left', on=['county', 'year'])
    # and, lets look at the finished product
    # age_df.head()

    # next we are going to look at income across the counties  we'll bound by 1990 and take a look
    # by county. The state and us info is here as well, so we will read those into their own dataframes and
    # use for comparision or feature engineering later.
    income_df = dfs['personal_income_df']
    # same process here - look at columns, info, describe
    # income_df.columns
    # income_df.info(), income_df.describe()
    # We see there are some columns here that are redundant and/or not necessary for what we are doing
    # lets drop all of them with a single value, or redundant information
    # income_df.nunique() will show how many uniques values exist in each column
    # ok, so down the list we can drop statename, (abbrv is fine), stfips (figure out what this is)
    # areatyname we will keep, as we want to use this to break into county/state/us dataframes
    # areaname we want
    # areatype - it looks like these map directly t areatyname, so we can drop
    # not sure about area, we can keep for now
    # we need period year for sure
    # periodtype, perioddesc, and period all ahve only single values, so can be dropped
    # inctype and description appear to be the same. We will keep the description,
    # as we will want them to be column headers eventually.
    # incsource and incsrcdes describe where the data caem from BEA or census.  While
    # it will be important to understand when looking at our data provenance, for
    # R&D and modelling purposes it isn't important.  We will drop both.
    # income we definitely want
    # incrank....not sure how useful this will be, but can keep for now
    # We'll keep popualtion to compare to numbers in our other datasets
    # We can drop releasedate as well - like incsource and incsrcdes this may be
    # important to understand in a qa step, but for R&D ew don't need.
    # ok, so we are left with the following columns
    cols = ['stateabbrv', 'areatyname', 'areaname', 'area', 'periodyear',
            'incdesc', 'income', 'incrank', 'population']
    income_df = dfs['personal_income_df'][cols]
    income_df = income_df[income_df['periodyear'] > 1989]
    # income_df.head()
    # income_df.info()
    # ok, it looks like incrank and population were forced to float by null values
    # we'll set the nulls to 0 and cast to int as neither a rank or population are meaningful as floats
    income_df[['incrank', 'population']] = income_df[['incrank', 'population']].fillna(0).astype(int)
    # ok, now lets create dummy binary columns from the incdesc column
    # income_df['incdesc'].value_counts()
    # there are only 16 entries for the last two, lets have a look at them
    # get vals
    # consider using.unique() here and walking through the error correction
    vals = income_df['incdesc'].value_counts().index
    # income_df[income_df['incdesc'] == vals[4]
    # income_df[income_df['incdesc'] == vals[5]
    # ok, so these don't look useful for our anlysis. Lets get rid of them.
    # Subset df using isin  and
    income_df = income_df[income_df['incdesc'].isin(vals[:3])]
    # ok, now to one row per county-year
    grouped_income = income_df.groupby(['stateabbrv', 'areatyname', 'areaname', 'area', 'periodyear', 'incdesc'])['income'].sum()
    grouped_income = grouped_income.unstack('incdesc').reset_index()
    # drop some stuff we don't need (MSA's and US)

    # get list because index is immutable
    cols = grouped_income.columns.tolist()
    # look at cols
    # split at hyphen, replace spaces with underscores, send to lowercase
    # [x.split(' -')[0] for x in cols]
    # [x.split(' -')[0].lower() for x in cols]
    # [x.split(' -')[0].lower().replace(' ', '_') for x in cols]
    cols = [x.split(' -')[0].lower().replace(' ', '_') for x in cols]
    # change areaname to county and periodyear to year
    grouped_income.columns = cols
    grouped_income = grouped_income.rename(columns={'areaname': 'county', 'periodyear': 'year'})
    # remove 'County'
    grouped_income['county'] = grouped_income['county'].str.replace('County', '').str.strip()
    # Drop  unused columns from each
    grouped_county_income = grouped_income[grouped_income['areatyname'] == 'County'].copy()
    grouped_county_income.drop(['stateabbrv', 'areatyname', 'area'], axis=1, inplace=True)

    grouped_state_income = grouped_income[grouped_income['areatyname'] == 'State'].copy()
    grouped_state_income.drop(['stateabbrv', 'areatyname', 'county', 'area'], axis=1, inplace=True)

    # TODO Use Colorado state wide columns to normalize ?
    # done with personal income data

    # TODO decide if I am going to work with this pdf at all
    # next, lets handle the pdf
    # this is tourism info, which is import for us to understand the volume of potential
    # non-local consumers
    # pdf_text = ....

    # Now onto the unemployment data
    unemp_df = dfs['unemployment_rates_df']
    # look at what we have
    # unemp_df.head()
    # unemp_df.columns
    # unemp_df.info()
    # unemp_df.describe()
    # Many of the fields should look familiar, as we have already evaluated them
    # for the income df.  Lets start with those columns and go from there
    # cols
    # it looks like we want the first five columns from our previous work
    # unemp.columns
    # and the last few on from this dataset, starting fom 'adjusted'
    #cols = cols[:5] + unemp.columns[-x:]
    # try a few x'es until land on correct
    unemp_cols = cols[:5] + unemp_df.columns[-10:].tolist()
    unemp_df = dfs['unemployment_rates_df'][unemp_cols]
    # figure out what laborforce means - ie, should I just pull unemprate by county and year
    # lets break this up into to df's, a yearly and a monthly

    # use .copy() to avoid setting with copy warning
    unemp_df_monthly = unemp_df[unemp_df['periodtype'] == 3].copy()
    unemp_df_yearly = unemp_df[unemp_df['periodtype'] == 1].copy()
    # fix dates to be the same as other df for monthly
    unemp_df_yearly['month'] = unemp_df_yearly['period'].astype(str).str.pad(2, 'left', '0')
    unemp_df_yearly['year'] = unemp_df_yearly['periodyear'].astype(str)
    # If the slash isn't added in the middle it sets the day to 20 rather than one
    #unemp_df_yearly['date'] = pd.to_datetime(unemp_df_yearly['month'] + '/'+ unemp_df_yearly['year'], format='%m/%Y')
    # got to site
    # https://data.colorado.gov/Labor-Employment/Unemployment-Estimates-in-Colorado/4e3w-qire
    # check what column headers are
    # looks like we want not preliminary.
    # So prelim =0
    # if we subset so areatyname = County can drop all of the following
        # stateabbrv
        # areatyname
        # area
        # periodyear
        # periodtype
        # pertypedesc
        # period
        # prelim (taking only prelim = 0)
        # benchmark (all 2018)
        # month
        # year (both created to get to date)
    # that will give a good set to model join to our other #TODO Name dataset datasets
    unemp_df_yearly = unemp_df_yearly[
        (unemp_df_yearly['areatyname'] == 'County') &
        (unemp_df_yearly['prelim'] == 0)]

    drop_cols = ['stateabbrv', 'areatyname', 'area',
                 'periodyear', 'periodtype', 'pertypdesc',
                 'period', 'prelim', 'benchmark', 'month']
    unemp_df_yearly.drop(drop_cols, axis=1, inplace=True)
    # look at df with .head()
    # notice that adjusted all = 0
    # unemp_df_yearly['adjusted'].sum()
    unemp_df_yearly.drop('adjusted', axis=1, inplace=True)
    # rename first column to mach other data sets
    unemp_df_yearly.rename(columns={'areaname': 'county'}, inplace=True)
    #TODO merge is broken, need to fix and prevent duplicate columns from coming through
    # remerged = pd.merge(merged, unemp_df_yearly, on=['county', 'date'])
    # this is going to fail because the word 'County' is present in each county field of the unemp_df_yearly df
    # need to remove
    unemp_df_yearly['county'] = unemp_df_yearly['county'].str.replace('County', '').str.strip()
    # TODO come back to this re merging by dates
    #remerged = pd.merge(merged, unemp_df_yearly, on=['county', 'date'], how='left')

    # done with unemp_monthly
    # going to ignore yearly for now
    # lets get on with liense stuff
    license_df = dfs['licensed_mj_biz_df']
    # fix columns
    license_df.columns  = license_df.columns.str.lower()
    # fix date
    license_df['month'] = license_df['month'].astype(str).str.pad(2, 'left', '0')
    license_df['year'] = license_df['year'].astype(str)
    # If the slash isn't added in the middle it sets the day to 20 rather than one
    license_df['date'] = pd.to_datetime(license_df['month'] + '/'+ license_df['year'], format='%m/%Y')
    license_df.drop(['month', 'year'], axis=1, inplace=True)
    # subset to present zip and retail rec store
    stores = ['Medical Marijuana Centers', 'Retail Marijuana Stores']
    license_df = license_df[license_df['category'].isin(stores) & license_df['zip'].notnull()].copy()
    # so, we can see that we have zip, but not county. Not great. Luckily I found this mapping online
    # https://www.zipcodestogo.com/Colorado/
    # So what do you think we should do here?
    # pandas ez mode
    zips = pd.read_html('https://www.zipcodestogo.com/Colorado/', flavor='bs4')
    # len(zips)
    # we got a few tables here.  It looks like the first one, the first two columns is what we want
    zips = zips[0][zips[0].columns[:2]]
    zips.columns = ['zip', 'county']
    # zips.head()
    # ok, looks like the headers are in the first three rows.
    # can also read in with skiprows arg
    zips = zips[3:]
    # lets check
    # pd.merge(license_df.head(), zips, on='zip', how='left')
    # ah, zips in the license df were floats
    license_df['zip'] = license_df['zip'].astype(int).astype(str)
    # we could also use string methods, split on . take [0]

    license_df = pd.merge(license_df, zips, on='zip', how='left')
    # look again
    # license_df.head()
    # license_df.info()
    # ok looks like certification is all null, so we can drop.
    # now to get the data into something we can join back to our data set.
    # what should we do?
    # dummy columns? groupbys? join as is?
    license_grouped = license_df.groupby(
        ['county', 'category', 'date'], as_index=False)['licensee'].count()
    # now we have totla mj business by county, type, and month licensed.
    # I'd also like to see total by county, type, and year.
    # yearly total of all mj businesses and
    # to get a year we will have to add a year column back, luckily that is
    # easy to do with the df.dt vectorized datetime handling functionality
    license_grouped['year'] = license_grouped['date'].dt.year
    yearly_licenses = license_grouped.groupby(['county', 'category', 'year'], as_index=False)['licensee'].sum()

    # I'd like to ahve one per county, per year as we do in our #TODO OTHER TABLE
    # To do that, we can use pandas pivot_table method
    yearly_pivot = yearly_licenses.pivot_table(index=['county', 'year'], columns='category', values='licensee')
    # yearly_pivot.head()
    # ok, so the missing values were set as NaN, which forced type float
    # lets fix that real quick
    yearly_pivot = yearly_pivot.fillna(0).astype(int)
    # yearly_pivot.head()
    # now lets reset the index and get this joined to our other data set.
    yearly_pivot = yearly_pivot.rename(columns=str).reset_index()

    # I want to merge with gmerged, but we need to turn the ages in to column headers, or otherwise reshaoe to get to one row per county year

    merged_pivots = pd.merge(yearly_pivot, age_df, on=['county', 'year'], how='right')
    # now merge in pesonal income data
    yearly_df = pd.merge(merged_pivots, grouped_county_income, on=['county', 'year'], how='left')
    # now add in tax and sales info
    # need to massage a bit to get to our county-year format
    # in this case we don't need to explicitly state the columns to aggregate by,
    # as te groupby will ignore the date column
    merged['year'] = merged['date'].dt.year
    merged = merged.groupby(['county', 'year'], as_index=False).sum()

    yearly_df = pd.merge(yearly_df, merged, on=['county', 'year'], how='left')

    # merge in unemployment info
    unemp_df_yearly['year'] = unemp_df_yearly['year'].astype(int)
    yearly_df = pd.merge(yearly_df, unemp_df_yearly, on=['county', 'year'], how='left')

    # next step, fix missing values and look for other issues
    yearly_df.iloc[:, 1:] = yearly_df.iloc[:, 1:].fillna(0).astype(int)
    # look at head, columns, describe
    # ok, first thing I see is we can drop expected_consumers_unders_18
    yearly_df.drop('expected_consumers_<18', axis=1, inplace=True)

    # ok, we have all the yearly values we want now.
    # what do we need to do after a merge?
    # - check for nulls
    # - check for other issues
    # - make sure column headers are appropriate and not duplicated
    # - shape is correct
    return yearly_df


if __name__ == '__main__':
    df = get_dataset()
    get_shops_by_year()

    # next, lets create a simple modelling set to predict revenue from our features set

