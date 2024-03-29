import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime as dt
from datetime import date
import dash_table
from textwrap import dedent as d
import plotly.express as px
from os import listdir
from os.path import isfile, join
from Data_Computation import *
from dateutil import relativedelta

app = dash.Dash(__name__)
csv_path = 'user_csv'

####################################
####  1. DATA INTAKE FUNCTIONS  ####
####################################

# function to read the price data
def read_bloomberg(file_name):
    df = pd.read_excel(file_name)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.set_index('Date', inplace=True)
    df = df.sort_index()
    return df

df = read_bloomberg('Bloomberg Data.xlsx')

# function to read products/currencies
def get_currency():
    currency = list(df.columns)
    currency = [name for name in currency if 'Unnamed' not in name]
    currency = [name for name in currency if name.lower() != 'date']
    currency = [name if name.find(' ') == -1 else name[:name.find(' ')] for name in currency]
    return currency

# get the currency list for tab 2 dropdown
currency_list = get_currency()

# function to find the starting date of the last three months. including current month for datepicker range
def get_last_3months():
    last3month = date.today() - relativedelta.relativedelta(months=2)
    return dt(last3month.year, last3month.month, 1).date()

# Initialise trade table
## helper function used by load_data() method to load user transaction records
def read_data(user):
    file_names = [f for f in listdir(csv_path) if isfile(join(csv_path, f)) and f[-4:]=='.csv']
    
    trade_table = pd.DataFrame(columns = ['Portfolio','Type of Trade','Direction','Product', 
                                      'Price', 'Size/Notional', 'Tenor', 'Amount to Risk',
                                      'Timeframe', 'Strategy Type','Timestamp','User'])
    
    if user=='all':
        for trader in file_names:
            cur=pd.read_csv(join(csv_path, trader))
            trade_table = trade_table.append(cur,sort=False,ignore_index=True)
    elif user+'.csv' in file_names:
        trade_table = pd.read_csv(join(csv_path, user+'.csv'))
    
    trade_table['Timestamp'] = pd.to_datetime(trade_table.Timestamp).apply(lambda x: x.date())
    
    return trade_table

def load_data():
    trade_table = read_data('all')
    portfolio_list = sorted(trade_table.Portfolio.unique())
    user_list = sorted(trade_table.User.unique())
    return trade_table, portfolio_list, user_list

trade_table, portfolio_list, user_list = load_data()
ratio_list = ['Sharpe Ratio', 'Hit Ratio', 'Sortino Ratio']

##########################################
#### 2. DATA MANIPULATION FUNCTIONS   ####
##########################################

######################## function for tab 2 ########################

# building the display table for all trades
# input: df, user_name
# ouput: dash_table.DataTable
def tab2_build_table(trade_table, user):
    trade_df = trade_table[trade_table.User==user]
    return dash_table.DataTable(
        id = 'tab2_trade_table',
        columns = [{"name": i, "id": i} for i in trade_df.columns],
        data = trade_table.to_dict('records'),
        style_header={'backgroundColor': 'rgb(30, 30, 30)'},
        style_cell={
            'backgroundColor': '#22252b',
            'textAlign': 'center',
            'color': 'white'
        },
        sort_action = 'custom',
        sort_mode = 'multi',
        sort_by = []
    )    

######################## function for tab 3 ########################

## function for table (helper function for tab3_build_table() method)
# input: df (records all information of trades maded by all users), username
# output: df (current positions grouped by product names for the specified trader)
def tab3_get_data(trade_table, user):
    ### filter to get user data
    trade_table['Size/Notional'] = trade_table['Size/Notional'].astype('int')
    trade_table = trade_table[trade_table.User==user]
    
    
    #create an empty df to hold data
    groupby_product = pd.DataFrame(columns=['Portfolio','Size/Notional'])
    groupby_product.index.name = 'Product'

    for p in trade_table.Portfolio.unique():
        #first filter out transactions related to one portfolio and get only the product and sum up the size for each product
        temp = trade_table[trade_table['Portfolio']==p][['Product','Size/Notional']].groupby('Product').sum()
        #insert the column to indicate the portfolio
        temp.insert(0,'Portfolio',temp.size*[p])
        groupby_product = groupby_product.append(temp)
    
    groupby_product = groupby_product.reset_index(level=['Product'])
    groupby_product = groupby_product[['Portfolio','Product','Size/Notional']]
    groupby_product = groupby_product.sort_values(by=['Portfolio', 'Product'])
    return groupby_product

