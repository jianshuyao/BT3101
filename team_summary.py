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
from textwrap import dedent as d


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# data for Tab 4
df = pd.read_excel('C:/Users/Bixuan/Desktop/NUS/BT3101/Code/trader_pnl.xlsx',encoding = "ISO-8859-1")
# figure for Tab 4
fig4 = go.Figure()
fig4.add_trace(go.Scatter(
                x=df.Date,
                y=df['A_PNL'],
                name="Trader A",
                line_color='blue',
                opacity=0.8))

fig4.add_trace(go.Scatter(
                x=df.Date,
                y=df['B_PNL'],
                name="Trader B",
                line_color='red',
                opacity=0.8))

fig4.add_trace(go.Scatter(
                x=df.Date,
                y=df['C_PNL'],
                name="Trader C",
                line_color='green',
                opacity=0.8))

fig4.add_trace(go.Scatter(
                x=df.Date,
                y=df['D_PNL'],
                name="Trader D",
                line_color='purple',
                opacity=0.8))

fig4.add_trace(go.Scatter(
                x=df.Date,
                y=df['E_PNL'],
                name="Trader E",
                line_color='orange',
                opacity=0.8))

# Use date string to set xaxis range
fig4.update_layout(xaxis_range=['2018-01-01','2018-01-31'],
                  title_text="Team Performance")


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
                    html.H3('Individual Summary'),
                    # Textbox Row 1
                    html.Div(className='row', children=[
                        html.Div([
                            dcc.Markdown(d("""
                                **TOTAL PNL**

                                100
                            """)),
                            html.Pre(id='total-pnl')
                        ], className='three columns'),

                        html.Div([
                            dcc.Markdown(d("""
                                **NO. OF PORTFOLIOS**

                                12
                            """)),
                            html.Pre(id='no-of-portfolios'),
                        ], className='three columns'),

                        html.Div([
                            dcc.Markdown(d("""
                                **LAST WEEK TRADES**

                                20
                            """)),
                            html.Pre(id='last-week-trades'),
                        ], className='three columns'),


                    ]),
                    #Textbox Row 2
                    html.Div(className='row', children=[
                        html.Div([
                            dcc.Markdown(d("""
                                **SHARPE RATIO**

                                1.2
                            """)),
                            html.Pre(id='sharpe-ratio')
                        ], className='three columns'),

                        html.Div([
                            dcc.Markdown(d("""
                                **SORTING RATIO**

                                1.2
                            """)),
                            html.Pre(id='sorting-ratio'),
                        ], className='three columns'),

                        html.Div([
                            dcc.Markdown(d("""
                                **HIT RATIO**

                                1.2
                            """)),
                            html.Pre(id='hit-ratio'),
                        ], className='three columns'),


                    ]),  
                    # Dropdown
                    html.Div([
                            # Select Timeframe
                            html.P([
                                html.Label('Select Timeframe'),
                                dcc.Dropdown(id='Timeframe-selector',
                                            options=[
                                                {'label': 'Daily', 'value': 'Daily'},
                                                {'label': 'Weekly', 'value': 'Weekly'},
                                                {'label': 'Monthly', 'value': 'Monthly'}
                                            ],
                                            value='Weekly')
                            ], style = {'width': '400px',
                                        'fontSize' : '20px',
                                        'padding-left' : '100px',
                                        'display': 'inline-block'}),           
                    ]),                    
                    # Graph
                    html.Div([
                            
                        html.Div([
                            dcc.Graph(id='team-view', figure = fig4)
                        ]),
                    ]),

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

@app.callback(
    Output(component_id='team-view', component_property='figure'),
    [
        Input(component_id='Timeframe-selector', component_property='value')
    ]
)
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
def load_timeframe_options():
    options = (
        [{'label': timeframe, 'value': timeframe}
         for timeframe in ['Daily','Weekly','Monthly']]
    )
    return options


              


if __name__ == '__main__':
    app.run_server()