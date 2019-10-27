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

app = dash.Dash(__name__)
csv_path = 'user_csv'

###### DATA INTAKE ########################
# Initialise trade table
def read_data(user):
    file_names = [f for f in listdir(csv_path) if isfile(join(csv_path, f)) and f[-4:]=='.csv']
    
    trade_table = pd.DataFrame(columns = ['Portfolio','Type of Trade','Direction','Product', 
                                      'Price', 'Size/Notional', 'Tenor', 'Amount to Risk',
                                      'Timeframe', 'Strategy Type','Timestamp','User'])
    
    if user=='all':
        for trader in file_names:
            cur=pd.read_csv(join(csv_path, trader)).dropna()
            trade_table = trade_table.append(cur,sort=False,ignore_index=True)
    elif user+'.csv' in file_names:
        trade_table = pd.read_csv(join(csv_path, user+'.csv')).dropna()
    
    trade_table['Timestamp'] = pd.to_datetime(trade_table.Timestamp).apply(lambda x: x.date())
    
    return trade_table.dropna()

def load_data():
    trade_table = read_data('all')
    portfolio_list = sorted(trade_table.Portfolio.unique())
    user_list = sorted(trade_table.User.unique())
    return trade_table, portfolio_list, user_list

def save_file(full_trade_table, user):
    user_df = full_trade_table[full_trade_table.User==user]
    user_df.to_csv(join(csv_path, user+'.csv'), index = False)

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
                


### function for tab 3
## function for table
# input: df
# output: df
def tab3_get_data(trade_table, user, start, end):
    ### filter to get user data
    trade_table['Size/Notional'] = trade_table['Size/Notional'].astype('int')
    trade_table = trade_table[trade_table.User==user]
    
    ### 
    if start:
        trade_table = trade_table[trade_table.Timestamp>=start]
    if end:
        trade_table = trade_table[trade_table.Timestamp<=end]
    
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
    data_df = tab3_get_data(trade_table, user, None, None)
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
                                                 options = ([{'label': user, 'value': user}for user in user_list]),
                                                 value = user_list[0])
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
                           html.Div([html.H6('Select Date:')], style = {'margin-left': 10, 'margin-right': 30}),
                           dcc.DatePickerRange(
                                id = 'tab1_date_range',
                                display_format='Y-M-D',
                                end_date = dt.now().date(),
                                start_date = min(trade_table['Timestamp'])
                           )],
                           className = 'row',
                           style = {'display': 'flex', 'flex-direction': 'row', 'align-items': 'center', "margin-top": 30}
                       ),
                    
                    # summary of total portfolios and PnL 
                       html.Div([
                            
                            html.Div([
                                html.Div(
                                        [html.H6(id = "tab1_total_pnl"), html.P('Total PnL')],
                                        className = "mini_container",
                                        style = {'margin-right':10})],
                                        className = 'six columns'),
                                
                            html.Div([
                                html.Div(
                                        [html.H6(id = "tab1_total_portfolio"), html.P('Total Portfolios')],
                                        className = "mini_container")],
                                        className = 'six columns'),
                        ],
                        className = 'twelve columns',
                        style = {"margin-top": 30}
                      ),
  
                ], 
                className="four columns", style = {'margin-left': 30, 'margin-top': 10, 'margin-bottom': 30}),
                
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
                className = 'eight columns',
                style = {'padding': 10, 'width': 800}),
            ],
            className = 'twelve columns',
            style = {'margin-left': 30, 'margin-right': 30, 'margin-top': 20, 'margin-bottom': 30})    
        ])

