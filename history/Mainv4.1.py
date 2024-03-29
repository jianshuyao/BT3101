import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime as dt
import dash_table
from textwrap import dedent as d
import plotly.express as px


#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

#app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app = dash.Dash(__name__)

# Initialise trade table
data = [('A1', 'type','dir','SGD', 1, 10,'tenor', 0.8,'week','strategy','1','A01'),
        ('A1', 'type','dir','CNY', 1.5, 20,'tenor', 1.3,'week','strategy','2','A01'),
        ('A1', 'type','dir','GBP', 0.5, 30,'tenor',0.3,'week','strategy','3','A01'),
        ('B1', 'type','dir','JPY', 3, 20,'tenor', 2.7,'week','strategy','1','B01'),
        ('B1', 'type','dir','CHF', 2, 10,'tenor', 1.7,'week','strategy','2','B01'),
        ('B1', 'type','dir','USD', 2.5, 30,'tenor', 2.2,'week','strategy','3','B01'),
        ('C1', 'type','dir','EUR', 3.5, 10,'tenor', 3.4,'week','strategy','1','C01'),
        ('C1', 'type','dir','SGD', 2, 10,'tenor', 1.7,'week','strategy','2','C01'),
        ('C1', 'type','dir','CNY', 1.5, 40,'tenor', 1.3,'week','strategy','3','C01'),
        ('A2', 'type','dir','SGD', 1, 10,'tenor',0.8,'day','strategy','3','A01'),
        ('A1', 'type','dir','CNY', 1.5, 20,'tenor', 1.3, 'day','strategy','2','A01'),
        ('A2', 'type','dir','GBP', 0.5, 30,'tenor',0.3,'day','strategy','1','A01'),
        ('B2', 'type','dir','JPY', 3, 20,'tenor', 2.7,'day','strategy','3','B01'),
        ('B2', 'type','dir','CHF', 2, 10,'tenor', 1.7,'day','strategy','2','B01'),
        ('B2', 'type','dir','USD', 2.5, 30,'tenor', 2.2,'day','strategy','1','B01'),
        ('C1', 'type','dir','EUR', 3.5, 10,'tenor', 3.4,'day','strategy','3','C01'),
        ('C2', 'type','dir','SGD', 2, 10,'tenor', 1.7,'day','strategy','2','C01'),
        ('C3', 'type','dir','CNY', 1.5, 40,'tenor', 1.3,'day','strategy','1','C01'),
        ('A1', 'type','dir','SGD', 1, 10,'tenor',0.8,'month','strategy','2','A01'),
        ('A1', 'type','dir','CNY', 1.5, 20,'tenor', 1.3,'month','strategy','3','A01'),
        ('A1', 'type','dir','GBP', 0.5, 30,'tenor', 0.3,'month','strategy','1','A01'),
        ('B2', 'type','dir','JPY', 3, 20,'tenor', 2.7,'month','strategy','2','B01'),
        ('B3', 'type','dir','CHF', 2, 10,'tenor', 1.7,'month','strategy','3','B01'),
        ('B3', 'type','dir','USD', 2.5, 30,'tenor', 2.2,'month','strategy','1','B01'),
        ('C3', 'type','dir','EUR', 3.5, 10,'tenor', 3.4,'month','strategy','2','C01'),
        ('C3', 'type','dir','SGD', 2, 10,'tenor', 1.7,'month','strategy','3','C01'),
        ('C3', 'type','dir','CNY', 1.5, 40,'tenor', 1.3,'month','strategy','1','C01')]

columns = ['Portfolio','Type of Trade','Direction','Product', 
           'Price', 'Size/Notional', 'Tenor', 'Amount to Risk',
           'Time Frame', 'Strategy Type','Timestamp','User']

trade_table = pd.DataFrame(data, columns = columns)
portfolio_list = sorted(trade_table.Portfolio.unique())
user_list = sorted(trade_table.User.unique())

# data processing
# function for tab 1
def get_user():
    user = list(trade_table['User'])
    user = np.unique(user)
    return user

# table for tab 3
trade_table['Size/Notional'] = trade_table['Size/Notional'].astype('int')
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


