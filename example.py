#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import pandas as pd
from datetime import date
from typing import Tuple
import numpy as np
import random

from config import DEFAULT_CC_LIST, CC_DICT, IMF_CODES
from impute_gdp_forecasts import prepare_gdp_forecasts_dataset

"""Prepare dummy datasets with released gdp data and average annual gdp forecasts based on imf data
   to check the behaviour of impute_gdp_forecasts module.
"""
def get_gdp_data_country(country_name:str, start_period:int=1960, end_period:int=None)->pd.Series:
    """Download real gdp data for one country from IMF
    """
    # Prepare URL
    if not end_period:
        end_period = date.today().year
    
    url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/IFS/'\
          'Q.%s.NGDP_R_SA_XDC.?startPeriod=%s&endPeriod=%s'\
          % (IMF_CODES[country_name], start_period, end_period)
    
    # Get data from the above URL using the requests package
    data = requests.get(url).json()

    # Load data into a pandas dataframe
    out = pd.DataFrame(data['CompactData']['DataSet']['Series']['Obs'])
    
    # Transform the dataframe
    col_dict = {'@TIME_PERIOD':'tstamp', '@OBS_VALUE':'value'}   
    out_tr = out.rename(columns=col_dict).set_index(['tstamp'])
    return out_tr.squeeze()


def prepare_data(asof_quarter:pd.Timestamp=pd.Timestamp('2019-06-01'), country_list:list=DEFAULT_CC_LIST)->Tuple[pd.DataFrame,pd.DataFrame]:
    """Prepare prepare datasets with released and forecasted gdp data.
    """
    # Prepare the dataset with real gdp data for a set of countries 
    dt = pd.concat({CC_DICT[cc]: get_gdp_data_country(cc) for cc in DEFAULT_CC_LIST}, axis=1).astype(float).sort_index()
    dt.index = pd.Series(pd.to_datetime(dt.index)).apply(lambda s: s+pd.offsets.QuarterEnd()-pd.offsets.MonthBegin())
    
    # Split the dataset into published data and forecasts, 
    # where forecasts are yoy average growth rates    
    published_gdp = dt.truncate(after=asof_quarter)  
    published_gdp.loc[asof_quarter,random.choices([True,False], k=dt.shape[1])] = np.nan   
    
    yoy_avg_forecasts = dt.resample('AS').mean().pct_change()
    yoy_avg_forecasts.index = yoy_avg_forecasts.index+pd.offsets.DateOffset(months=11)
    yoy_avg_forecasts = yoy_avg_forecasts.truncate(before=asof_quarter)
    
    return published_gdp, yoy_avg_forecasts


def run_example()->pd.DataFrame:
    """Run example
    """
    published_gdp, yoy_avg_forecasts = prepare_data()
    quartely_gdp = prepare_gdp_forecasts_dataset(published_gdp, yoy_avg_forecasts)
    return quartely_gdp