# input: df, username (using tab3_get_data to get the table data and add formatting)
# ouput: dash_table.DataTable 
def tab3_build_table(trade_table, user):
    #trade_table = pd.DataFrame.from_dict(trade_table_store)
    data_df = tab3_get_data(trade_table, user)
    return dash_table.DataTable(
        id = 'tab3 product table',
        columns = [{"name": i, "id": i} for i in data_df.columns],
        data = data_df.to_dict('records'),
        style_header={'backgroundColor': 'rgb(30, 30, 30)'},
        style_cell={
            'backgroundColor': '#22252b',
            'textAlign': 'center',
            'color': 'white'
        },
        sort_action = 'custom',
        sort_mode = 'multi',
        sort_by = []
    )

######################## function for tab 4 ########################
    
## build individual view for PnL graph 
# input: start date, end date, df
# output: figure
def tab4_build_idv_graph(start, end,trade_table_store):
    trade_table = pd.DataFrame.from_dict(trade_table_store)
    temp_df = trade_table
    trans_preprocessing(temp_df)

    users = list(temp_df['User'])
    users = np.unique(users)

    pnl_traders = {}
    for user in users:
        trader_df = temp_df.groupby('User').get_group(user)
        pnl_temp = pnl_trader(start,end,trader_df,df)
        pnl_temp.reset_index(level=0,inplace=True)
        pnl_traders[user] = pnl_temp

    fig = {'data': [go.Scatter(x=pnl_traders[user]['Date'], 
                               y=pnl_traders[user]['PnL'],
                               mode = 'lines+markers',
                               name = user) for user in users],
            'layout':{"paper_bgcolor": "rgba(0,0,0,0)",
                      "plot_bgcolor": "rgba(0,0,0,0)",
                      "font": {"color": "lightgrey"},
                      "margin": {'t': 30},
                      "xaxis": dict(title= 'Time'),
                      "yaxis": dict(title= 'PnL')}
        }
    return fig

## build team aggregated view for PnL graph 
# input: start date, end date, df
# output: figure
def tab4_build_agg_graph(start, end, trade_table_store):
    trade_table = pd.DataFrame.from_dict(trade_table_store)
    temp_df = trade_table
    trans_preprocessing(temp_df)

    users = list(temp_df['User'])
    users = np.unique(users)

    pnl = pnl_team(start,end,temp_df,df)
    pnl.reset_index(level=0,inplace=True)
            
    X = pnl['Date']
    Y = pnl['PnL']

    fig = {'data': [go.Scatter(x=X, 
                               y=Y,
                               # mode = 'lines+markers',
                               fill = 'tozeroy',
                               )],

            'layout':{"paper_bgcolor": "rgba(0,0,0,0)",
                      "plot_bgcolor": "rgba(0,0,0,0)",
                      "font": {"color": "lightgrey"},
                      "margin": {'t': 30},
                      "xaxis": dict(title= 'Date'),
                      "yaxis": dict(title= 'PnL')}
            }
            
    return fig

#####################################
####  3. DATA DISPLAY FUNCTIONS  ####
#####################################

######################## tab 2 components ########################

# building the input fileds, including text boxes, dropdowns and datepicker for tab 2 (initializer)
def tab2_build_inputs(): 
    
    # first row of input fields
    div_1 = html.Div([ 
                        html.Div( # user field
                                dcc.Input(id = 'user', className = "text_input", type = 'text', placeholder = 'User*'),
                                style = {'margin-right': 60}),
                        html.Div( # portfolio field
                                dcc.Input(id = 'portfolio', className = "text_input", type = 'text', placeholder = 'Portfolio*'),
                                style = {'margin-right': 60}),
                        html.Div( # transaction datepicker
                                dcc.DatePickerSingle(
                                    id = 'timestamp',
                                    max_date_allowed = dt.now().date(),
                                    placeholder = 'Date*'),
                                style = {'width': 200, 'margin-right': 60}),
                        html.Div( # trade type field
                                dcc.Input(id = 'type', type = 'text', className = "text_input", placeholder = 'Type of Trade'),
                                style = {'margin-right': 60}),        
                        
                    ], 
                    style = {'margin-top': 10, 'margin-bottom': 30,
                             'display': 'flex', 'justify-content': 'flex-start'})
    
    # second row of input fields
    div_2 = html.Div([ 
                        html.Div( # product/currency dropdown using the product list obtained earlier
                                dcc.Dropdown(id='product',
                                             options=[{'label': curr, 'value': curr}for curr in currency_list],
                                             placeholder = 'Product*'),
                                style = {'width': 200, 'margin-right': 60}),
                        html.Div( # direction dropdown, long or short
                                dcc.Dropdown(id='direction',
                                             options=[{'label': 'Long', 'value': 'Long'},
                                                      {'label': 'Short', 'value': 'Short'}],
                                             placeholder = 'Direction*'),
                                style = {'width': 200, 'margin-right': 60}),
                        html.Div( # price field, number input
                                dcc.Input(id = 'price', type = 'number',  className = "text_input", placeholder = 'Price*'),
                                style = {'margin-right': 60}),
                        html.Div( # size of transaction field, number input
                                dcc.Input(id = 'size', type = 'number',  className = "text_input", placeholder = 'Size/Notional*'),
                                style = {'margin-right': 60}),
                    ], 
                    style = {'margin-top': 10, 'margin-bottom': 30,
                             'display': 'flex', 'justify-content': 'flex-start'})
    
    # third row of input fields     
    div_3 = html.Div([ 
                        html.Div( # tenor field
                                dcc.Input(id = 'tenor', type = 'text',  className = "text_input", placeholder = 'Tenor'),
                                style = {'margin-right': 60}),
                        html.Div( # risk tolerance field, number
                                dcc.Input(id = 'risk', type = 'number',  className = "text_input", placeholder = 'Amount to Risk'),
                                style = {'margin-right': 60}),
                        html.Div( # timeframe field
                                dcc.Input(id = 'timeframe', type = 'text',  className = "text_input", placeholder = 'Timeframe'),
                                style = {'margin-right': 60})
                    ], 
                    style = {'margin-top': 10, 'margin-bottom': 30,
                             'display': 'flex', 'justify-content': 'flex-start'})
    
    # last row of input
    div_4 = html.Div([ # strategy field 
                    dcc.Input(id = 'strategy', type = 'text',  placeholder = 'Strategy Type', style = {'width': 800, 'height': 100})
                    ], style = {'margin-top': 10, 'margin-bottom': 30,
                             'display': 'flex', 'justify-content': 'flex-start'})
        
    
    return html.Div([div_1, div_2, div_3, div_4], style = {'margin': 'auto', 'width': '85%'}) 