# Dashboard layout
app.layout = html.Div([
    
    html.Div([
        html.Div(html.Img(className="logo", src=app.get_asset_url("logo.png")), 
                 className = "one column"),
        html.Div(
                 html.H3('NatWest Risk Analytics Platform'),
                 className = "six columns", style = {'color': 'white', 'font-size': 20, 'margin-top': 20})
        ], className = "row", style = {'margin-left': 50, 'margin-right': 50}
    ),
    
    dcc.Tabs(id="tabs", className='custom-tabs', children=[
        dcc.Tab(label = 'Individual Summary', className = 'custom-tab', selected_className="custom-tab--selected", children = [
            html.Div([
                #html.H3('Individual Summary'),
                    
                html.Div([
                        # user selection
                        html.Div([
                            html.H6('Select User'),
                            dcc.Dropdown(
                                        id = 'tab1_user_selection',
                                        options = ([
                                                    {'label': user, 'value': user}
                                                    for user in get_user()]
                                        ),
                                        value = get_user()[0]),                                    
                                         
                        ], style = {'margin':10}),
                            
                       # summary of total portfolios and PnL 
                       html.Div([
                            
                            html.Div([
                                html.Div(
                                        [html.H6(id = "tab1_total_pnl"), html.P('Total PnL')],
                                        className = "mini_container",
                                        style = {'margin':10})],
                                        className = 'six columns'),
                                
                            html.Div([
                                html.Div(
                                        [html.H6(id = "tab1_total_portfolio"), html.P('Total PnL')],
                                        className = "mini_container",
                                        style = {'margin':10})],
                                        className = 'six columns'),
                        ],
                        className = 'twelve columns'),
                        
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
                style = {'padding': 10, 'margin-top': 10, 'width': 800}),
            ],
            className = 'twelve columns',
            style = {'margin-left': 30, 'margin-right': 30, 'margin-top': 10, 'margin-bottom': 30})    
        ]),
        
        dcc.Tab(label='Add Transaction', className = 'custom-tab', selected_className="custom-tab--selected", children = [ 
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
                                #dcc.Input(id = 'timestamp', type = 'text', placeholder = 'Timestamp'),
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
                                             value='Long'),
                                className = "three columns", style = {'width': 200, 'margin-right': 70}),
                        html.Div(
                                dcc.Input(id = 'price', type = 'number',  className = "text_input", placeholder = 'Price'),
                                className = "three columns"),
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
                    html.Button('Add', id = 'button')
                ], style = {'padding': 10,'margin-right': 200, 'display': 'flex', 'flex-direction': 'row-reverse'}),
                            
                html.Div(className = 'table-trades', children = [
                    dash_table.DataTable(id = 'trade-table',
                                         columns = [{"name": i, "id": i} for i in trade_table.columns],
                                         style_cell={
                                            'backgroundColor': '#22252b',
                                            'textAlign': 'center',
                                            'color': 'white'
                                         }),
                ], style = {'height': 400,'margin-left': 50, 'width': 1200, 'margin-top': 15})  
            ], style = {'margin-left': 30, 'margin-top': 10, 'margin-bottom': 30})
        ]),
        
        
        dcc.Tab(label='Individual Analysis', className = 'custom-tab', selected_className="custom-tab--selected", children = [
            html.Div([    
                    #html.H3('Individual Analysis'),  
                html.Div([    
                    html.Div([
                         ###Dropdown to select user
                        html.Div([
                            html.H6('Select User'),
                            dcc.Dropdown(id = 'tab3 user',
                                         options = [{'label': 'Trader '+i, 'value': i} for i in user_list],
                                         value=user_list[0])],
                            style = {'padding':8},
                        ),
                        
                        ###Drodown to select time unit
#                        html.Div([
#                            html.H6('Select Timeframe'),
#                            dcc.Dropdown(id = 'tab3 time unit',
#                                         options=[{'label': 'Daily', 'value': 'day'},
#                                                  {'label': 'Weekly', 'value': 'week'},
#                                                  {'label': 'Monthly', 'value': 'month'}],
#                                         value='day')],
#                            style = {'padding':8},
#                        ),
                    
                        ###Dropdown to select portfolio
                        html.Div([
                            html.H6('Select Portfolio'),
                            dcc.Dropdown(id = 'tab3 portfolio',
                                         options= [{'label': 'Portfolio '+i, 'value': i} for i in portfolio_list],
                                         value=portfolio_list[0])],
                            style = {'padding':8},
                        ),
                    ], 
                    className = "four columns"),                          
                                        
                    html.Div([
                        html.Div(
                            className = "row chart-top-bar",
                            children = [
                                html.Div(
                                    className="inline-block chart-title",
                                    children = "PnL Performance",
                                ),
                                        
                                html.Div(
                                    className = "graph-top-right inline-block",
                                    children = [
                                        html.Div([
                                            #html.H6('Select Timeframe'),
                                            dcc.Dropdown(id = 'tab3 time unit',
                                                         options=[{'label': 'Daily', 'value': 'day'},
                                                                  {'label': 'Weekly', 'value': 'week'},
                                                                  {'label': 'Monthly', 'value': 'month'}],
                                                         value='day')],
                                        style = {'width': 300}),
                                    ])
                        ]),
                            
                        dcc.Graph(id='tab3 daily pnl'),
                    ], 
                    className = "eight columns",
                    style = {'padding': 10, 'width': 800})
                    
                ], 
                className = "twelve columns",
                style = {'margin-left': 30, 'margin-top': 10, 'margin-bottom': 30}),  
                            
                    ###text boxes to display ratio for selected porfolio
                html.Div([   
                    html.Div([
                        html.Div([
                                html.H6(id="sharpe_ratio_text"), html.P("Sharpe Ratio")],
                                id="sharpe_ratio",
                                className="mini_container",
                                style = {'padding': 20, 'margin-bottom': 20}),
                            
                        html.Div([
                                html.H6(id="hit_ratio_text"), html.P("Hit Ratio")],
                                id="hit_ratio",
                                className="mini_container",
                                style = {'padding': 20, 'margin-bottom': 20}),
                            
                        html.Div(
                                [html.H6(id="sortino_ratio_text"), html.P("Sortino Ratio")],
                                id="sortino_ratio",
                                className="mini_container",
                                style = {'padding': 20, 'margin-bottom': 20})],
                            
                        id="info-container",
                        className="four columns",
                        style = {'padding': 10}),
                        
                        html.Div([
                            dash_table.DataTable(
                                id = 'groupby_product',
                                columns = [{"name": i, "id": i} for i in groupby_product.columns],
                                data = groupby_product.to_dict('records'),
                                style_cell={
                                            'backgroundColor': '#22252b',
                                            'textAlign': 'center',
                                            'color': 'white'
                                }
                            )], 
                            className = 'eight columns table-trades',
                            style = {'height': 400, 'padding': 10, 'width': 800})
                 ], 
                 className = "twelve columns",
                 style = {'margin-left': 30, 'margin-top': 10, 'margin-bottom': 30})
                        
             ], style = {'margin-left': 30, 'margin-right': 30, 'margin-top': 10, 'margin-bottom': 30})   
        ]),
        
        
        
        dcc.Tab(label='Team Summary', className = 'custom-tab', selected_className="custom-tab--selected", children = [
           html.Div([ 
                #html.H3('Team Summary'),

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
                    html.Div(
                        ###Drodown to select time unit
                        className = "row chart-top-bar",
                        children = [
                            html.Div(
                                className="inline-block chart-title",
                                children = "Team PnL View",
                            ),
                                    
                            html.Div(
                                #html.H6('Select Timeframe'),
                                className = "graph-top-right inline-block",
                                children = [
                                    html.Div([
                                        dcc.Dropdown(id='tab4 time unit',
                                                     options=[{'label': 'Daily', 'value': 'day'},
                                                              {'label': 'Weekly', 'value': 'week'},
                                                              {'label': 'Monthly', 'value': 'month'}],
                                                     value='day')],
                                        style = {'width': 300}
                                )],
                            )
                        ], style = {'justify-content': 'center'}
                    ), 

                    dcc.Graph(id='tab4 team view',
                              figure={'layout':{'title': 'Team View'}})
                ],
                style = {'margin-left': 160, 'margin-top': 10, 'margin-bottom': 30, 'width': 1000})

            ], style = {'margin-left': 30, 'margin-right': 30, 'margin-top': 10, 'margin-bottom': 30}),        
        ])
    ])     
])

