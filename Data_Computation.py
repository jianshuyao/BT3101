
# coding: utf-8

# In[1]:

import pandas as pd
import numpy as np


# In[2]:

#bloomberg sample data for 5 currencies 
df = pd.read_excel('Dummy Dataset.xlsx')
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
df.set_index('Date', inplace=True)
df = df.sort_index()


def trans_preprocessing(trader_data):
    #handle direction and notional of trade 
    #Size is a new column with the direction of trade
    # long: positive; short: negative
    trader_data['Size'] = trader_data.Direction.apply(
               lambda x: (1 if x == 'long' else -1))
    trader_data['Size'] = trader_data.Size * trader_data['Size/Notional']
    trader_data['Timestamp'] = pd.to_datetime(trader_data['Timestamp'],dayfirst=True)


# In[5]:

#transaction data for one trade A
transaction_A = pd.read_csv('A_transaction.csv')
trans_preprocessing(transaction_A)
transaction_A


# In[14]:

from datetime import datetime
get_datetime = lambda s: datetime.strptime(s, "%d/%m/%Y")
#get_datetime = lambda s: datetime.strptime(s, "%Y-%m-%d")

#find the nearest date after a given date
def nearest_after(ls,base):
    base = get_datetime(base)
    later = filter(lambda d: d >= base, ls)
    try:
        return min(later)
    except ValueError:
        return None 
    #closest_date = min(later)
    #return closest_date


# ### The below function only works for start from timestamp 0
# ### i.e. : no other trade made before that

# In[15]:

def pnl_product(start,end,trader_df,portfolio,currency,df):
    #start is the nearest date after the given starting date when there is a trade (dd/mm/yy)
    #start will be taken as the starting point 
    #all previous trade will be ignored

    
    #input example: '1/9/2019', '10/9/2019', A1_KWN, bloomberg_df
    #input dates are inclusive
    
    product = trader_df.groupby('Portfolio').get_group(portfolio).groupby('Product').get_group(currency)
    
    start = nearest_after(product.Timestamp,start)
    end = pd.to_datetime(end,dayfirst=True)
    
    
    
    try:
        product = product[(product['Timestamp'] >= start) & (product['Timestamp'] <= end)]
    except TypeError:
        print('There is no trade for ' + currency + ' within the given time range.')
        return None
        
    #only filter those trades within the selected time range for both transaction and bloomberg datasets
    product = product[(product['Timestamp'] >= start) & (product['Timestamp'] <= end)]
    df = df[(df.index >= start) & (df.index <= end)]
    df = df.sort_index()
    
    
    result = pd.DataFrame()
    result['Date'] = df.index
    result.set_index('Date', inplace=True)
    result['PnL'] = np.nan
    
    profit = 0 
    close_price = 0
    old_entry_price = 0
    new_entry_price = 0
    size = 0 #sum of size of products for previous days 
    new_trade_size = 0
    
    #for everyday
    for j in df.index:
        #print(j)
        
        #for all trades on that day
        temp = product[product['Timestamp']==j]
        
        if not temp.empty:
        #if there is trade
            #print('yes')
            
            for i in range(temp.shape[0]):
                close_price = df.ix[temp.iloc[i,10]][currency]
                #print('the close price is ' + str(close_price))
                new_entry_price = temp.iloc[i,4]
                #print('the new entry price is ' + str(new_entry_price))
                new_size = temp.iloc[i,12]
                #print('the new size is ' + str(new_size))
                profit = profit + (close_price - new_entry_price) * new_size + (close_price - old_entry_price)* size
                old_entry_price = close_price
                #print('old entry price assignment done')
                size = size + new_size
                #print('size assignment done')
            
            result.at[j, 'PnL'] = profit
            profit = 0
            
        else: 
            #print('No')
            close_price = df.ix[j][currency]
            #print("close price on this no-trade day is " + str(close_price))
            profit = (close_price - old_entry_price)*size
            result.at[j, 'PnL'] = profit
            
    
    return result 
        


# ### PnL function for limited time range

# In[9]:

#bloomberg sample data for 5 currencies for 1 month
df2 = pd.read_excel('Dummy Dataset_1month.xlsx')
df2 = df2.loc[:, ~df2.columns.str.contains('^Unnamed')]
df2.set_index('Date', inplace=True)
df2 = df2.sort_index()



#find the nearest date before a given date
def nearest_before(ls,base):
    base = get_datetime(base)
    later = filter(lambda d: d < base, ls)
    try:
        return max(later)
    except ValueError:
        return None 


# In[39]:

from datetime import timedelta



# In[31]:

def product_position_til(date,trader_df,portfolio,currency):
    
    #this function calculates the overall position of one product in one portfolio before input date
    #trades made on input date itself are not included 
    product = trader_df.groupby('Portfolio').get_group(portfolio).groupby('Product').get_group(currency)
    date = nearest_before(product.Timestamp,date)
    #print(date)
    
    try:
        product = product[(product['Timestamp'] <= date)]
    except TypeError:
        return 0
    
    result = product.Size.sum()
    
    return result


