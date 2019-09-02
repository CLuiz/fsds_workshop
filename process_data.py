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
    # TODO ensure categorical handling is working properly,  Trace through.
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    # fix month and year iteratively
    df['month'] = df['month'].astype(str).str.pad(2, 'left', '0')
    df['year'] = df['year'].astype(str)
    # If the slash isn't added in the middle it sets the day to 20 rather than one
    df['date'] = pd.to_datetime(df['month'] + '/'+ df['year'], format='%m/%Y')
    df.drop(['month', 'year'], axis=1, inplace=True)

    # fix using fill na and cast as int
    df[cash_cols] = df[cash_cols].fillna(0).astype(int)

    # not thinking I am going to need these columns.  #TODO delete or keep this part of the work?
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


def prep_population_df(df):
    pop_by_age_df = dfs['pop_by_age_and_year_df']
    # get usage by age dict
    # url ='https://www.statista.com/statistics/737849/share-americans-age-group-smokes-marijuana/'
    usage_by_age_dict = {'18-29': .24, '30-49': .13, '50-64': .11, '65+': .06}
    labels = list(usage_by_age_dict.keys())
    # Add an under 18 label
    labels.insert(0, '<18')

    # discretize into age buckets
    pop_by_age_df['binned_age'] = pd.cut(
        pop_by_age_df['age'],
        [0, 18, 29, 49, 65, 120],
        labels=labels,
        include_lowest=True)

    # Now lets group by year, county, and binned_age
    grouped = pop_by_age_df.groupby(['county', 'year', 'binned_age'], as_index=False)[
        'malePopulation', 'femalePopulation', 'totalPopulation'].sum()
    # Get the total population in a county each year
    total_pop_by_year = grouped.groupby(
        ['county', 'year'], as_index=False)['totalPopulation'].sum()

    # rename total population column before merging
    cols = total_pop_by_year.columns.tolist()
    cols = cols[:-1] + ['global_total_pop']
    total_pop_by_year.columns = cols

    # combine our grouped populations with our total yearly poulations
    gmerged = pd.merge(grouped, total_pop_by_year, on=['county', 'year'])
    # next, lets look at how many expected users there are, given the stats we
    #found on the statista site
    # add entry for under 18 and set usage fraction to zero
    usage_by_age_dict['<18'] = 0

    # TODO these two steps should be combined
    gmerged['consumer_fraction'] = gmerged['binned_age'].apply(usage_by_age_dict.get)
    gmerged['expected_consumers'] = [
        x * y for x, y in zip(gmerged['consumer_fraction'], gmerged['totalPopulation'])]

    # Calculate total expected consumers per year, per county across all ages
    expected_consumers_by_year = gmerged.groupby(
        ['county', 'year'], as_index=False)['expected_consumers'].sum()
    # Cast as int - fractional people don't make sense
    expected_consumers_by_year['expected_consumers'] = expected_consumers_by_year['expected_consumers'].astype(int)

    # ok, now lets reshape the data to have one row per county, per year.
    # We can do this using pandas pivot_table method and some massaging of the multi indices
    # after pivoting.

    age_pivot = pd.pivot_table(gmerged, index=['county', 'year'], values=['expected_consumers', 'malePopulation', 'femalePopulation',
        'totalPopulation', 'consumer_fraction'], columns='binned_age')

    # The row level is easy, the columns are different though.
    # The easy way to do this (and end up with interpretable headers) is to
    rename the columns to a single str including both pieces of the index. This is how that can be done

    # first we change the column type from categorical to string as so
    age_pivot = age_pivot.rename(columns=str)

    # next we can join the levels of the column names using a list comprehension
    age_pivot.columns = ['_'.join(col) for col in age_pivot.columns]

    # now drop the county/year multi-index
    age_pivot.reset_index(inplace=True)

    # now to add back the global population numbers
    global_pops = gmerged[['county', 'year', 'global_total_pop']].drop_duplicates()

    age_df = pd.merge(
        age_pivot, global_pops,
        how='left', on=['county', 'year'])
    # and, lets look at the finished product
    return age_df


