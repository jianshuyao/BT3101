import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime as dt
import dash_table


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Initialise trade table
data = [('A', 'type','dir','SGD','1','10','tenor','risk','week','strategy','1'),
        ('A', 'type','dir','CNY','1.5','20','tenor','risk','week','strategy','2'),
        ('A', 'type','dir','GBP','0.5','30','tenor','risk','week','strategy','3'),
        ('B', 'type','dir','JPY','3','20','tenor','risk','week','strategy','1'),
        ('B', 'type','dir','CHF','2','10','tenor','risk','week','strategy','2'),
        ('B', 'type','dir','USD','2.5','30','tenor','risk','week','strategy','3'),
        ('C', 'type','dir','EUR','3.5','10','tenor','risk','week','strategy','1'),
        ('C', 'type','dir','SGD','2','10','tenor','risk','week','strategy','2'),
        ('C', 'type','dir','CNY','1.5','40','tenor','risk','week','strategy','3'),
       ('A', 'type','dir','SGD','1','10','tenor','risk','day','strategy','3'),
        ('A', 'type','dir','CNY','1.5','20','tenor','risk','day','strategy','2'),
        ('A', 'type','dir','GBP','0.5','30','tenor','risk','day','strategy','1'),
        ('B', 'type','dir','JPY','3','20','tenor','risk','day','strategy','3'),
        ('B', 'type','dir','CHF','2','10','tenor','risk','day','strategy','2'),
        ('B', 'type','dir','USD','2.5','30','tenor','risk','day','strategy','1'),
        ('C', 'type','dir','EUR','3.5','10','tenor','risk','day','strategy','3'),
        ('C', 'type','dir','SGD','2','10','tenor','risk','day','strategy','2'),
        ('C', 'type','dir','CNY','1.5','40','tenor','risk','day','strategy','1'),
       ('A', 'type','dir','SGD','1','10','tenor','risk','month','strategy','2'),
        ('A', 'type','dir','CNY','1.5','20','tenor','risk','month','strategy','3'),
        ('A', 'type','dir','GBP','0.5','30','tenor','risk','month','strategy','1'),
        ('B', 'type','dir','JPY','3','20','tenor','risk','month','strategy','2'),
        ('B', 'type','dir','CHF','2','10','tenor','risk','month','strategy','3'),
        ('B', 'type','dir','USD','2.5','30','tenor','risk','month','strategy','1'),
        ('C', 'type','dir','EUR','3.5','10','tenor','risk','month','strategy','2'),
        ('C', 'type','dir','SGD','2','10','tenor','risk','month','strategy','3'),
        ('C', 'type','dir','CNY','1.5','40','tenor','risk','month','strategy','1'),]

columns = ['Portfolio','Type of Trade','Direction','Product', 
           'Price', 'Size/Notional', 'Tenor', 'Amount to Risk',
           'Time Frame', 'Strategy Type','time stamp']

trade_table = pd.DataFrame(data, columns = columns)
trade_table['Size/Notional'] = trade_table['Size/Notional'].astype('int')
groupby_product = pd.DataFrame(columns=['Portfolio','Size/Notional'])
groupby_product.index.name = 'Product'

for p in trade_table.Portfolio.unique():
    temp = trade_table[trade_table['Portfolio']==p][['Product','Size/Notional']].groupby('Product').sum()
    temp.insert(0,'Portfolio',temp.size*[p])
    groupby_product = groupby_product.append(temp)
    
groupby_product = groupby_product.reset_index(level=['Product'])
groupby_product = groupby_product[['Portfolio','Product','Size/Notional']]


