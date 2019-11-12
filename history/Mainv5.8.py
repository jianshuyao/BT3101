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

def read_bloomberg(file_name):
    df = pd.read_excel(file_name)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.set_index('Date', inplace=True)
    df = df.sort_index()
    return df

df = read_bloomberg('Bloomberg Data.xlsx')

def get_currency():
    currency = list(df.columns)
    currency = [name for name in currency if name[0:7] != "Unnamed"]
    currency = [name for name in currency if name.lower() != 'date']
    currency = [name if name.find(' ') == -1 else name[:name.find(' ') != -1] for name in currency]
    return currency

currency_list = get_currency()

###### DATA INTAKE ########################
# Initialise trade table
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


###### DATA Processing Functions ########################
### function for tab 2
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
                
def get_last_3months():
    last3month = date.today() - relativedelta.relativedelta(months=2)
    return dt(last3month.year, last3month.month, 1).date()

### function for tab 3
## function for table
# input: df
# output: df
def tab3_get_data(trade_table, user):
    ### filter to get user data
    trade_table['Size/Notional'] = trade_table['Size/Notional'].astype('int')
    trade_table = trade_table[trade_table.User==user]
    
    ### 
    #if start:
    #    trade_table = trade_table[trade_table.Timestamp>=start]
    #if end:
    #    trade_table = trade_table[trade_table.Timestamp<=end]
    
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

# input: df
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

## function for ratios
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

##### Build top banner ######################################
def build_banner():
    return html.Div(
                id = "banner",
                className = "banner",
                children = [
                    html.Div(
                        id = "title",
                        className = "banner-title",
                        children = [
                                    html.Img(className = "banner-logo", src=app.get_asset_url("logo.png")),
                                    html.H3('NatWest Risk Analytics Platform')
                        ]
                    ),
                    
                    html.Div(
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



###### Development of respective tabs ########################
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
                                            start_date = get_last_3months()
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
                            
                            html.Div([
                                    
                                    html.Div(
                                        className = "row chart-top-bar",
                                        children = [
                                            html.Div(
                                                className="inline-block chart-title",
                                                children = "PnL Performance",
                                            )
                                    ]),
                                    
                                    dcc.Graph(id = 'tab1_pnl_performance')
                            ],
                            style = {'padding': 10, 'margin': 'auto','width': '80%'}),
                        ],
                        style = {'margin-left': 30, 'margin-right': 30, 'margin-top': 20, 'margin-bottom': 30})    
                ])

