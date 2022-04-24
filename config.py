#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 24 09:20:51 2022

@author: ae
"""
from imfpy import searches


DEFAULT_CC_LIST = ['France','Germany','Japan','Italy','United Kingdom', 'United States']


CC_DICT = {
    'France':'FRF',
    'Germany':'DEM',
    'Japan':'JPY',
    'Italy':'ITL',
    'United Kingdom':'GBP', 
    'United States':'USD'
    }

IMF_CODES = searches.country_codes().set_index(['Country']).squeeze().to_dict()
