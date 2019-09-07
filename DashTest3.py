# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 17:35:26 2019

@author: dell
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 15:21:14 2019

@author: dell
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 14:22:03 2019

@author: Shuyao
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import plotly.graph_objs as go

df = pd.read_excel('C:/jsy/UNI/BT3101/Data/Rate.xlsx',encoding = "ISO-8859-1")

# Get Data/Data Processing
def get_currency():
    currency = list(df['Currency'])
    currency = np.unique(currency)
    return currency

def get_prices(currency):
    result = df[df['Currency'] == currency]
    return result

def load_currency_options():
    options = (
        [{'label': currency, 'value': currency}
         for currency in get_currency()]
    )
    return options

# Layout
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

df_curr = get_currency()[0]
default = go.Scatter(
            x=df[df['Currency'] == df_curr]['Date'],
            y=df[df['Currency'] == df_curr]['Price'],
            mode='lines+markers',
            name = df_curr)

layout = go.Layout(
            title = 'Daily Prices (' + df_curr + ')',
            xaxis={'type': 'date', 'title': 'Date'},
            yaxis={'title': 'Price'},
            hovermode='closest')

fig = go.Figure(data = [default],layout = layout)

app.layout = html.Div([
    # Header
    html.Div([
        html.H1('Daily Rate Viewer')  
    ]),   

    # Dropdown
    html.Div([
            # Select Currency
            html.P([
                html.Label('Select Currency'),
                dcc.Dropdown(id='currency-selector',
                             options=load_currency_options(),
                             value = load_currency_options()[0])
            ], style = {'width': '400px',
                        'fontSize' : '20px',
                        'padding-left' : '100px',
                        'display': 'inline-block'}),           
    ]),
    
    # Graph
    html.Div([
            
        html.Div([
            dcc.Graph(id='daily-graph', figure = fig)
        ]),
    ]),
])

# Interaction
# Load Currency Dropdown
@app.callback(
    Output(component_id='daily-graph', component_property='figure'),
    [
        Input(component_id='currency-selector', component_property='value')
    ]
)
def load_daily_graph(currency):
    result = get_prices(currency)
    fig = go.Figure(data = [result],
                    layout = go.Layout(title = 'Daily Prices (' + currency + ')',
                                       xaxis={'type': 'date', 'title': 'Date'},
                                       yaxis={'title': 'Price'},
                                       hovermode='closest'))
    return fig



if __name__ == '__main__':
    app.run_server()