def prep_income_df(df):
    cols = ['stateabbrv', 'areatyname', 'areaname', 'area', 'periodyear',
            'incdesc', 'income', 'incrank', 'population']
    income_df = df[cols]
    income_df = income_df[income_df['periodyear'] > 1989]
    # we'll set the nulls to 0 and cast to int as neither a rank or population are meaningful as floats
    income_df[['incrank', 'population']] = income_df[['incrank', 'population']].fillna(0).astype(int)
    # some of the incdesc vals are not useful.  Remove all but the top 3
    vals = income_df['incdesc'].value_counts().index

    # Subset df using isin  and the top vals from above
    income_df = income_df[income_df['incdesc'].isin(vals[:3])]

    # ok, now to one row per county-year
    grouped_income = income_df.groupby(['stateabbrv', 'areatyname', 'areaname', 'area', 'periodyear', 'incdesc'])['income'].sum()
    grouped_income = grouped_income.unstack('incdesc').reset_index()

    # get list because index is immutable
    cols = grouped_income.columns.tolist()
    cols = [x.split(' -')[0].lower().replace(' ', '_') for x in cols]

    # change areaname to county and periodyear to year
    grouped_income.columns = cols
    grouped_income = grouped_income.rename(columns={'areaname': 'county', 'periodyear': 'year'})
    # remove 'County'
    grouped_income['county'] = grouped_income['county'].str.replace('County', '').str.strip()

    # drop some stuff we don't need (MSA's and US)
    grouped_county_income = grouped_income[grouped_income['areatyname'] == 'County'].copy()

    # Drop  unused columns from each
    grouped_county_income.drop(['stateabbrv', 'areatyname', 'area'], axis=1, inplace=True)

    # TODO decide whether or not to normalize by state numbers
    # remove the following two lines if not
    grouped_state_income = grouped_income[grouped_income['areatyname'] == 'State'].copy()
    grouped_state_income.drop(['stateabbrv', 'areatyname', 'county', 'area'], axis=1, inplace=True)
    return grouped_county_income


def prep_unemp_df(df):
    # it looks like we want the first five columns from our previous work
    # and the last few on from this dataset, starting fom 'adjusted'
    unemp_cols = cols[:5] + df.columns[-10:].tolist()
    unemp_df = df[unemp_cols]
    # figure out what laborforce means - ie, should I just pull unemprate by county and year

    # lets break this up into to df's, a yearly and a monthly

    # use .copy() to avoid setting with copy warning
    unemp_df_monthly = unemp_df[unemp_df['periodtype'] == 3].copy()
    # could use monthly data to create a rolling (or yearly) employment
    # security indicator.  One would expect lower variation in employment
    # would equate to stable spending.

    unemp_df_yearly = unemp_df[unemp_df['periodtype'] == 1].copy()

    # fix dates to be the same as other df for monthly
    unemp_df_yearly['month'] = unemp_df_yearly['period'].astype(str).str.pad(2, 'left', '0')
    unemp_df_yearly['year'] = unemp_df_yearly['periodyear'].astype(str)

    # TODO remove commented date lines below if not using for merge
    # If the slash isn't added in the middle it sets the day to 20 rather than one
    #unemp_df_yearly['date'] = pd.to_datetime(unemp_df_yearly['month'] + '/'+ unemp_df_yearly['year'], format='%m/%Y')
    unemp_df_yearly = unemp_df_yearly[
        (unemp_df_yearly['areatyname'] == 'County') &
        (unemp_df_yearly['prelim'] == 0)]

    # remove columns we are not using
    drop_cols = ['stateabbrv', 'areatyname', 'area',
                 'periodyear', 'periodtype', 'pertypdesc',
                 'period', 'prelim', 'benchmark', 'month',
                 'adjusted']

    unemp_df_yearly.drop(drop_cols, axis=1, inplace=True)
    # rename first column to match other data sets

    unemp_df_yearly.rename(columns={'areaname': 'county'}, inplace=True)
    #TODO merge is broken, need to fix and prevent duplicate columns from coming through

    # subsequent merges are going to fail because the word 'County' is present
    # in each county field of the unemp_df_yearly df need to remove
    unemp_df_yearly['county'] = unemp_df_yearly['county'].str.replace('County', '').str.strip()
    return unemp_df_yearly


