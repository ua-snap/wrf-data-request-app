import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import json
import pandas as pd
import numpy as np
import plotly
import copy

app = dash.Dash()

app.scripts.config.serve_locally = True
# app.css.config.serve_locally = True

# setup our data
DF_VARS = pd.read_csv( './data/wrf-variables.csv' )
DF_VARS_OUT = DF_VARS[['Variable']].copy( deep=True )
DF_VARS_OUT.loc[:,'hourly'] = ''
DF_VARS_OUT.loc[:,'daily'] = ''
DF_VARS_OUT.loc[:,'monthly'] = ''

app.layout = html.Div([
    html.Div([html.H4('WRF Variables Selector')]),
    html.Div([
        # dcc.Checklist(
        #     options=[
        #         {'label': 'hourly', 'value': 'hourly'},
        #         {'label': 'daily', 'value': 'daily'},
        #         {'label': 'monthly', 'value': 'monthly'}
        #     ],
        #     values=[],
        #     labelStyle={'display': 'inline-block'},
        #     id='time-checklist'
        # ),
        html.Div([
            dcc.Dropdown(
                options=[
                    {'label': 'hourly', 'value': 'hourly'},
                    {'label': 'daily', 'value': 'daily'},
                    {'label': 'monthly', 'value': 'monthly'}
                ],
                value='daily',
                id='time-checklist'
            ),], className='two columns'),

            html.Div([
                dcc.Input(
                    placeholder='Enter a valid email address here...',
                    type='email',
                    value='',
                    id='email-input'
                ),
                html.Button(
                    children = 'send_email',
                    id = 'send-email-button',
                    type = 'submit',
                    n_clicks = 0
                    ),
                ],
                style = dict(
                    width = '30%',
                    display = 'table-cell',
                    ),
                className='row'),

        ], className='row'),
        html.Div([
            html.Div([
                dt.DataTable(
                    rows=DF_VARS.to_dict('records'),
                    row_selectable=True,
                    filterable=False,
                    sortable=False,
                    selected_row_indices=[],
                    max_rows_in_viewport=50,
                    id='datatable-wrf-variables'
                ),], className='eight columns'),

            html.Div([
                dt.DataTable(
                    rows=DF_VARS_OUT.to_dict('records'),
                    row_selectable=False,
                    filterable=False,
                    sortable=False,
                    selected_row_indices=[],
                    max_rows_in_viewport=50,
                    id='datatable-wrf-variables-selection'
                ),], className='four columns'),

        ], className="row" ),
        html.Div(id='email-temp')
])

# style={'display': 'none'}

@app.callback(
    Output('email-temp', 'children'),
    [Input('send-email-button', 'n_clicks')],
    [ State('email-input', 'value'), 
    State('datatable-wrf-variables-selection', 'rows')] )
def send_email( nclicks, email_addy, rows ):
    df = pd.DataFrame.from_records( rows )
    out_fn = './tmp_output/temp-selection-output_{}.csv'.format(email_addy)
    df.to_csv( out_fn, sep=',', index=False )
    return out_fn

@app.callback(
    Output('datatable-wrf-variables-selection', 'rows'),
    [Input('datatable-wrf-variables', 'selected_row_indices'),
    Input('time-checklist', 'value')],
    [State('datatable-wrf-variables-selection', 'rows')])
def update_rows(row_update, aggregation, rows):
    print(aggregation)
    row_copy = copy.deepcopy(rows)
    
    for idx,row in enumerate(row_copy):
        if idx in row_update:
            row_copy[idx][aggregation] = 'X'
        else:
            row_copy[idx][aggregation] = ''
    return row_copy

@app.callback(
    Output('datatable-wrf-variables','selected_row_indices'),
    [Input('time-checklist', 'value')],
    [State('datatable-wrf-variables-selection', 'rows')])
def update_table_selection(aggregation, rows):
    row_copy = copy.deepcopy( rows )
    table_selection = []
    for idx,row in enumerate(row_copy):
        if row[aggregation] == 'X':
            table_selection = table_selection + [idx]
    return table_selection


app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

if __name__ == '__main__':
    app.run_server(debug=True)