######################## tab 3 components ########################

## function for building ratio containers
# helper function used by tab3_build_ratio to do formatting for individual container
def tab3_ratio_box(ratio_name):
    r_id = ratio_name.lower().replace(' ','_')
    return html.Div([
        html.H6(id = r_id + "_text"), html.P(ratio_name)],
        id=r_id,
        className="mini_container",
        style = {'margin-bottom': 20, 'margin-left': 80})

def tab3_build_ratio(ratio_list):
    result=[]
    for ratio in ratio_list:
        result.append(tab3_ratio_box(ratio))
    return result

####################
# Build top banner # 
####################
def build_banner():
    return html.Div(
                id = "banner",
                className = "banner",
                children = [
                    html.Div(
                        id = "title",
                        className = "banner-title",
                        children = [
                                    html.Img(className = "banner-logo", src=app.get_asset_url("logo.png")), # logo of NatWest
                                    html.H3('NatWest Risk Analytics Platform') # title of platform
                        ]
                    ),
                    
                    html.Div( # user dropdown selection
                        id = "login",
                        className = "banner-login",
                        children = [
                                    html.H5("Hello"), 
                                    dcc.Dropdown(id  = "user_login",
                                                 className = 'banner-dropdown',
#                                                 options = ([{'label': user, 'value': user}for user in user_list]),
#                                                 value = user_list[0]
                                    )
                        ]
                    )
                ]
                    
           )

######################## Development of respective tabs ########################

############################
# Tab 1 Individual Summary # 
############################                     
                        
def init_tab_1():
    return dcc.Tab(label = 'Individual Summary', className = 'custom-tab', selected_className="custom-tab--selected", 
                   children = [           
                        html.Div([                    
                            html.Div([
                                   # date selection
                                   html.Div([
                                       html.Div([html.H6('Select Date:')], style = {'margin-right': 30}),
                                       dcc.DatePickerRange(
                                            id = 'tab1_date_range',
                                            display_format='Y-M-D',
                                            end_date = dt.now().date(),
                                            start_date = get_last_3months(),
                                            max_date_allowed = dt.now().date(),
                                            min_date_allowed = get_last_3months()
                                       )],
                                       className = 'row',
                                       style = {'display': 'flex', 'flex-direction': 'row',
                                                'margin-right':50}
                                   ),
                                
                                # summary of total portfolios and PnL 
                                   html.Div([
                                        
                                        html.Div([
                                            html.Div(
                                                    [html.H6(id = "tab1_total_pnl"), html.P('Total PnL')],
                                                    className = "mini_container",
                                                    style = {'margin-right':50})]),
                                            
                                        html.Div([
                                            html.Div(
                                                    [html.H6(id = "tab1_total_portfolio"), html.P('Total Portfolios')],
                                                    className = "mini_container",
                                                    style = {'margin-right':50})]),
                                    ],
                                    style = {'display': 'flex', 'flex-direction': 'row'}
                                  ),
              
                            ], 
                            style = {'margin':'auto', 'margin-top': 30, 'margin-bottom': 30, 'width': '90%',
                                     'display': 'flex', 'flex-direction': 'row', 'justify-content': 'flex-start'}),
                            
                            # PnL graph
                            html.Div([
                                    
                                    html.Div( # title bar
                                        className = "row chart-top-bar",
                                        children = [
                                            html.Div(
                                                className="inline-block chart-title",
                                                children = "PnL Performance",
                                            )
                                    ]),
                                    
                                    dcc.Graph(id = 'tab1_pnl_performance') # PnL area chart
                            ],
                            style = {'padding': 10, 'margin': 'auto','width': '80%'}),
                        ],
                        style = {'margin-left': 30, 'margin-right': 30, 'margin-top': 20, 'margin-bottom': 30})    
                ])

