import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import pandas as pd
import numpy as np
import plotly, json, copy
# email imports 
import smtplib, glob
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

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
    if email_addy:
        out_fn_list = []
        for model_scenario,rows in ALL_DATA.items(): 
            df = pd.DataFrame.from_records( rows )
            out_fn = './tmp_output/temp-selection-output_{}_{}.csv'.format(model_scenario.replace(' ','_'), email_addy)
            df.to_csv( out_fn, sep=',', index=False )
            out_fn_list = out_fn_list + [out_fn]
    
        EMAIL_BODY='''
        'Greetings,\n\n
        Here are the CSV file references of the variables you requested.\n\n
        We will be in touch with the data once is has been packaged up.\n\n
        Best Wishes,\n
        SNAP Data Team'
        '''        
        files=[i for i in glob.glob('./tmp_output/*{}*.csv').format(email_addy) ]
        out = send_mail( [email_addy, 'malindgren@alaska.edu'], 
            '[SNAP Data Request] Your WRF Data Requested Variables Reference', 
            EMAIL_BODY, files )
        _ = [ os.unlink(fn) for fn in files ]
    return 1

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

def send_mail( send_to, subject, text, files=None ):
    assert isinstance(send_to, list)

    username = "snap.data.requests@gmail.com"
    password = os.environ['GPASS']

    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)

    server = smtplib.SMTP("smtp.gmail.com:587")
    server.starttls()
    server.login(username,password)
    server.sendmail(username, send_to, msg.as_string())
    server.quit()
    

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

if __name__ == '__main__':
    app.run_server(debug=True)