## tab 1 display portfolios
@app.callback(Output('tab1_total_portfolio', 'children'),
              [Input('tab1_user_selection', 'value')])
def display_tab1_portfolio(user):
    portfolios = list(trade_table[trade_table['User'] == user]['Portfolio'])
    portfolios = np.unique(portfolios)
    
    return portfolios.size

## tab 1 display pnl
@app.callback(Output('tab1_total_pnl', 'children'),
              [Input('tab1_user_selection', 'value')])
def display_tab1_pnl(user):
    portfolios = trade_table[trade_table['User'] == user]
    pnl = list(portfolios['Price'])
    return np.mean(pnl)

## tab 1 display pnl charts
@app.callback(Output('tab1_pnl_performance', 'figure'),
              [Input('tab1_user_selection', 'value')])
def update_tab1_pnl(user):
    pnl = trade_table[trade_table['User'] == user]
    #pnl['Amount'] = pnl['Price'] * pnl['Size/Notional']
    portfolios = list(trade_table[trade_table['User'] == user]['Portfolio'])
    portfolios = np.unique(portfolios)
    return {'layout': {"paper_bgcolor": "rgba(0,0,0,0)",
                       "plot_bgcolor": "rgba(0,0,0,0)",
                       "font": {"color": "lightgrey"},
                       "margin": {'t': 30},
                       "xaxis": dict(title= 'Product'),
                       "yaxis": dict(title= 'Price')
                        },
            'data': [
                        go.Scatter(
                        x = pnl[pnl['Portfolio'] == portfolio]['Product'],
                        y = pnl[pnl['Portfolio'] == portfolio]['Price'],
                        mode = 'lines+markers',
                        name = portfolio) for portfolio in portfolios                    
                    ]}    