# Dashboard layout
app.layout = html.Div([
    html.H1('Risk Analytics Platform'),
    
    dcc.Tabs(id="tabs", children=[
        dcc.Tab(label='Individual Summary', children = [
                html.Div([
                    html.H3('Individual Summary')
                ])        
        ]),
        
        dcc.Tab(label='Input Trade', children = [
                html.H3('Input Trade'),
                html.Div([
                    dcc.Input(id = 'portfolio', type = 'text', placeholder = 'Portfolio'),
                    dcc.Input(id = 'type', type = 'text', placeholder = 'Type of Trade'),
                    dcc.Input(id = 'product', type = 'text', placeholder = 'Product'),
                    dcc.Input(id = 'direction', type = 'text', placeholder = 'Direction'),
                    dcc.Input(id = 'price', type = 'number', placeholder = 'Price'),
                    dcc.Input(id = 'size', type = 'number', placeholder = 'Size/Notional'),
                    dcc.Input(id = 'tenor', type = 'text', placeholder = 'Tenor'),
                    dcc.Input(id = 'risk', type = 'number', placeholder = 'Amount to Risk'),
                    dcc.Input(id = 'timeframe', type = 'text', placeholder = 'Timeframe'),
                    dcc.Input(id = 'strategy', type = 'text', placeholder = 'Strategy Type')
                ], style = {'padding': 20}),
                html.Div([
                    html.Button('Submit', id = 'button')
                ], style = {'padding': 20}),
                html.Div([
                    dash_table.DataTable(id = 'trade-table',
                                         columns = [{"name": i, "id": i} for i in trade_table.columns]),
                ], style = {'padding': 20})     
        ]),
        
        
        
        dcc.Tab(label='Individual Analysis', 
                children = [
                    html.H3('Individual Analysis'),  
                    
                    html.Div([
                        ###Drodown to select time unit
                        html.Div([
                            dcc.Dropdown(id='tab3 time unit',
                                         options=[{'label': 'Daily', 'value': 'day'},
                                                  {'label': 'Weekly', 'value': 'week'},
                                                  {'label': 'Monthly', 'value': 'month'}],
                                         value='day')],
                            style={'width': '48%', 'display': 'inline-block'}
                        ),
                    
                        ###Dropdown to select portfolio
                        html.Div([
                            dcc.Dropdown(id='tab3 portfolio',
                                         options=[{'label': 'Portfolio A', 'value': 'A'},
                                                  {'label': 'Portfolio B', 'value': 'B'},
                                                  {'label': 'Portfolio C', 'value': 'C'}],
                                         value='A')],
                            style={'width': '48%', 'display': 'inline-block'}
                        )
                    ]),                          
                                        
                    dcc.Graph(id='tab3 daily pnl',
                              figure={'layout':{'title': 'Daily PnL'}}),
                    
                    
                    ###text boxes to display ratio for selected porfolio
                    html.Div([
                        html.Div([
                            html.H6(id="sharpe_ratio_text"), html.P("Sharpe Ratio")],
                            id="sharpe_ratio",
                            className="mini_container"),
                        
                        html.Div([
                            html.H6(id="hit_ratio_text"), html.P("Hit Ratio")],
                            id="hit_ratio",
                            className="mini_container"),
                        
                        html.Div(
                            [html.H6(id="sortino_ratio_text"), html.P("Sortino Ratio")],
                            id="sortino_ratio",
                            className="mini_container")],
                        
                        id="info-container",
                        className="row container-display"),
                    
                    html.Div([
                        dash_table.DataTable(
                            id = 'groupby_product',
                            columns = [{"name": i, "id": i} for i in groupby_product.columns],
                            data = groupby_product.to_dict('records') 
                        )], 
                        style = {'padding': 20})
                
                ]),
        
        
        
        dcc.Tab(label='Team Summary', children = [
                html.Div([
                    html.H3('Individual Summary')
                ])        
        ]),        
    ])
])

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
    State('strategy', 'value')])
def update_table(n_clicks, portfolio, type, product, direction, price, size, tenor, risk, timeframe, strategy):
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
    return trade_table.head().to_dict('records')


###tab3 daily pnl
@app.callback(Output('tab3 daily pnl', 'figure'),
              [Input('tab3 time unit', 'value'),
               Input('tab3 portfolio', 'value')]
             )
def update_tab3_daily(time,portfolio):
    temp_df = trade_table[trade_table['Portfolio']==portfolio]
    temp_df = temp_df[temp_df['Time Frame']==time].sort_values('time stamp')
#    temp = trade_table[trade_table['Time Frame']==time]
    
    return {'data': [go.Scatter(x=temp_df['time stamp'], 
                                y=temp_df['Price'],
                                mode='lines+markers',
                                name='lines+markers')],
            'layout': go.Layout(xaxis={'title': 'time'},
                                yaxis={'title': 'price'})}
    
    
              


if __name__ == '__main__':
    app.run_server()