def init_tab_2():
    return dcc.Tab(label='Add Transaction', className = 'custom-tab', selected_className="custom-tab--selected", children = [ 
           html.Div([     
                #html.H3('Add Transaction'),
                html.Div([
                    html.Div([
                        html.Div(
                                dcc.Input(id = 'user', className = "text_input", type = 'text', placeholder = 'User'),
                                className = "three columns"),
                        html.Div(
                                dcc.Input(id = 'portfolio', className = "text_input", type = 'text', placeholder = 'Portfolio'),
                                className = "three columns"),
                        html.Div(
                                dcc.DatePickerSingle(
                                    id = 'timestamp',
                                    placeholder = 'Date'),
                                className = "three columns", style = {'width': 270}),
                        html.Div(
                                dcc.Input(id = 'type', type = 'text', className = "text_input", placeholder = 'Type of Trade'),
                                className = "three columns"),        
                        
                    ], className = "twelve columns", style = {'padding': 10}),
                                
                    html.Div([
                        html.Div(
                                dcc.Input(id = 'product', type = 'text', className = "text_input", placeholder = 'Product'),
                                className = "three columns"),
                        html.Div(
                                dcc.Dropdown(id='direction',
                                             options=[{'label': 'Long', 'value': 'Long'},
                                                      {'label': 'Short', 'value': 'Short'}],
                                             placeholder = 'Direction'),
                                className = "three columns", style = {'width': 200, 'margin-right': 65}),
                        html.Div(
                                dcc.Input(id = 'price', type = 'number',  className = "text_input", placeholder = 'Price'),
                                className = "three columns", style = {'margin-right': 5}),
                        html.Div(
                                dcc.Input(id = 'size', type = 'number',  className = "text_input", placeholder = 'Size/Notional'),
                                className = "three columns"),
                    ], className = "twelve columns", style = {'padding': 10}),
                                
                    html.Div([    
                        html.Div(
                                dcc.Input(id = 'tenor', type = 'text',  className = "text_input", placeholder = 'Tenor'),
                                className = "three columns"),
                        html.Div(
                                dcc.Input(id = 'risk', type = 'number',  className = "text_input", placeholder = 'Amount to Risk'),
                                className = "three columns"),
                        html.Div(
                                dcc.Input(id = 'timeframe', type = 'text',  className = "text_input", placeholder = 'Timeframe'),
                                className = "three columns")
                    ], className = "twelve columns", style = {'padding': 10}),
                        
                    html.Div([
                    dcc.Input(id = 'strategy', type = 'text',  placeholder = 'Strategy Type', style = {'width': 800, 'height': 100})
                    ], className = "twelve columns", style = {'padding': 10}),
                                
                ], style = {'margin-left': 120}),
                    
                            
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
                ],style = {'padding': 10,'margin-right': 200, 'display': 'flex', 'flex-direction': 'row-reverse'}),
                                
                html.Div(
                    dcc.ConfirmDialog(id = 'confirm', message = 'There are blank fields!')
                ),
                
                html.Div(id = 'tab2_table',
                         children = tab2_build_table(trade_table, user_list[0]), 
                         style = {'height': 400,'margin-left': 50, 'width': 1200, 'margin-top': 15})  
            ], style = {'margin-left': 30, 'margin-top': 20, 'margin-bottom': 30})
        ])

def init_tab_3():
    selector_date = html.Div([
        html.Div([
            html.H6('Select Date:')], 
            style = {'margin-left': 10, 'margin-right': 20}),
        dcc.DatePickerRange(
            id = 'tab3_date_range',
            display_format='Y-M-D',
            end_date = dt.now().date(),
            start_date = min(trade_table['Timestamp'])
        )],
        className = 'row',
        style = {'display': 'flex', 'flex-direction': 'row', 'align-items': 'center', "margin-top": 30}
    )
    
    selector_portfolio = html.Div([
        html.H6('Select Portfolio'),
        dcc.Dropdown(id = 'tab3 portfolio')],
        style = {'padding':8})
    
    ratio_container = html.Div(
        id="info-container",
        children = tab3_build_ratio(ratio_list),
        className="four columns",
        style = {'padding': 10})
    
    selector_section = html.Div([
        selector_date, selector_portfolio], 
        className = "four columns")
    
    
    pnl_header = html.Div(
        className = "row chart-top-bar",
        children = [
            html.Div(
                className="inline-block chart-title",
                children = "PnL Performance")])
    
    pnl_graph = dcc.Graph(
        id='tab3 daily pnl', 
        figure = go.Figure(
            layout = go.Layout({"paper_bgcolor": "rgba(0,0,0,0)",
                                "plot_bgcolor": "rgba(0,0,0,0)",
                                "font": {"color": "lightgrey"},
                                "margin": {'t': 30}}))) 
    
    pnl_section = html.Div([
        pnl_header,pnl_graph], 
        className = "eight columns",
        style = {'padding': 10, 'width': 800})
    
    table = html.Div(
        id='tab3_table',
        children = tab3_build_table(trade_table,user_list[0]),
        className = 'eight columns',
        style = {'height': 400, 'padding': 10, 'width': 800})
    
    return dcc.Tab(label='Individual Analysis', className = 'custom-tab', selected_className="custom-tab--selected", 
                   children = [
                       html.Div([  
                           html.Div([selector_section, pnl_section], 
                                    className = "twelve columns",
                                    style = {'margin-left': 30, 'margin-top': 10, 'margin-bottom': 30}),  
                           
                           html.Div([ratio_container, table],
                                    className = "twelve columns",
                                    style = {'margin-left': 30, 'margin-top': 10, 'margin-bottom': 30})
                       ],
                           style = {'margin-left': 30, 'margin-right': 30, 'margin-top': 20, 'margin-bottom': 30}
                       )
                   ]
                  )