#########################
# Tab 2 Add Transaction # 
######################### 

def init_tab_2():
    
    return dcc.Tab(label='Add Transaction', className = 'custom-tab', selected_className="custom-tab--selected", children = [
            html.Div([     
                
                html.Div(id='input_section', children = tab2_build_inputs()), # using the init funciton earlier to build input field
                
                # confirm dialog with button for both add and clear action, only shown when button is clicked                             
                html.Div([ 
                    # confirm dialog with button for add transaction action 
                    dcc.ConfirmDialogProvider(
                        children = html.Button(
                            'Add',style = {'margin-left': 30, 'width': 100,'text-align': 'center'}
                        ),
                        id = 'add',
                        message = 'Are you sure to continue?'),
                    
                    # confirm dialog with button for clear input action 
                    dcc.ConfirmDialogProvider(
                        children = html.Button(
                            'Clear',style = {'width': 100, 'text-align': 'center'}
                        ),
                        id = 'reset',
                        message = 'Are you sure to clear all inputs?'),
                ],style = {'padding': 10, 'display': 'flex', 'flex-direction': 'row-reverse','width': '90%',}),
                
                # confirm dialog, only display when add button is clicked without all required inputs filled in
                # serve to prevent trades with missing information to be added                  
                html.Div(
                    dcc.ConfirmDialog(id = 'confirm', message = 'Please fill in all * fields!')
                ),
                
                # dash table for display of trades accoridng to the user selected
                html.Div(id = 'tab2_table',
                         # initializa to display the trades of the first user in the user list
                         children = tab2_build_table(trade_table, user_list[0]), 
                         style = {'height': 400,'margin': 'auto', 'width': '90%', 'margin-top': 15})  
            ], style = {'margin-left': 30, 'margin-right': 30, 'margin-top': 20, 'margin-bottom': 30 })
    ])

#############################
# Tab 3 Individual Analysis # 
############################# 

def init_tab_3():
    selector_date = html.Div([
        html.Div([
            html.H6('Select Date:')], 
            style = {'margin-left': 10, 'margin-right': 30}),
        dcc.DatePickerRange(
            id = 'tab3_date_range',
            display_format='Y-M-D',
            end_date = dt.now().date(),
            start_date = get_last_3months(),
            max_date_allowed = dt.now().date(),
            min_date_allowed = get_last_3months()
        )],
        className = 'row',
        style = {'margin':'auto','margin-bottom': 30, 'width': '90%',
                 'display': 'flex', 'flex-direction': 'row', "margin-top": 30}
    )
    
    selector_portfolio = html.Div([
#        html.H6('Select Portfolio'),
        dcc.Dropdown(id = 'tab3 portfolio')],
        style = {'width':300})
    
    ratio_container = html.Div(
        id="info-container",
        children = tab3_build_ratio(ratio_list),
        className="four columns",
        style = {'padding': 10})
    
                
    pnl_header = html.Div(
                    className = "row chart-top-bar",
                    children = [
                            html.Div(
                                className="inline-block chart-title",
                                children = "PnL Performance",
                            ),
                                    
                            html.Div(
                                className = "graph-top-right inline-block",
                                children = [selector_portfolio],
                                style = {'width': 300}),
                    ])
    
    pnl_graph = dcc.Graph(
        id='tab3 daily pnl', 
        figure = go.Figure(
            layout = go.Layout({"paper_bgcolor": "rgba(0,0,0,0)",
                                "plot_bgcolor": "rgba(0,0,0,0)",
                                "font": {"color": "lightgrey"},
                                "margin": {'t': 30}}))) 
    
    pnl_section = html.Div([
        pnl_header,pnl_graph], 
        style = {'margin': 'auto', 'width': '80%'})
    
    table = html.Div(
        id='tab3_table',
        children = tab3_build_table(trade_table,user_list[0]),
        className = 'eight columns',
        style = {'height': 400, 'padding': 10})
    
    return dcc.Tab(label='Individual Analysis', className = 'custom-tab', selected_className="custom-tab--selected", 
                   children = [
                       html.Div([ 
                            html.Div([selector_date]),  
                           
                           html.Div([pnl_section], 
                                    style = {'margin-top': 10, 'margin-bottom': 30}),  
                           
                           html.Div([ratio_container, table],
                                    className = "twelve columns",
                                    style = {'margin': 'auto', 'margin-top': 10, 'margin-bottom': 30, 'width': '90%'})
                       ],
                           style = {'margin-left': 30, 'margin-right': 30, 'margin-top': 20, 'margin-bottom': 30}
                       )
                  ]
            )

