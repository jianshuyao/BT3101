# -*- coding: utf-8 -*-

## create four tabs for dashboard

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
columns = ['Portfolio','Type of Trade','Direction','Product', 
           'Price', 'Size/Notional', 'Tenor', 'Amount to Risk',
           'Time Frame', 'Strategy Type']

trade_table = pd.DataFrame(columns = columns)

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
        
        dcc.Tab(label='Individual Analysis', children = [
            html.H3('Individual Analysis'),           
            html.Div([
                dcc.Dropdown(
                    options=[
                        {'label': 'Daily', 'value': 'Daily'},
                        {'label': 'Weekly', 'value': 'Weekly'},
                        {'label': 'Monthly', 'value': 'Monthly'}
                    ],
                    value='Weekly'
                ),                 
                dcc.Graph(
                    id="Live PnL",
                    figure={
                        'data': [
                            {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'line', 'name': 'Portfolio A'},
                            {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'line', 'name': 'Portfolio B'},
                        ],
                        'layout': {
                            'title': 'Live PnL Chart'
                         }
                    })  
            ],style={ 'padding': 20}),

            html.Div([
                dcc.Dropdown(
                options=[
                    {'label': 'Portfolio A', 'value': 'A'},
                    {'label': 'Portfolio B', 'value': 'B'},
                    {'label': 'Portfolio C', 'value': 'C'}
                ],
                value='A'
                ),
            ]),

            html.Div(
                [

                    html.Div(
                        [html.H6(id="sharpe_ratio_text"), html.P("Sharpe Ratio")],
                        id="sharpe_ratio",
                        className="mini_container",
                    ),
                    html.Div(
                        [html.H6(id="hit_ratio_text"), html.P("Hit Ratio")],
                        id="hit_ratio",
                        className="mini_container",
                    ),
                    html.Div(
                        [html.H6(id="sortino_ratio_text"), html.P("Sortino Ratio")],
                        id="sortino_ratio",
                        className="mini_container",
                    ),
                ],
                id="info-container",
                className="row container-display",
            )
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




              


if __name__ == '__main__':
    app.run_server()