def read_license_files(data_dir='data/licenses_by_year'):
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
    # at minimum.
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
    # use pandas read_html to get a mapping of zip codes to counties from the
    # source url
    zips = d.read_html(source, flavor='bs4', skiprows=3)
    zips = zips[0].iloc[:, :2]
    zips.columns = ['zip', 'county']
    return zips


def get_shops_by_year(license_file_dir='data/licenses_by_year/'):
    shops_by_year = read_license_files(license_file_dir)
    shops_by_year = (
        shops_by_year.
        reset_index().
        rename(columns={'level_0': 'source'}).
        drop('level_1', axis=1))
    shops_by_year['source'] = shops_by_year['source'].str[:3]
    zips = get_zips()
    license_df = pd.merge(shops_by_year, zips, on='zip')
    # there are some errors with how the zip codes are entered and we didn't get
    # them all. I'll leave this as an opportunity to improve on the processing
    # pipeline

    # fix inconcistent dataset nameing. ret = rec for the rec (partial) dataset of 2019
    license_df['source'] = ['rec' if x == 'ret' else x for x in license_df['source']

    # TODO Do I need to interim group by date? Or go straight to year?
    license_grouped = license_df.groupby(
        ['county', 'category', 'date'], as_index=False)['licensee'].count()
    # now we have total mj business by county, type, and month licensed.
    # I'd also like to see total by county, type, and year.
    # yearly total of all mj businesses and

    # Add back year column with pandas vectorized datetime operation
    license_grouped['year'] = license_grouped['date'].dt.year
    yearly_licenses = license_grouped.groupby(['county', 'category', 'year'], as_index=False)['licensee'].sum()

    # Pivot to get to one per county, per year
    yearly_pivot = yearly_licenses.pivot_table(index=['county', 'year'], columns='category', values='licensee')
    # fix missing values that were set as NaN, and forced type float
    yearly_pivot = yearly_pivot.fillna(0).astype(int)
    # reset the index and change the column index to type str
    yearly_pivot = yearly_pivot.rename(columns=str).reset_index()
    return yearly_pivot


if __name__ == '__main__':
    # read (most) csvs downloaded with install script into dict of form
    # datasource name: data frame
    # skipping licenses by year because of mixed document types
    dfs = load_csvs('data')

    # population
    # Pull out population data and clean up
    pop_df = prep_population_df(dfs['pop_by_age_and_year_df'])

    # personal income data
    # Pull income dataset and clean up
    grouped_county_income_df = prep_income_df(dfs['personal_income_df'])

    # revenue
    # Pull out tax and revenue data and clean up

    # get mj sales info
    mj_sales_df = prep_revenue_df(
        dfs['mj_sales_revenue_df'],
        ['med_sales', 'rec_sales'],
        ['med_blank_code', 'rec_blank_code'])

    # get tax info
    mj_tax_df = prep_revenue_df(
        dfs['monthly_tx_revenue_df'],
        ['med_tax_rev', 'rec_tax_rev'],
        ['med_blank_code', 'rec_blank_code'])

    # drop unwanted columns from tax data
    mj_tax_df.drop(['med_remainderofstate_counties',  'rec_remainderofstate_counties'], axis=1, inplace=True)

    # join tax & revenue dfs
    merged_tax_rev_df = pd.merge(
    mj_sales_df, mj_tax_df, on=['county', 'date'], how='left')

    # unemp
    # Pull unemployment data
    unemp_df = prep_unemp_df(dfs['unemployment_rates_df'])

    # licenses
    # Pull all license data and get to a useable form
    shops_by_year_df = get_shops_by_year(license_file_dir='data/licenses_by_year/')

    # TODO join all data frames together