######################
# Tab 4 Team Summary # 
###################### 

def init_tab_4():
    return dcc.Tab(label='Team Summary', className = 'custom-tab', selected_className="custom-tab--selected", children = [
           html.Div([ 
                
                ### select date range
                html.Div([
                           html.Div([html.H6('Select Date:')], style = {'margin-right': 30}),
                           dcc.DatePickerRange(
                                id = 'tab4_date_range',
                                display_format='Y-M-D',
                                end_date = dt.now().date(),
                                start_date = get_last_3months(),
                                max_date_allowed = dt.now().date(),
                                min_date_allowed = get_last_3months()
                           )],
                           style = {'margin':'auto', 'margin-bottom': 30, 'width': '90%',
                                   'display': 'flex', 'flex-direction': 'row', "margin-top": 30}
                ),
                
                ###text boxes to display ratio for selected porfolio
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(id="total_pnl_text_tab4"), html.P("Total PnL")],
                            id="total_pnl_tab4",
                            className = "mini_container"),
                    ], style = {'margin-right': 50}),
                    
                    html.Div([
                        html.Div([
                            html.H6(id="no_of_porfolios_text_tab4"), html.P("Number of Portfolios")],
                            id="no_of_porfolios_tab4",
                            className = "mini_container"),
                    ],style = {'margin-right': 50}),
                                
                    html.Div([            
                        html.Div(
                            [html.H6(id="last_week_trades_text_tab4"), html.P("Last Week Trades")],
                            id="last_week_trades_tab4",
                            className = "mini_container"),
                    ],style = {'margin-right': 50})], 
                    id="info-container_1_tab4",
                    style = {'margin-top': 10, 'margin-bottom': 30,
                             'display': 'flex', 'justify-content': 'center'}),

                html.Div([
                    html.Div([
                        html.Div(
                            [html.H6(id="sortino_ratio_text_tab4"), html.P("Sortino Ratio")],
                            id="sortino_ratio_tab4",
                            className = "mini_container"),
                    ], style = {'margin-right': 50}),
    
                    html.Div([
                        html.Div(
                            [html.H6(id="sharpe_ratio_text_tab4"), html.P("Sharpe Ratio")],
                            id="sharpe_ratio_tab4",
                            className = "mini_container"),
                    ], style = {'margin-right': 50}),
                    
    
                    html.Div([
                        html.Div(
                            [html.H6(id="hit_ratio_text_tab4"), html.P("Hit Ratio")],
                            id="hit_ratio_tab4",
                            className = "mini_container"),
                    ], style = {'margin-right': 50})],
                    id="info-container_tab4",
                    style = {'margin-top': 10, 'margin-bottom': 30, 'display': 'flex', 'justify-content': 'center'}),
            
                ### Team PnL performance graph 
                html.Div([
                        html.Div(
                            className = "row chart-top-bar",
                            children = [
                                html.Div(
                                    className="inline-block chart-title",
                                    children = "Team PnL Performance",
                                ),
                                        
                                html.Div(
                                    className = "graph-top-right inline-block",
                                    children = [
                                        html.Div([
                                            #html.H6('Select Timeframe'),
                                            dcc.Dropdown(id  = "tab 4 switch view",
                                             options=[
                                                {'label': 'Individuals', 'value': 'Individuals'},
                                                {'label': 'Aggregated', 'value': 'Aggregated'}],
                                             value = 'Aggregated'
                                        )],
                                        style = {'width': 300}),
                                    ])
                        ]),
                            
                        dcc.Graph(id='tab4 graphs'),
                    ], 
                    style = {'margin':'auto', 'width': '80%'}) 

            ], style = {'margin-left': 30, 'margin-right': 30, 'margin-top': 20, 'margin-bottom': 30})
        ])
                                            
#############################
#### 4. DASHBOARD LAYOUT ####                  
#############################
                                            
