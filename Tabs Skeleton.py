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


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Initialise trade table
columns = ['Portfolio','Type of Trade','Direction','Product', 
           'Price', 'Size/Notional', 'Tenor', 'Amount to Risk',
           'Time Frame', 'Strategy Type']
trade_table = pd.DataFrame(columns = columns)

app.layout = html.Div([
    html.H1('Risk Analytics Platform'),
    
    dcc.Tabs(id="tabs", children=[
        dcc.Tab(label='Individual Summary', children = [
                html.Div([
                    html.H3('Individual Summary')
                ])        
        ]),
        
        dcc.Tab(label='Input Trade', children = [
                html.H3('Input Trade')  
        ]),
        
        dcc.Tab(label='Individual Analysis', children = [
                html.Div([
                    html.H3('Individual Analysis')
                ])
        ]),
        
        dcc.Tab(label='Team Summary', children = [
                html.Div([
                    html.H3('Individual Summary')
                ])        
        ]),        
    ])
])

if __name__ == '__main__':
    app.run_server()
