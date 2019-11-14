import pandas as pd
import numpy as np
from datetime import timedelta
from datetime import datetime
from fractions import Fraction
from math import sqrt



####################################
####  1. HELPER FUNCTIONS  ####
####################################

# function to preprocess transaction data 
# Purpose: 
## 1. Take direction of the trade into consideration. Long: Postive; Short: Negative
## 2. Transform Date string to Datetime object
# input: transaction datafram of a trader
# output: processed transaction dataframe
def trans_preprocessing(trader_data):
    #handle direction and notional of trade 
    #Size is a new column with the direction of trade
    # long: positive; short: negative
    trader_data['Size'] = trader_data.Direction.apply(
               lambda x: (1 if x == 'long' else -1))
    trader_data['Size'] = trader_data.Size * trader_data['Size/Notional']
    trader_data['Timestamp'] = pd.to_datetime(trader_data['Timestamp'],dayfirst=True)


#transaction data for one trade A
transaction_A = pd.read_csv('transaction.csv')
trans_preprocessing(transaction_A)
transaction_A


get_datetime = lambda s: datetime.strptime(s, "%d/%m/%Y")

#find the nearest date after a given date
def nearest_after(ls,base):
    base = get_datetime(base)
    later = filter(lambda d: d >= base, ls)
    try:
        return min(later)
    except ValueError:
        return None 


#find the nearest date before a given date
def nearest_before(ls,base):
    base = get_datetime(base)
    later = filter(lambda d: d < base, ls)
    try:
        return max(later)
    except ValueError:
        return None 

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

# function to calculate PnL of a single product of a portforlio of a trader 
# Inputs: Start and end date, preprocessed transaction dataframe, portfolio name (string), product name (String), bloomberg dataframe
# Output: PnL Dataframe, Date as index
def pnl_product(start,end,trader_df,portfolio,currency,df):
    
    #input example: '1/9/2019', '10/9/2019', 'A1', 'TWN', bloomberg_df
    #input dates are inclusive
    
    product = trader_df.groupby('Portfolio').get_group(portfolio).groupby('Product').get_group(currency)
    size = product_position_til(start,trader_df,portfolio,currency)
                
    if size == 0:
        start = nearest_after(product.Timestamp,start)
        #print (start)
    else:
        start = pd.to_datetime(start,dayfirst=True)
        #print('size is ' + str(size))
    
    end = pd.to_datetime(end,dayfirst=True)
    
    try:
        product = product[(product['Timestamp'] >= start) & (product['Timestamp'] <= end)]
    except TypeError:
        #print('There is no trade for ' + currency + ' within the given time range.')
        return None
        
    #only filter those trades within the selected time range for both transaction and bloomberg datasets
    product = product[(product['Timestamp'] >= start) & (product['Timestamp'] <= end)]
    
    temp = start-timedelta(1)
    if temp in df.index:
        previous_close = df.loc[start-timedelta(1),currency]
    else:
        temp_str = str(temp.day)+'/'+str(temp.month)+'/'+str(temp.year)
        temp = nearest_before(df.index,temp_str)
        previous_close = df.loc[temp,currency]
        
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
        #print('previous close price is ' + str(previous_close))
    new_entry_price = 0
    #original size is defined previously; new_trade_size is the trades made on the day
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
                #print('new size is ' + str(size))
            
            result.at[j, 'PnL'] = profit
            profit = 0
            
        else: 
            #print('No')
            close_price = df.ix[j][currency]
            #print("close price on this no-trade day is " + str(close_price))
            profit = (close_price - old_entry_price)*size
            result.at[j, 'PnL'] = profit
            
    
    return result 



# function calculate PnL of a portfolio 
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
        

# function calculate PnL of all portfolios of a trader 
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

# function calculate PnL of all portfolios of a team 
def pnl_team(start,end,team_df,df):
    traders = team_df['User'].unique()
    
    for i in range(len(traders)):
        trader = traders[i]
        if i ==0:
            trader_df = team_df.groupby('User').get_group(trader)
            result = pnl_trader(start,end,trader_df,df)
        else:
            temp = pnl_trader(start,end,trader_df,df)
            try:
                result = pd.concat([result, temp]).groupby('Date', as_index=True).sum()
            except ValueError:
                return None
        return result  



# function calculate Sharpe Ratio
def cal_sharpe_ratio(pnl_df):
    mu = pnl_df.PnL.mean()
    sd = pnl_df.PnL.std()
    try:
        result = mu/sd
    except ZeroDivisionError:
        return 0
    
    return round(result,2)

# function calculate Sortino Ratio
def cal_sortino_ratio(pnl_df):
    mu = pnl_df.PnL.mean()
    sd = pnl_df.loc[(pnl_df['PnL'] <= 0)].PnL.std()
    try:
        result = mu/sd
    except ZeroDivisionError:
        return 0
    return round(result,2)
                     

# function calculate Hit Ratio
def cal_hit_ratio(pnl_df):
    winning = pnl_df.loc[(pnl_df['PnL'] > 0)].shape[0]
    total = pnl_df.shape[0]
    try:
        result = winning/total
        return round(result,2)
    except ZeroDivisionError:
        print ("No losing trade")
        return winning