app.layout = html.Div(
    children = [
        # banner
        build_banner(), 
        
        # individual tabs
        dcc.Tabs(id = "tabs", 
                 className = 'custom-tabs', 
                 children = [
                     init_tab_1(),
                     init_tab_2(),
                     init_tab_3(),
                     init_tab_4()
        ]),
        
        dcc.Store(id='trade_table_store'),
        dcc.Interval(# scans the shared folder and reload all transaction data
            id='interval-component',
            interval=20*1000, # every 20 seconds
            n_intervals=5
        )
    ]
)

###########################################################
#### 5. INTERACTIONS BETWEEN COMPONENTS WITH CALLBACKS ####                  
###########################################################
                               
######################## general ########################

### read trader transactions by interval
@app.callback(Output('trade_table_store', 'data'),
              [Input('interval-component', 'n_intervals')])
def update_data_source(n): 
    trade_table, portfolio_list, user_list = load_data()
    return trade_table.to_dict('records')


### update table user options according when new data comes in
# input: trade table data store
# state: selected value of user
# output: list of options of users, selected value of user
@app.callback(
   [Output('user_login', 'options'),
    Output('user_login', 'value')],
   [Input('trade_table_store', 'data')],
   [State('user_login', 'value')])
def update_userlist(data_dict, login):
    trade_table = pd.DataFrame.from_dict(data_dict)
    user_list = sorted(trade_table.User.unique())
    user_list.sort()
    
    # during initialization, no user would be selected. in this case, the first user in the list is selected
    if login == None: 
        login = user_list[0]
        
    options = [{'label': user, 'value': user}for user in user_list]
    return options, login

######################## tab 1 ########################

### tab 1 display pnl charts, portfolios and total pnl
# input: user selection, date selection, trade data store, bloomberg data
# output: pnl figure, number of total pnl, number of portfolios
@app.callback([Output('tab1_pnl_performance', 'figure'),
               Output('tab1_total_pnl', 'children'),
               Output('tab1_total_portfolio', 'children')],
              [Input('user_login', 'value'),
               Input('tab1_date_range', 'start_date'),
               Input('tab1_date_range', 'end_date'),
               Input('trade_table_store', 'data'),
               Input('bloomberg_store', 'data')])
def update_tab1_pnl(user, start_date, end_date, data_dict, bloomberg_dict):
    #df = pd.DataFrame.from_dict(bloomberg_dict)
    df = read_bloomberg('Bloomberg Data.xlsx')
    trade_table = pd.DataFrame.from_dict(data_dict)
    start_date = dt.strptime(start_date, "%Y-%m-%d").strftime('%d/%m/%Y')
    end_date = dt.strptime(end_date, "%Y-%m-%d").strftime('%d/%m/%Y')
    
    transaction = trade_table[trade_table['User'] == user]
    portfolios = list(transaction['Portfolio'])
    portfolios = np.unique(portfolios)
    trans_preprocessing(transaction)

    pnl = pnl_trader(start_date, end_date, transaction, df) 

    pnl.reset_index(level=0, inplace=True)
    figure = {'layout': {"paper_bgcolor": "rgba(0,0,0,0)",
                       "plot_bgcolor": "rgba(0,0,0,0)",
                       "font": {"color": "lightgrey"},
                       "margin": {'t': 30},
                       "xaxis": dict(title= 'Date'),
                       "yaxis": dict(title= 'PnL')
                        },
            'data': [
                        go.Scatter(
                        #x = pnl[pnl['Portfolio'] == portfolio]['Product'],
                        x = pnl['Date'],
                        #y = pnl[pnl['Portfolio'] == portfolio]['Price'],
                        y = pnl['PnL'],
                        fill = 'tozeroy',)                    
                    ]}
    return figure, round(pnl['PnL'].sum(),2), portfolios.size

######################## tab 2 ########################
    
### tab 2 clear inputs
# input: click on clear button
# state: original state of input section
# output: rebuilt input section
@app.callback(
         Output('input_section', 'children'),
        [Input('reset', 'submit_n_clicks')],
        [State('input_section', 'children')])
def clear_content(reset, origin):
    if reset: 
        # only rebuild the section when the button is clicked
        return tab2_build_inputs()
    return origin

### tab 2 update dashtable according to sorting criteria selected
# input: trade table data store, selected value of user, selected sorting criteria
# output: sorted data to be fed to the table components
@app.callback(
    Output('tab2_trade_table', 'data'),
    [Input('trade_table_store', 'data'),
     Input('user_login', 'value'),
     Input('tab2_trade_table','sort_by')])
def update_table(data_dict, user, sort_by):
    trade_table = pd.DataFrame.from_dict(data_dict)
    trade_user = trade_table[trade_table.User == user]
    
    if len(sort_by):
        trade_df = trade_user.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[col['direction'] == 'asc' for col in sort_by],
            inplace=False)
    else: 
        trade_df = trade_user
    return trade_df.to_dict('records')