# tab 2 update table
@app.callback(
    Output('trade-table', 'data'),
    [Input('button', 'n_clicks')],
    [State('portfolio', 'value'),
     State('product', 'value'),
    State('type', 'value'),
    State('direction', 'value'),
    State('price', 'value'),
    State('size', 'value'),
    State('tenor', 'value'),
    State('risk', 'value'),
    State('timeframe', 'value'),
    State('strategy', 'value'),
    State('timeframe', 'value'),
    State('user', 'value')])
def update_table(n_clicks, portfolio, type, product, direction, price, size, tenor, risk, timeframe, strategy, timestamp, user):
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
    return trade_table.to_dict('records')


###tab3 daily pnl
@app.callback(Output('tab3 daily pnl', 'figure'),
              [Input('tab3 time unit', 'value'),
               Input('tab3 portfolio', 'value'),
               Input('tab3 user', 'value')])
def update_tab3_daily(time,portfolio,user):
    temp_df = trade_table[trade_table['Portfolio']==portfolio]
    temp_df = temp_df[trade_table['User']==user]
    temp_df = temp_df[temp_df['Time Frame']==time].sort_values('Timestamp')
#    temp = trade_table[trade_table['Time Frame']==time]
    
    return {'data': [go.Scatter(x=temp_df['Timestamp'], 
                                y=temp_df['Price'],
                                mode = 'lines+markers')],
            'layout': {"paper_bgcolor": "rgba(0,0,0,0)",
                       "plot_bgcolor": "rgba(0,0,0,0)",
                       "font": {"color": "lightgrey"},
                       "margin": {'t': 30},
                       "xaxis": dict(title= 'Time'),
                       "yaxis": dict(title= 'Price')
                        },
            }


# tab 4 graph
@app.callback(Output('tab4 team view', 'figure'),
              [Input('tab4 time unit', 'value')])

def update_tab4_team_view(time):
    tab4_df_user = trade_table[['User','Timestamp','Time Frame','Size/Notional']]
    temp_df = tab4_df_user[tab4_df_user['Time Frame']==time].sort_values('Timestamp')
    users = list(temp_df['User'])
    users = np.unique(users)
#    temp = trade_table[trade_table['Time Frame']==time]
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


if __name__ == '__main__':
    app.run_server()