def init_tab_4():
    return dcc.Tab(label='Team Summary', className = 'custom-tab', selected_className="custom-tab--selected", children = [
           html.Div([ 
                #html.H3('Team Summary'),
                
                ### select date range
                html.Div([
                           html.Div([html.H6('Select Date:')], style = {'margin-left': 10, 'margin-right': 30}),
                           dcc.DatePickerRange(
                                id = 'tab4_date_range',
                                display_format='Y-M-D',
                                end_date = dt.now().date(),
                                start_date = min(trade_table['Timestamp'])
                           )],
                           className = 'row',
                           style = {'margin-left': 30, 'margin-top': 10, 'margin-bottom': 30,
                                   'display': 'flex', 'flex-direction': 'row', 'align-items': 'center', "margin-top": 30}
                ),
                
                ###text boxes to display ratio for selected porfolio
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(id="total_pnl_text_tab4"), html.P("Total PnL")],
                            id="total_pnl_tab4",
                            className = "mini_container"),
                        ], className = "three columns"),
                    
                    html.Div([
                        html.Div([
                            html.H6(id="no_of_porfolios_text_tab4"), html.P("Number of Portfolios")],
                            id="no_of_porfolios_tab4",
                            className = "mini_container"),
                    ], className = "three columns"),
                                
                    html.Div([            
                        html.Div(
                            [html.H6(id="last_week_trades_text_tab4"), html.P("Last Week Trades")],
                            id="last_week_trades_tab4",
                            className = "mini_container"),
                    ], className = "three columns"),            

                    html.Div([
                        html.Div(
                            [html.H6(id="sharpe_ratio_text_tab4"), html.P("Sharpe Ratio")],
                            id="sharpe_ratio_tab4",
                            className = "mini_container"),
                    ], className = "three columns")], 
                    id="info-container_1_tab4",
                    className="twelve columns",
                    style = {'margin-left': 30, 'margin-top': 10, 'margin-bottom': 30, 
                             'display': 'flex', 'justify-content': 'center'}),

                html.Div([
                    html.Div([
                        html.Div(
                            [html.H6(id="sorting_ratio_text_tab4"), html.P("Sorting Ratio")],
                            id="sorting_ratio_tab4",
                            className = "mini_container"),
                    ], className = "three columns"),
    
                    html.Div([
                        html.Div(
                            [html.H6(id="information_ratio_text_tab4"), html.P("Information Ratio")],
                            id="information_ratio_tab4",
                            className = "mini_container"),
                    ], className = "three columns"),
                    
                    html.Div([   
                        html.Div(
                            [html.H6(id="jensen_measure_text_tab4"), html.P("Jensen Measure")],
                            id="jensen_measure_tab4",
                            className = "mini_container"),
                    ], className = "three columns"),
    
                    html.Div([
                        html.Div(
                            [html.H6(id="hit_ratio_text_tab4"), html.P("Hit Ratio")],
                            id="hit_ratio_tab4",
                            className = "mini_container"),
                    ], className = "three columns"),],
                    id="info-container_tab4",
                    className="twelve columns",
                    style = {'margin-left': 30, 'margin-top': 10, 'margin-bottom': 30, 
                             'display': 'flex', 'justify-content': 'center'}),
    
                html.Div(className = "twelve columns", children = [
                    html.Div([
                        html.Div(
                            ###Drodown to select time unit
                            className = "row chart-top-bar",
                            children = [
                                html.Div(
                                    className="inline-block chart-title",
                                    children = "Team PnL View (Individuals)",
                                ),   
                            ], style = {'justify-content': 'center'}
                        ), 
    
                        dcc.Graph(id='tab4 team view'),
                    ], className = 'six columns'),    

                    html.Div([
                        html.Div(
                            ###Drodown to select time unit
                            className = "row chart-top-bar",
                            children = [
                                html.Div(
                                    className="inline-block chart-title",
                                    children = "Team PnL View (Aggregated)",
                                ),
                            ], style = {'justify-content': 'center'}
                        ), 
    
                        dcc.Graph(id='tab4 aggregated view')
                ], className = 'six columns')    
              ],
              style = {'margin-top': 10, 'margin-bottom': 30})

            ], style = {'margin-left': 30, 'margin-right': 30, 'margin-top': 20, 'margin-bottom': 30}),        
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
        
        dcc.Store(id='trade_table_store', data = trade_table.to_dict('records')),
        dcc.Interval(
            id='interval-component',
            interval=5*1000, # every 5 seconds
            n_intervals=50
        )
    ]
)