def init_tab_2():
    return dcc.Tab(label='Add Transaction', className = 'custom-tab', selected_className="custom-tab--selected", children = [ 
           html.Div([     
                #html.H3('Add Transaction'),
                html.Div([
                    html.Div([
                        html.Div(
                                dcc.Input(id = 'user', className = "text_input", type = 'text', placeholder = 'User*'),
                                style = {'margin-right': 60}),
                        html.Div(
                                dcc.Input(id = 'portfolio', className = "text_input", type = 'text', placeholder = 'Portfolio*'),
                                style = {'margin-right': 60}),
                        html.Div(
                                dcc.DatePickerSingle(
                                    id = 'timestamp',
                                    max_date_allowed = dt.now().date(),
                                    placeholder = 'Date*'),
                                style = {'width': 200, 'margin-right': 60}),
                        html.Div(
                                dcc.Input(id = 'type', type = 'text', className = "text_input", placeholder = 'Type of Trade'),
                                style = {'margin-right': 60}),        
                        
                    ], 
                    style = {'margin-top': 10, 'margin-bottom': 30,
                             'display': 'flex', 'justify-content': 'flex-start'}),
                                
                    html.Div([
                        html.Div(
                                dcc.Dropdown(id='product',
                                             options=[{'label': curr, 'value': curr}for curr in currency_list],
                                             placeholder = 'Product*'),
                                style = {'width': 200, 'margin-right': 60}),
                        html.Div(
                                dcc.Dropdown(id='direction',
                                             options=[{'label': 'Long', 'value': 'Long'},
                                                      {'label': 'Short', 'value': 'Short'}],
                                             placeholder = 'Direction*'),
                                style = {'width': 200, 'margin-right': 60}),
                        html.Div(
                                dcc.Input(id = 'price', type = 'number',  className = "text_input", placeholder = 'Price*'),
                                style = {'margin-right': 60}),
                        html.Div(
                                dcc.Input(id = 'size', type = 'number',  className = "text_input", placeholder = 'Size/Notional*'),
                                style = {'margin-right': 60}),
                    ], 
                    style = {'margin-top': 10, 'margin-bottom': 30,
                             'display': 'flex', 'justify-content': 'flex-start'}),
                                
                    html.Div([    
                        html.Div(
                                dcc.Input(id = 'tenor', type = 'text',  className = "text_input", placeholder = 'Tenor'),
                                style = {'margin-right': 60}),
                        html.Div(
                                dcc.Input(id = 'risk', type = 'number',  className = "text_input", placeholder = 'Amount to Risk'),
                                style = {'margin-right': 60}),
                        html.Div(
                                dcc.Input(id = 'timeframe', type = 'text',  className = "text_input", placeholder = 'Timeframe'),
                                style = {'margin-right': 60})
                    ], 
                    style = {'margin-top': 10, 'margin-bottom': 30,
                             'display': 'flex', 'justify-content': 'flex-start'}),
                        
                    html.Div([
                    dcc.Input(id = 'strategy', type = 'text',  placeholder = 'Strategy Type', style = {'width': 800, 'height': 100})
                    ], style = {'margin-top': 10, 'margin-bottom': 30,
                             'display': 'flex', 'justify-content': 'flex-start'}),
                                
                ], style = {'margin': 'auto', 'width': '85%'}),
                    
                            
                html.Div([
                    dcc.ConfirmDialogProvider(
                        children = html.Button(
                            'Add',
                        ),
                        id = 'add',
                        message = 'Are you sure to continue?'),
                                
#                    dcc.ConfirmDialogProvider(
#                        children = html.Button(
#                            'Reset',
#                        ),
#                        id = 'reset',
#                        message = 'Are you sure to clear all inputs?'),
                ],style = {'padding': 10, 'display': 'flex', 'flex-direction': 'row-reverse','width': '90%',}),
                                
                html.Div(
                    dcc.ConfirmDialog(id = 'confirm', message = 'Please fill in all * fields!')
                ),
                
                html.Div(id = 'tab2_table',
                         children = tab2_build_table(trade_table, user_list[0]), 
                         style = {'height': 400,'margin': 'auto', 'width': '90%', 'margin-top': 15})  
            ], style = {'margin-left': 30, 'margin-right': 30, 'margin-top': 20, 'margin-bottom': 30 })
        ])