### tab 2 add transaction
# input: click on add button
# state: selected value of user, trade table data store
#        filled input for user, portfolio, product, type, date, direction, price, size, tenor, risk tolerance, timeframe, strategy
# output: confirm dialog to remind users of unfilled fields if there is any 
# else, the new trade will be written to the csv
@app.callback(
     Output('confirm', 'displayed'),
    [Input('add', 'submit_n_clicks')],
    [State('user_login', 'value'),
     State('trade_table_store', 'data'),
     State('portfolio', 'value'),
     State('product', 'value'),
     State('type', 'value'),
     State('direction', 'value'),
     State('price', 'value'),
     State('size', 'value'),
     State('tenor', 'value'),
     State('risk', 'value'),
     State('timeframe', 'value'),
     State('strategy', 'value'),
     State('timestamp', 'date'),
     State('user', 'value')])
def add_trans(submit_n_clicks, login, data_dict, portfolio, product,  
              type, direction, price, size, tenor, 
              risk, timeframe, strategy, timestamp, user):
    
    trade_table = pd.DataFrame.from_dict(data_dict)
    
    # check if all required fields are filled after the button is clicked
    if submit_n_clicks:
        inputs = [portfolio, product, direction, price, size, timestamp, user]
        for input in inputs:
            if input == None: # if not, the confirm dialog will be displayed
                return True
            
        index = len(trade_table)
        # add new transaction to the current table 
        trade_table.loc[index, 'Portfolio'] = portfolio
        trade_table.loc[index, 'Type of Trade'] = type
        trade_table.loc[index, 'Product'] = product
        trade_table.loc[index, 'Direction'] = direction
        trade_table.loc[index, 'Price'] = price
        trade_table.loc[index, 'Size/Notional'] = size
        trade_table.loc[index, 'Tenor'] = tenor
        trade_table.loc[index, 'Amount to Risk'] = risk
        trade_table.loc[index, 'Timeframe'] = timeframe
        trade_table.loc[index, 'Strategy Type'] = strategy
        trade_table.loc[index, 'Timestamp'] = timestamp
        trade_table.loc[index, 'User'] = user
        
        # write to csv and do not display the confirm dialog
        trade_table[trade_table.User == user].to_csv(join(csv_path, user + '.csv'), index = False)
        return False
    return False

######################## tab 3 ########################

###tab3 portfolio dropdown by user
# input: selected trader name, trade data 
# output: the list of portfolios found under this trader. Displayed in the tab3 dropdown to select portfolio
@app.callback(Output('tab3 portfolio', 'options'),
              [Input('user_login', 'value'),
               Input('trade_table_store', 'data')])
def update_portfolio(user, data_dict):
    data_df = pd.DataFrame.from_dict(data_dict)
    data = data_df[data_df.User==user]
    pfl_list = sorted(data.Portfolio.unique())
    return [{'label': 'Portfolio '+i, 'value': i} for i in pfl_list]

###tab3 table
# input: trade table, selected trader name, sort by which column of the table
# output: the table in the tab3 displaying the current positions of all products
@app.callback(
    Output('tab3 product table', 'data'),
    [Input('trade_table_store', 'data'),
     Input('user_login', 'value'),
     Input('tab3 product table','sort_by')
    ])
def update_table(data_dict, user, sort_by):
    data = pd.DataFrame.from_dict(data_dict)
    df = tab3_get_data(data, user)
    
    if len(sort_by):
        trade_df = df.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[col['direction'] == 'asc' for col in sort_by],
            inplace=False)
    else: trade_df = df
    
    return trade_df.to_dict('records')

###tab3 update graph
# input: selected start date in tab3 slider,
#        selected end date in the tab3 slider,
#        trade table,
#        selected user name
#        selected portfolio name
# output: the calculated daily pnl for the selected user and portfolio for the selected dates
@app.callback(Output('tab3 daily pnl', 'figure'),
              [Input('tab3_date_range', 'start_date'),
               Input('tab3_date_range', 'end_date'),
               Input('trade_table_store', 'data'),
               Input('user_login', 'value'),
               Input('tab3 portfolio', 'value')])
