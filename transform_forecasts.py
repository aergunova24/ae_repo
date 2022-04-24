#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 24 14:19:25 2022

@author: ae
"""
import pandas as pd


s = published_gdp['JPY']
f = yoy_avg_forecasts['JPY']

def get_one_year_forecast(s:pd.Series, f:pd.Series)->pd.Series:
    i = s.dropna().last_valid_index()
    if s.dropna().last_valid_index().month==12:
        i +=pd.offsets.DateOffset(years=1)
        
    avg_last_year = s[s.index.year==(i.year-1)].mean()
    
    i_year_gdp_forecast = f[f.index.year==i.year][0]
    i_year_avg_gdp_forecast = avg_last_year*(1+i_year_gdp_forecast)
    
    sum_i_year = s[s.index.year==i.year].fillna(0).sum()
    
    rhs = (4*i_year_avg_gdp_forecast-sum_i_year)/s.dropna().iloc[-1]
    current_year_dt = s[s.index.year==i.year]
    n_obs = current_year_dt.isnull().sum()
    
    
    