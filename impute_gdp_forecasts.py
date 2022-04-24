#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sympy
import warnings

"""This module imputes quartely forecasts of gdp growth from the forecasts of average annual gdp growth
   assuming that some gdp data might be already released within a year.
"""

def transfor_published_gdp_data(published_gdp:pd.DataFrame, yoy_avg_forecasts:pd.DataFrame)->pd.DataFrame():
    """Tranform dataset by adding exta rows for the forecasting period.
    """
    # Check whether an input is a pd.DataFrame
    if isinstance(published_gdp, pd.Series):
        published_gdp = published_gdp.to_frame()
        
    # Add extra rows to the dataset for the forecasting period
    start_idx = published_gdp.last_valid_index()+pd.offsets.DateOffset(months=3)
    end_idx = yoy_avg_forecasts.last_valid_index()
    
    extra_idx = pd.date_range(start=start_idx,end=end_idx,freq='QS-DEC')
    extra_dt = pd.DataFrame(index=extra_idx, columns=published_gdp.columns)
    
    published_gdp_tr = pd.concat([published_gdp,extra_dt]).sort_index()
    return published_gdp_tr
    
    
    
def impute_one_year_forecast(s:pd.Series, f:pd.Series)->pd.Series:
    """Impute quartely GDP forecasts for one year.
    """
    i = s.dropna().last_valid_index()+pd.offsets.YearEnd()-pd.offsets.MonthBegin()
    if s.dropna().last_valid_index().month==12:
        i +=pd.offsets.DateOffset(years=1)
        
    avg_last_year = s[s.index.year==(i.year-1)].mean()
    
    i_year_gdp_forecast = f[f.index.year==i.year][0]
    i_year_avg_gdp_forecast = avg_last_year*(1+i_year_gdp_forecast)
    
    sum_i_year = s[s.index.year==i.year].fillna(0).sum()
    
    rhs = (4*i_year_avg_gdp_forecast-sum_i_year)/s.dropna().iloc[-1]
    current_year_dt = s[s.index.year==i.year]
    n_obs = current_year_dt.isnull().sum()
    
    # Get quartely forecasts of gdp growth (y) from the forecasts of average annual gdp growth from the equations:
    # (1) x1 + x1*(1+y) + x1*(1+y)ˆ2 + x1*(1+y)ˆ3 = 4*average gdp forecast level, 
    # when only data for the first quarter (x1) within a year is available.
    # (2) x1 + x2 + x2*(1+y) + x2*(1+y)ˆ2 = 4*average gdp forecast level, 
    # when only data for the first and second quarters (x1 and x2) within a year is available.
    # (3) x1 + x2 + x3 + x3*(1+y) = 4*average gdp forecast level, 
    # when data for the first three quarters (x1, x2 and x3) within a year is available.
    # (4) x0*(1+y) + x0*(1+y)ˆ2 + x0(1+y)ˆ3 + x0(1+y)ˆ4 = 4*average gdp forecast level, 
    # when no data for the current year is available (x0 is gdp for the last quarter of the previous year).
    
    y = sympy.symbols('y')
    str_eq = []
    str_eq.extend(['y**'+str(i) for i in range(1,n_obs+1)])
    str_eq = '+'.join(str_eq)
    growth_rate = sympy.solve(sympy.simplify(str_eq)-rhs,y)
    
    # As polinomial equation of order n is solved, we have n solutions and we need to select 
    # a propeper one. Selection creteria 1. drop complex numbers,
    # selections criteria 2. (1+ quartely gdp growth) should lie in the interval [0.5,1.5]
    # based on economic judgement.
    
    growth_rate = [i for i in growth_rate if (type(i)==sympy.core.numbers.Float)]
    growth_rate = [i for i in growth_rate if (i>0.5)&(i<1.5)]
    
    # Check whether there is one remaining solution.
    if len(growth_rate)!=1:
        message = 'Check the solutions of the equaition for gdp growth rates for %s in %s'\
            % (s.name, i.year)
        warnings.warn(message)
    
    # Fill forward gdp series with quartely forecasts
    int_dt_idx = pd.date_range(start=i-pd.offsets.DateOffset(months=n_obs*3), end=i,freq='QS-DEC')
    int_dt = pd.Series(growth_rate[0], index=int_dt_idx, name=current_year_dt.name)
    int_dt.iloc[0] = 1
    int_dt = int_dt.cumprod()
    out = s.ffill().mul(int_dt).reindex(int_dt.index)
    s = s.fillna(out)
    return s

    
def get_one_country_forecasts(s:pd.Series,f:pd.Series)->pd.Series:
    """Impute GDP forecasts for one country for the whole forecasting horizon.
    """
    if s.dropna().last_valid_index()==s.index[-1]:
        return s
    else:
        s = impute_one_year_forecast(s, f)
    
    s = get_one_country_forecasts(s,f)
    return s
        

def prepare_gdp_forecasts_dataset(published_gdp:pd.DataFrame, yoy_avg_forecasts:pd.DataFrame)->pd.DataFrame:
    """Inpute GDP forecasts for the whole list of countries.
    """
    published_gdp_tr = transfor_published_gdp_data(published_gdp, yoy_avg_forecasts)
    
    gdp_forecasts = pd.concat(
        {
            cc: get_one_country_forecasts(published_gdp_tr[cc],yoy_avg_forecasts[cc])
            for cc in published_gdp_tr.columns
                }, axis=1).astype(float)
    return gdp_forecasts