def update_tab3_daily(start, end, data_dict, user, portfolio):
    df = read_bloomberg('Bloomberg Data.xlsx')
    trade_table = pd.DataFrame.from_dict(data_dict)
    temp_df = trade_table.loc[(trade_table['Portfolio']==portfolio) 
                              & (trade_table['User'] == user)]
    trans_preprocessing(temp_df)
    
    start = dt.strptime(start, "%Y-%m-%d").strftime('%d/%m/%Y')
    end = dt.strptime(end, "%Y-%m-%d").strftime('%d/%m/%Y')

    pnl = pnl_portfolio(start, end, temp_df, portfolio, df)  
    pnl.reset_index(level=0, inplace=True)
    X = pnl['Date']
    Y = pnl['PnL']
    
    return {'layout': {"paper_bgcolor": "rgba(0,0,0,0)",
                       "plot_bgcolor": "rgba(0,0,0,0)",
                       "font": {"color": "lightgrey"},
                       "margin": {'t': 30},
                       "xaxis": dict(title= 'time',range=[min(X),max(X)]),
                       "yaxis": dict(title= 'price', range=[min(Y),max(Y)])
                      },
            'data': [go.Scatter(x = X, y = Y, fill = 'tozeroy',)]
           }  

###tab3 update ratios
# input: start date, end date, trade table, user name
# output: the computed ratios for the selected user
@app.callback([Output('sharpe_ratio_text', 'children'),
               Output('hit_ratio_text', 'children'),
               Output('sortino_ratio_text', 'children')],
              [Input('tab3_date_range', 'start_date'),
               Input('tab3_date_range', 'end_date'),
               Input('trade_table_store', 'data'),
               Input('user_login', 'value')])
def update_tab3_ratio_list(start, end, data_dict, user):
    trade_table = pd.DataFrame.from_dict(data_dict)
    temp_df = trade_table.loc[(trade_table['User'] == user)]
    trans_preprocessing(temp_df)
    
    start = dt.strptime(start, "%Y-%m-%d").strftime('%d/%m/%Y')
    end = dt.strptime(end, "%Y-%m-%d").strftime('%d/%m/%Y')

    pnl = pnl_trader(start, end, temp_df, df)  

    sharpe_ratio = 0
    hit_ratio = 1
    sortino_ratio = 2

    sharpe_ratio = cal_sharpe_ratio(pnl)
    hit_ratio = cal_hit_ratio(pnl)
    sortino_ratio = cal_sortino_ratio(pnl)
    
    return sharpe_ratio, hit_ratio, sortino_ratio

######################## tab 4 ########################

# tab 4 team PnL graphs and ratio computation
# inputs: selected start date in tab4 slider,
#        selected end date in the tab4 slider,
#        individual/aggregated switch view option in tab4,
#        trade table
# output: Team PnL graphs in tab4,
#         the computed ratios for team performance for the selected date range

@app.callback([Output('tab4 graphs', 'figure'),
               Output('total_pnl_text_tab4', 'children'),
               Output('no_of_porfolios_text_tab4', 'children'),
               Output('last_week_trades_text_tab4', 'children'),
               Output('sortino_ratio_text_tab4', 'children'),
               Output('sharpe_ratio_text_tab4', 'children'),
               Output('hit_ratio_text_tab4', 'children')],
              [Input('tab4_date_range', 'start_date'),
               Input('tab4_date_range', 'end_date'),
               Input('tab 4 switch view','value'),
               Input('trade_table_store', 'data')])
def update_tab4_graphs(start,end,view,trade_table_store):
    df = read_bloomberg('Bloomberg Data.xlsx')
    total_pnl = 0
    number_of_portfolios = 1
    last_week_trades = 2
    sortino_ratio = 3
    sharpe_ratio = 4
    hit_ratio = 5

    start = dt.strptime(start, "%Y-%m-%d").strftime('%d/%m/%Y')
    end = dt.strptime(end, "%Y-%m-%d").strftime('%d/%m/%Y')

    trade_table = pd.DataFrame.from_dict(trade_table_store)
    temp_df = trade_table
    trans_preprocessing(temp_df)
    pnl_df = pnl_team(start, end, temp_df, df)


    sharpe_ratio = cal_sharpe_ratio(pnl_df)
    sortino_ratio = cal_sortino_ratio(pnl_df)
    hit_ratio = cal_hit_ratio(pnl_df)
    number_of_portfolios = len(temp_df.Portfolio.unique())
    total_pnl = round(pnl_df.PnL.sum(),2)
    last_week_trades = temp_df.shape[0]


    if view == 'Individuals':
        fig = tab4_build_idv_graph(start, end,trade_table_store)
        return fig, total_pnl, number_of_portfolios, last_week_trades, sortino_ratio, sharpe_ratio, hit_ratio
    else:
        fig = tab4_build_agg_graph(start, end, trade_table_store)
        return fig, total_pnl, number_of_portfolios, last_week_trades, sortino_ratio, sharpe_ratio, hit_ratio

############################
#### 6. RUN APPLICATION ####                  
############################

if __name__ == '__main__':
    app.debug = True
    app.run_server()