def init_tab_3():
    selector_date = html.Div([
        html.Div([
            html.H6('Select Date:')], 
            style = {'margin-left': 10, 'margin-right': 30}),
        dcc.DatePickerRange(
            id = 'tab3_date_range',
            display_format='Y-M-D',
            end_date = dt.now().date(),
            start_date = get_last_3months()
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
    
#    selector_section = html.Div([
#        selector_date, selector_portfolio], 
#        className = "four columns")
    
    
#    pnl_header = html.Div(
#        className = "row chart-top-bar",
#        children = [
#            html.Div(
#                className="inline-block chart-title",
#                children = "PnL Performance")])
                
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
                                start_date = get_last_3months()
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
                                            

# Dashboard layout
app.layout = html.Div(
    children = [
        build_banner(),
        
        dcc.Tabs(id = "tabs", 
                 className = 'custom-tabs', 
                 children = [
                     init_tab_1(),
                     init_tab_2(),
                     init_tab_3(),
                     init_tab_4()
        ]),
        
        dcc.Store(id='trade_table_store'),
        dcc.Interval(
            id='interval-component',
            interval=20*1000, # every 20 seconds
            n_intervals=5
        ),
        
        dcc.Store(id='bloomberg_store'),
        dcc.Interval(
            id='interval-bloomberg',
            interval=20*1000, # every 20 seconds
            n_intervals=5
        )
    ]
)


### read file by interval
@app.callback(Output('trade_table_store', 'data'),
              [Input('interval-component', 'n_intervals')])
def update_data_source(n): 
    trade_table, portfolio_list, user_list = load_data()
    return trade_table.to_dict('records')

### read file by interval
@app.callback(Output('bloomberg_store', 'data'),
              [Input('interval-bloomberg', 'n_intervals')])
def update_bloomberg(n): 
    df = read_bloomberg('Bloomberg Data.xlsx')
    return df.to_dict('records')

### date picker range
#@app.callback([Output('tab1_date_range','start_date'),
#               Output('tab3_date_range', 'start_date'),
#               Output('tab4_date_range', 'start_date')],
#              [Input('user_login', 'value'),
#               Input('trade_table_store', 'data')])
#def update_datepicker(user, data_dict): 
#    trade_table = pd.DataFrame.from_dict(data_dict)
#    trade_user = trade_table[trade_table['User'] == user]
#    start_user = min(trade_user['Timestamp'])
#    start_all = min(trade_user['Timestamp'])
#    return start_user, start_user, start_all 

## tab 1 display pnl charts, portfolios and total pnl
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

# update table user options
@app.callback(
   [Output('user_login', 'options'),
    Output('user_login', 'value')],
   [Input('trade_table_store', 'data')],
   [State('user_login', 'value')])
def update_userlist(data_dict, login):
    trade_table = pd.DataFrame.from_dict(data_dict)
    user_list = sorted(trade_table.User.unique())
    user_list.sort()
    if login == None:
        login = user_list[0]
    options = [{'label': user, 'value': user}for user in user_list]
    return options, login


@app.callback(
    Output('tab2_trade_table', 'data'),
    [Input('trade_table_store', 'data'),
     Input('user_login', 'value'),
     Input('tab2_trade_table','sort_by')])
def update_table(data_dict, user, sort_by):
    trade_table = pd.DataFrame.from_dict(data_dict)
    trade_user = trade_table[trade_table.User == user]
    user_list = sorted(trade_table.User.unique())
    
    if len(sort_by):
        trade_df = trade_user.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[col['direction'] == 'asc' for col in sort_by],
            inplace=False)
    else: 
        trade_df = trade_user
    return trade_df.to_dict('records')


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
#    user_list = sorted(trade_table.User.unique())
#    trade_user = trade_table[trade_table.User == login]
#    
#    if len(sort_by):
#        trade_df = trade_user.sort_values(
#            [col['column_id'] for col in sort_by],
#             ascending=[ col['direction'] == 'asc' for col in sort_by ],
#             inplace=False )
#    else: trade_df = trade_user
        
    if submit_n_clicks:
        inputs = [portfolio, product, direction, price, size, timestamp, user]
        for input in inputs:
            if input == None: 
                return True
            
        index = len(trade_table)
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
        trade_table[trade_table.User == user].to_csv(join(csv_path, user + '.csv'), index = False)
#        if (user not in user_list):
#            user_list.append(user)
#            user_list.sort()
#            options = [{'label': u, 'value': u}for u in user_list]
        return False
    return False



###tab3 portfolio dropdown by user
@app.callback(Output('tab3 portfolio', 'options'),
              [Input('user_login', 'value'),
               Input('trade_table_store', 'data')])
def update_portfolio(user, data_dict):
    data_df = pd.DataFrame.from_dict(data_dict)
    data = data_df[data_df.User==user]
    pfl_list = sorted(data.Portfolio.unique())
    return [{'label': 'Portfolio '+i, 'value': i} for i in pfl_list]

###tab3 table
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

###tab3 update graph
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



# tab 4 graphs
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


    if view == 'Individuals':
        fig = tab4_build_idv_graph(start, end,trade_table_store)
        return fig, total_pnl, number_of_portfolios, last_week_trades, sortino_ratio, sharpe_ratio, hit_ratio
    else:
        fig = tab4_build_agg_graph(start, end, trade_table_store)
        return fig, total_pnl, number_of_portfolios, last_week_trades, sortino_ratio, sharpe_ratio, hit_ratio


if __name__ == '__main__':
    app.debug = True
    app.run_server()
