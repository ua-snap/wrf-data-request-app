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
DF_VARS = DF_VARS[['Variable','Name','Dimensions','Units']]
DF_VARS.columns = ['Variable','Description','Dimensions','Units']
DF_VARS_OUT = DF_VARS[['Variable']].copy( deep=True )
DF_VARS_OUT.loc[:,'hourly'] = ''
DF_VARS_OUT.loc[:,'daily'] = ''
DF_VARS_OUT.loc[:,'monthly'] = ''

ALL_DATA = { model_scenario:DF_VARS_OUT.copy(deep=True).to_dict('records') for model_scenario in ['ERA-Interim','GFDL-CM3 Historical','GFDL-CM3 RCP85','NCAR-CCSM4 Historical','NCAR-CCSM4 RCP85']}

app.layout = html.Div([
    html.Div([html.H4('WRF Variables Selector')]),
    html.Div([
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
            dcc.Dropdown(
                options=[
                    {'label': 'ERA-Interim', 'value': 'ERA-Interim'},
                    {'label': 'GFDL-CM3 Historical', 'value': 'GFDL-CM3 Historical'},
                    {'label': 'GFDL-CM3 RCP85', 'value': 'GFDL-CM3 RCP85'},
                    {'label': 'NCAR-CCSM4 Historical', 'value': 'NCAR-CCSM4 Historical'},
                    {'label': 'NCAR-CCSM4 RCP85', 'value': 'NCAR-CCSM4 RCP85'}
                ],
                value='GFDL-CM3 Historical',
                id='model-scenario-checklist'
            ),], className='three columns'),
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
                    column_widths=[150,375,120,100],
                    id='datatable-wrf-variables'
                ),], className='seven columns'),

            html.Div([
                dt.DataTable(
                    rows=DF_VARS_OUT.to_dict('records'),
                    row_selectable=False,
                    filterable=False,
                    sortable=False,
                    selected_row_indices=[],
                    max_rows_in_viewport=50,
                    column_widths=[150,95,95,95],
                    id='datatable-wrf-variables-selection'
                ),], className='four columns'),

        ], className="row" ),
        html.Div(id='email-temp')
])

# # style={'display': 'none'}

@app.callback(
    Output('email-temp', 'children'),
    [Input('send-email-button', 'n_clicks')],
    [ State('email-input', 'value'), 
    State('datatable-wrf-variables-selection', 'rows')] )
def send_email( nclicks, email_addy, rows ):
    for model_scenario,rows in ALL_DATA.items(): 
        df = pd.DataFrame.from_records( rows )
        out_fn = './tmp_output/temp-selection-output_{}_{}.csv'.format(model_scenario.replace(' ','_'), email_addy)
        df.to_csv( out_fn, sep=',', index=False )
    return out_fn

@app.callback(
    Output('datatable-wrf-variables-selection', 'rows'),
    [Input('datatable-wrf-variables', 'selected_row_indices'),
    Input('time-checklist', 'value'),
    Input('model-scenario-checklist','value')],
    [State('datatable-wrf-variables-selection', 'rows')])
def update_rows( row_update, aggregation, model_scenario, rows ):
    if model_scenario in ALL_DATA.keys():
        row_copy = ALL_DATA[ model_scenario ]
    else:
        row_copy = rows # copy.deepcopy( rows )
    
    for idx,row in enumerate( row_copy ):
        if idx in row_update:
            row[ aggregation ] = 'X'
        else:
            row[ aggregation ] = ''

    ALL_DATA[ model_scenario ] = row_copy
    return row_copy

@app.callback(
    Output('datatable-wrf-variables', 'selected_row_indices'),
    [Input('model-scenario-checklist','value'),
    Input('time-checklist', 'value')])
def update_rows_selector( model_scenario, aggregation ):
    rows = ALL_DATA[model_scenario]
    l = [ i[aggregation] for i in rows ]
    ind, = np.where( np.array(l) == 'X' )
    return ind.tolist()

# @app.callback(
#     Output('datatable-wrf-variables','selected_row_indices'),
#     [Input('time-checklist', 'value')],
#     [State('datatable-wrf-variables-selection', 'rows')])
# def update_table_selection(aggregation, rows):
#     row_copy = copy.deepcopy( rows )
#     table_selection = []
#     for idx,row in enumerate(row_copy):
#         if row[aggregation] == 'X':
#             table_selection = table_selection + [idx]
#     return table_selection


app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

if __name__ == '__main__':
    app.run_server(debug=True)