# In[70]:

def pnl_product2(start,end,trader_df,portfolio,currency,df):
    #start is the nearest date after the given starting date when there is a trade (dd/mm/yy)
    # start will be taken as the starting point 
    #all previous trade will be ignored

    
    #input example: '1/9/2019', '10/9/2019', A1_KWN, bloomberg_df
    #input dates are inclusive
    
    product = trader_df.groupby('Portfolio').get_group(portfolio).groupby('Product').get_group(currency)
    size = product_position_til(start,trader_df,portfolio,currency)
                
    if size == 0:
        start = nearest_after(product.Timestamp,start)
    else:
        start = pd.to_datetime(start,dayfirst=True)
        print('size is ' + str(size))
    
    end = pd.to_datetime(end,dayfirst=True)
    
    try:
        product = product[(product['Timestamp'] >= start) & (product['Timestamp'] <= end)]
    except TypeError:
        print('There is no trade for ' + currency + ' within the given time range.')
        return None
        
    #only filter those trades within the selected time range for both transaction and bloomberg datasets
    product = product[(product['Timestamp'] >= start) & (product['Timestamp'] <= end)]
    previous_close = df.loc[start-timedelta(1),currency]
    df = df[(df.index >= start) & (df.index <= end)]
    df = df.sort_index()
    #print(df)
    
    result = pd.DataFrame()
    result['Date'] = df.index
    result.set_index('Date', inplace=True)
    result['PnL'] = np.nan
    
    profit = 0 
    close_price = 0
    if size == 0:
        old_entry_price = 0
    else:
        old_entry_price = previous_close
        print('previous close price is ' + str(previous_close))
    new_entry_price = 0
    #original size is defined previously; new_trade_size is the trades made on the day
    new_trade_size = 0
    
    
    
    
    #for everyday
    for j in df.index:
        print(j)
        
        #for all trades on that day
        temp = product[product['Timestamp']==j]
        
        if not temp.empty:
        #if there is trade
            print('yes')
            
            for i in range(temp.shape[0]):
                close_price = df.ix[temp.iloc[i,10]][currency]
                print('the close price is ' + str(close_price))
                new_entry_price = temp.iloc[i,4]
                print('the new entry price is ' + str(new_entry_price))
                new_size = temp.iloc[i,12]
                print('the new size is ' + str(new_size))
                profit = profit + (close_price - new_entry_price) * new_size + (close_price - old_entry_price)* size
                old_entry_price = close_price
                print('old entry price assignment done')
                size = size + new_size
                print('size assignment done')
                print('new size is ' + str(size))
            
            result.at[j, 'PnL'] = profit
            profit = 0
            
        else: 
            print('No')
            close_price = df.ix[j][currency]
            print("close price on this no-trade day is " + str(close_price))
            profit = (close_price - old_entry_price)*size
            result.at[j, 'PnL'] = profit
            
    
    return result 



# In[8]:

def pnl_portfolio(start,end,trader_df,portfolio,df):
    products = trader_df.groupby('Portfolio').get_group(portfolio)['Product'].unique()
    
    for i in range(len(products)):
        currency = products[i]
        if i == 0:
            result = pnl_product(start,end,trader_df,portfolio,currency,df)
        else:
            temp = pnl_product(start,end,trader_df,portfolio,currency,df)
            try:
                result = pd.concat([result, temp]).groupby('Date', as_index=True).sum()
            except ValueError:
                return None
    return result
        
        


# In[9]:

def pnl_trader(start,end,trader_df,df):
    portfolios = trader_df['Portfolio'].unique()
    
    for i in range(len(portfolios)):
        portfolio = portfolios[i]
        if i == 0:
            result = pnl_portfolio(start,end,trader_df,portfolio,df)
        else:
            temp = pnl_portfolio(start,end,trader_df,portfolio,df)
            try:
                result = pd.concat([result, temp]).groupby('Date', as_index=True).sum()
            except ValueError:
                return None
    return result    

               


# In[10]:

from math import sqrt
def sharpe_ratio(pnl_df):
    mu = pnl_df.PnL.mean()
    sd = pnl_df.PnL.std()
    try:
        result = mu/sd
    except ZeroDivisionError:
        return 0
    
    return result


# In[11]:

def sortino_ratio(pnl_df):
    mu = pnl_df.PnL.mean()
    sd = pnl_df.loc[(pnl_df['PnL'] <= 0)].PnL.std()
    try:
        result = mu/sd
    except ZeroDivisionError:
        return 0
    return result
                     


# In[12]:

from fractions import Fraction
def hit_ratio(pnl_df):
    winning = pnl_df.loc[(pnl_df['PnL'] > 0)].shape[0]
    losing = pnl_df.loc[(pnl_df['PnL'] <= 0)].shape[0]
    try:
        result = winning/losing
        return result
    except ZeroDivisionError:
        print ("No losing trade")
        return winning


def hello_world():
    print('Hello Matiantian')

trial = pnl_trader('20/08/2019','15/09/2019',transaction_A,df)
trial.head()