### read file by interval
@app.callback(Output('trade_table_store', 'data'),
              [Input('interval-component', 'n_intervals')])
def update_data_source(n): 
    trade_table, portfolio_list, user_list = load_data()
    return trade_table.to_dict('records')


## tab 1 display pnl charts, portfolios and total pnl
@app.callback([Output('tab1_pnl_performance', 'figure'),
               Output('tab1_total_pnl', 'children'),
               Output('tab1_total_portfolio', 'children')],
              [Input('user_login', 'value'),
               Input('tab1_date_range', 'start_date'),
               Input('tab1_date_range', 'end_date')])
def update_tab1_pnl(user, start_date, end_date):
    start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime('%d/%m/%Y')
    end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime('%d/%m/%Y')
    
    transaction = trade_table[trade_table['User'] == user]
    portfolios = list(transaction['Portfolio'])
    portfolios = np.unique(portfolios)
    trans_preprocessing(transaction)

    pnl = pnl_trader(start_date, end_date, transaction_A, df)
    #pnl = pnl_trader('20/08/2019','15/09/2019',transaction,df) #TODO: 把Currenry整同步了
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
                        mode = 'lines+markers')                    
                    ]}
    return figure, round(pnl['PnL'].sum(),2), portfolios.size

# tab 2 update table
@app.callback(
    [Output('confirm', 'displayed'),
     Output('tab2_trade_table', 'data'),
     Output('user_login', 'options'),
     Output('user_login', 'value')],
    [Input('add', 'submit_n_clicks'),
     Input('tab2_trade_table', "sort_by")],
    [State('user_login', 'value'),
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
def update_table(submit_n_clicks, sort_by, 
                 login, portfolio, type, product, direction, price, size, tenor, risk, timeframe, strategy, timestamp, user):
    
    trade_user = trade_table[trade_table.User == login]
    options = [{'label': user, 'value': user}for user in user_list]
    
    if len(sort_by):
        trade_df = trade_user.sort_values(
            [col['column_id'] for col in sort_by],
             ascending=[ col['direction'] == 'asc' for col in sort_by ],
             inplace=False )
    else: trade_df = trade_user
        
    if submit_n_clicks:
        inputs = [portfolio, type, product, direction, price, size, tenor, risk, timeframe, strategy, timestamp, user]
        for input in inputs:
            if input == None: 
                return True, trade_table.to_dict('records'), options, login
            
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
        trade_user = trade_table[trade_table.User == user]
        if (user not in user_list):
            user_list.append(user)
            user_list.sort()
            options = [{'label': user, 'value': user}for user in user_list]
        save_file(trade_table, user)
        return False, trade_table.to_dict('records'), options, user 
    return False, trade_user.to_dict('records'), options, login


### tab 2 clear input
#@app.callback(
#    [Output('portfolio', 'value'),
#     Output('product', 'value'),
#     Output('type', 'value'),
#     Output('direction', 'value'),
#     Output('price', 'value'),
#     Output('size', 'value'),
#     Output('tenor', 'value'),
#     Output('risk', 'value'),
#     Output('timeframe', 'value'),
#     Output('strategy', 'value'),
#     Output('timestamp', 'date'),
#     Output('user', 'value')],
#    [Input('reset','submit_n_clicks')],
#    [State('portfolio', 'value'),
#     State('product', 'value'),
#     State('type', 'value'),
#     State('direction', 'value'),
#     State('price', 'value'),
#     State('size', 'value'),
#     State('tenor', 'value'),
#     State('risk', 'value'),
#     State('timeframe', 'value'),
#     State('strategy', 'value'),
#     State('timestamp', 'date'),
#     State('user', 'value')])
#def update(clicks):
#    if clicks:
#        return None, None, None, None, None, None, None, None, None, None, None, None


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
    [Input('tab3_date_range', 'start_date'),
     Input('tab3_date_range', 'end_date'),
     Input('trade_table_store', 'data'),
     Input('user_login', 'value'),
     Input('tab3 product table','sort_by')
    ])
def update_table(start_date, end_date, data_dict, user, sort_by):
    data = pd.DataFrame.from_dict(data_dict)
    df = tab3_get_data(data, user, start_date, end_date)
    
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
    trade_table = pd.DataFrame.from_dict(data_dict)
    temp_df = trade_table.loc[(trade_table['Portfolio']==portfolio) 
                              & (trade_table['User'] == user)]
    trans_preprocessing(temp_df)
    
    if start: temp_df = temp_df[temp_df.Timestamp>=start]
    if end: temp_df = temp_df[temp_df.Timestamp<=end]
    
    temp_df = temp_df[['Timestamp', 'Price']].groupby('Timestamp').sum()
    temp_df = temp_df.reset_index(level=['Timestamp'])
    temp_df = temp_df.sort_values('Timestamp')

    X = temp_df['Timestamp']
    Y = temp_df['Price']
    
    return {'layout': {"paper_bgcolor": "rgba(0,0,0,0)",
                       "plot_bgcolor": "rgba(0,0,0,0)",
                       "font": {"color": "lightgrey"},
                       "margin": {'t': 30},
                       "xaxis": dict(title= 'time',range=[min(X),max(X)]),
                       "yaxis": dict(title= 'price', range=[min(Y),max(Y)])
                      },
            'data': [go.Scatter(x = X, y = Y, mode = 'lines+markers')]
           }  

# tab 4 graph
@app.callback(Output('tab4 team view', 'figure'),
              [Input('tab4_date_range', 'start_date'),
               Input('tab4_date_range', 'end_date'),
              Input('trade_table_store', 'data')])
def update_tab4_team_view(start, end,trade_table_store):
    trade_table = pd.DataFrame.from_dict(trade_table_store)
    temp_df = trade_table
    trans_preprocessing(temp_df)

    users = list(temp_df['User'])
    users = np.unique(users)

    
    if start: temp_df = temp_df[temp_df.Timestamp>=start]
    if end: temp_df = temp_df[temp_df.Timestamp<=end]

    # temp_df = temp_df.reset_index(level=['Timestamp'])
    temp_df = temp_df.sort_values('Timestamp')

    fig = {'data': [go.Scatter(x=temp_df[temp_df['User'] == user]["Timestamp"], 
                               y=temp_df[temp_df['User'] == user]["Size/Notional"],
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

# tab 4 graph 2
@app.callback(Output('tab4 aggregated view', 'figure'),
              [Input('tab4_date_range', 'start_date'),
               Input('tab4_date_range', 'end_date')],
              [State('trade_table_store', 'data')])

def update_tab4_aggregated_view(start, end, trade_table_store):
    trade_table = pd.DataFrame.from_dict(trade_table_store)
    temp_df = trade_table
    trans_preprocessing(temp_df)

    users = list(temp_df['User'])
    users = np.unique(users)

    
    if start: temp_df = temp_df[temp_df.Timestamp>=start]
    if end: temp_df = temp_df[temp_df.Timestamp<=end]


    temp_df = temp_df.groupby('Timestamp')['Size/Notional'].sum().to_frame().reset_index()

    fig = {'data': [go.Scatter(x=temp_df["Timestamp"], 
                               y=temp_df["Size/Notional"],
                               # mode = 'lines+markers',
                               fill = 'tozeroy',
                               )],

           'layout':{"paper_bgcolor": "rgba(0,0,0,0)",
                       "plot_bgcolor": "rgba(0,0,0,0)",
                       "font": {"color": "lightgrey"},
                       "margin": {'t': 30},
                       "xaxis": dict(title= 'Time'),
                       "yaxis": dict(title= 'PnL')}
          }
    
    return fig

if __name__ == '__main__':
    app.debug = True
    hello_world()
    app.run_server()
