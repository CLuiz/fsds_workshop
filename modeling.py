import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split, KFold, GridSearchCV, RandomizedSearchCV
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_squared_error

pd.set_option('display.float_format', '{:.2f}'.format)


def build_simple_features(df):
    # count of total addressable consumers in each county by year
    cust_cols =  [col for col in df.columns if 'expected' in col]
    df['total_expected_consumers'] = df[cust_cols].sum(axis=1)
    df.drop(cust_cols, axis=1, inplace=True)
    # expected dollars per year given customers

    # total revenue first
    df['total_rev'] = df[['med_sales', 'rec_sales']].sum(axis=1)
    # per shop rev, med and rec
    df['rec_sales_per_shop'] = df['rec_sales'] / df['rec']
    df['med_sales_per_shop'] = df['med_sales'] / df['med']
    df['total_sales_per_shop'] = df['total_rev'] / df[['rec', 'med']].sum(axis=1)

    sales_cols = [col for col in df.columns if 'sales' in col]
    df[sales_cols] = df[sales_cols].replace([np.inf, np.nan], 0).astype(int)
    # given consumers, unemp_rate, income & pop can we predict total revenue?
    # discover licensee info is not what we are looking for, provide links to data
    # add scaling to all relevant columns

    return df


def main():
    # intent:
    # use the datseta to model 2 things at first
    # 1 - find the best counties without rec shops currently to open a dispensary
    # ex.  best_shop ~ expected revenue given pop and rev numbers of other counties across the years
    # 2 - Find the best county with & without rec to open the next ship (model incremental revenue associated with the opening of a shop given pop, current rec, current med)
    # 3 - find the same quantities in 5 and ten years using year over year population and revenue growth

    np.random.seed(42)
    df = pd.read_parquet('data/processed_data/processed_dataset.parquet')
    # add a few features and scale vals
    df = build_simple_features(df)


    # first, lets predict revenue based on our feature set
    # this is going to be a much smaller data set - we need to use
    # only rows with med and/or rec numbers depending on our methedology,
    # and we only have  a few years of data.  We further need to split
    # into train and test sets.  Luckily we can get away with a simple model here.

    # create modeling df including all rows with revenue
    # take all rows with revenue

    # TODO 2019 data not making it through.  WHY?
    model_df = df[df['total_rev'] > 0]

    # simplify to a few columns for first modeling effort
    simple_modeling_cols =['county', 'year', 'global_total_pop',
       'median_household_income', 'per_capita_personal_income',
       'unemprate', 'total_expected_consumers', 'med', 'rec', 'total_rev']

    simple_model_df = model_df[simple_modeling_cols]
    # lets set index to be county and year

    # We have a time series and we don't want any data from the future getting into our
    # model. We will break the dataset up to holdback the 2018 data for testing
    train = simple_model_df[simple_model_df['year'] != 2018]
    test = simple_model_df[simple_model_df['year'] == 2018]
    train.set_index(['county', 'year'], inplace=True)
    test.set_index(['county', 'year'], inplace=True)
    X_train, y_train = train.iloc[:, :-1], train.iloc[:, -1]
    X_test, y_test = test.iloc[:, :-1], test.iloc[:, -1]

    # now, lets we will use scikit-learn's MinMaxScaler to scale our features
    # We need to fit to the training data, then transorm both the test and training data
    # We can't fit to the entire dataset because of data leakage, ie, data
    # from our test set would like into our training data via the minmax
    # encoding

    # This is an example of the scikit-learn api
    # instantiate object
    X_scaler = MinMaxScaler()
    # fit object to data (or fit_transform)
    X_scaler.fit(X_train)
    # use object to transform (predict) on train set / other data
    X_train_scaled = X_scaler.transform(X_train)
    X_test_scaled = X_scaler.transform(X_test)

    y_scaler = MinMaxScaler()
    # fit object to data (or fit_transform)
    y_scaler.fit(y_train)
    # use object to transform (predict) on train set / other data
    y_train_scaled = y_scaler.transform(y_train)
    y_test_scaled = y_scaler.transform(y_test)

    # have that issue here.

    # ok, lets run the data through a linear regression to set a baseline

    reg = LinearRegression()
    reg.fit(X_train, y_train)
    r2 = reg.score(X_train, y_train)
    preds = reg.predict(X_test)
    test['preds'] = preds
    rmse = pow(mean_squared_error(test['total_rev'], test['preds']), .5)
    # get in sample error
    train_preds = reg.predict(X_train)

    # show chart
    plt.scatter(y_test, preds)
    plt.scatter(y_train, train_preds)
    plt.savefig('fig.png')
    # there is definitely signal here, but it
    # looks like Denver is screwing up the rest of the state.

    # there are a few things we ca do at this point, the easist being try
    # a more sophisticated modeling approach. Random Forest time.
    rf_reg = RandomForestRegressor(n_estimators=200, random_state=42, oob_score=True)
    rf_reg.fit(X_train, y_train)
    rf_preds = rf_reg.predict(X_test)

    # look at feature importances
    # rf_reg.feature_importances_
    # hmm, 85% of the regressores value is from our expected customers i
    # feature, and it is far outperforming global population- Nice!



    # DECISIONS point - improve regressor or move on to another modeling technique?
    # If improve regressor - wing it
    # if new technique, clustering




    # check shape, info, etc
    # we only have 2019 numbers up until ...Aug?  so we need to scale out.  We will use a naive method here, and ignore 4th quarter revenue growth.  Ie, full_year_rev = rev_to_aug * 12/8
    # scale 2019 numbers #TODO These didn't appear to come through. investigate license pipeline

    # adjust features.  Label encode, dummies, bucket items, etc

    # Now lets look at population adjusted revenue

    # ok, now cost of living

    #
    # what fields should we simplify to, and what fields need to be removed?
    # remove
       # - raw population figures including unemp numbers
       # - med, rec, shop count, tax & rev

    # simplify:
        # - total expected consumers
        # - expected dollars spent per consumer Maybe?
        # -

    # one easy thing we can do is figure out the optimal number of shops
    # given the expected consumers in an area
    # access score - is there an adjacent county with rec?
    return df

if __name__ == '__main__':
    df = pd.read_parquet('data/processed_data/processed_dataset.parquet')
