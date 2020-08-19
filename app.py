import base64
import datetime
import io

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table

import plotly.express as px

import pandas as pd
import numpy as np

pd.options.plotting.backend = "plotly"

df = pd.DataFrame()

conVal=[]
numVal=[]
intVal=[]
col=[]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_url = ["https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css"]

app = dash.Dash(__name__, external_stylesheets=external_url, suppress_callback_exceptions=True)

intro = html.Div([
    html.H1('Data Visualize App'),
    html.Hr()
])

file_import = html.Div([
    html.H3('Import File'),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-data-upload'),
])

app.layout= html.Div([
    intro,
    file_import
])

operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]

# filter translate function
def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3

def parse_contents(contents, filename, date):
    global df
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xlsx' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))

        df.columns = [column.replace(" ", "_") for column in df.columns]
        # determine numeric or continous
        conVal.clear()
        numVal.clear()
        intVal.clear()
        col.clear()
        for i in range(0, df.shape[1]):
            checknum = df[df.keys()[i]].nunique()
            # print(df[df.keys()[i]].dtypes)
            if (checknum > 10 or df[df.keys()[i]].dtypes == 'float64'):
                conVal.append(str(df.keys()[i]))
                col.append(str(df.keys()[i]))
            elif (checknum > 10 or df[df.keys()[i]].dtypes == 'int64'):
                intVal.append(str(df.keys()[i]))
                col.append(str(df.keys()[i]))
            else:
                numVal.append(str(df.keys()[i]))
                col.append(str(df.keys()[i]))

        # print(conVal)
        # print(numVal)
        # print(col)


    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H6(filename),
        html.P(datetime.datetime.fromtimestamp(date)),

        # Tab이 왔으면 좋겠는 위치
        html.Div([
            dcc.Tabs(
                id="tabs",
                value='tab-table',
                children=[
                    dcc.Tab(label="Data Pivot Table", value='tab-table'),
                    dcc.Tab(label="Graph", value='tab-graph'),
                    dcc.Tab(label="Dash Board", value='tab-dash')
                ]),
                html.Div(id='tabs-content-props')
        ]),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

@app.callback(Output('tabs-content-props', 'children'),[Input('tabs', 'value')])
def tab_content(tab):
    if tab == 'tab-table':
        return html.Div([
            html.Br(),
            dash_table.DataTable(
                id='pivot-table',
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],

                filter_action='custom',
                filter_query='',

                sort_action='custom',
                sort_mode='multi',
                sort_by=[ ]
            )
        ])
    elif tab == 'tab-graph':
        return html.Div([
            # graph type: scatter / plot / box / pie / histogram
            # HOW to make graph interactive?
            html.H6('Graph Part'),
            html.Label(["Graph Type",
                        dcc.Dropdown(
                            options=[
                                {'label': 'Scatter Plot', 'value': 'scatter'},
                                {'label': 'box plot', 'value': 'box'},
                                {'label': 'Pie Chart', 'value': 'pie'},
                                {'label': 'Histogram', 'value': 'histogram'},
                                {'label': 'Bar Chart', 'value': 'bar'},
                                {'label': '3D Scatter', 'value': '3dscatter'},
                            ],
                            placeholder="Select a graph type",
                            id="graph-dropdown"
                        ),
            ]),
            html.Div(
                id='graph-container'
            )
        ])
    elif tab == 'tab-dash':
        return html.Div([
            html.H6('Dash board')
        ])

@app.callback(Output('graph-container', "children"),[Input("graph-dropdown", "value")])
def setcolumns(graphoption):
    if graphoption == 'scatter':
        return html.Div([
            html.Label([
                "X axis",
                dcc.Dropdown(
                    options=[{'label':i , 'value':i } for i in col],
                    placeholder="Select a X axis",
                    id="col-1"
                )
            ]),
            html.Label([
                "Y axis",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in col],
                    placeholder="Select a Y axis",
                    id="col-2"
                )
            ]),
            html.Label([
                "Color",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in col if i not in conVal],
                    placeholder="Select color",
                    id="color"
                )
            ]),
            html.Br(),
            html.Button(
                children='Apply', id='scatter-btn', n_clicks=0
            ),
            html.Br(),
            dcc.Graph(id='scatter-graph')
        ])
    elif graphoption == 'box':
        return html.Div([
            html.Label([
                "X axis",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in numVal],
                    placeholder="Select a X axis",
                    id="col-1"
                )
            ]),
            html.Label([
                "Y axis",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in conVal],
                    placeholder="Select a Y axis",
                    id="col-2"
                )
            ]),
            html.Label([
                "Color",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in col if i not in conVal],
                    placeholder="Select color",
                    id="color"
                )
            ]),
            html.Br(),
            html.Button(
                children='Apply', id='box-btn', n_clicks=0
            ),
            html.Br(),
            dcc.Graph(id='box-graph')
        ])
    elif graphoption == 'bar':
        return html.Div([
            html.Label([
                "X axis",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in conVal],
                    placeholder="Select a X axis",
                    id="col-1"
                )
            ]),
            html.Label([
                "Y axis",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in conVal],
                    placeholder="Select a Y axis",
                    id="col-2"
                )
            ]),
            html.Label([
                "Color",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in col if i not in conVal],
                    placeholder="Select color",
                    id="color"
                )
            ]),
            html.Br(),
            html.Button(
                children='Apply', id='bar-btn', n_clicks=0
            ),
            html.Br(),
            dcc.Graph(id='bar-graph')
        ])
    elif graphoption == 'histogram':
        return html.Div([
            html.Label([
                "Columns",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in col if i not in conVal],
                    placeholder="Select a column",
                    id="col-1"
                )
            ]),
            html.Label([
                "Color",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in col if i not in conVal],
                    placeholder="Select color",
                    id="color"
                )
            ]),
            html.Br(),
            html.Button(
                children='Apply', id='histo-btn', n_clicks=0
            ),
            html.Br(),
            dcc.Graph(id='histo-graph')
        ])
    elif graphoption == 'pie':
        return html.Div([
            html.Label([
                "Columns",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in col],
                    placeholder="Select a column",
                    id="col-1"
                )
            ]),
            html.Label([
                "Color",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in col if i not in conVal],
                    placeholder="Select color",
                    id="color"
                )
            ]),
            html.Br(),
            html.Button(
                children='Apply', id='pie-btn', n_clicks=0
            ),
            html.Br(),
            dcc.Graph(id='pie-graph')
        ])
    elif graphoption == '3dscatter':
        return html.Div([
            html.Label([
                "X axis",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in col],
                    placeholder="Select a X axis",
                    id="col-1"
                )
            ]),
            html.Label([
                "Y axis",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in col],
                    placeholder="Select a Y axis",
                    id="col-2"
                )
            ]),
            html.Label([
                "Z axis",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in col],
                    placeholder="Select a Y axis",
                    id="col-3"
                )
            ]),
            html.Label([
                "Color",
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in col if i not in conVal],
                    placeholder="Select color",
                    id="color"
                )
            ]),
            html.Br(),
            html.Button(
                children='Apply', id='3dscatter-btn', n_clicks=0
            ),
            html.Br(),
            dcc.Graph(id='3dscatter-graph')
        ])


# pivot-table의 데이터는 같은 레이아웃일 때만 가져올 수 있음 (필터링 관련)
# graph function
@app.callback(Output('scatter-graph', "figure"), [Input('scatter-btn', "n_clicks")],[State('col-1', "value"), State('col-2', "value"), State('color', "value")])
def appendScatter(clicks, col1, col2, color):
    print(clicks, col1, col2, color)
    global df
    fig=px.scatter()
    if clicks > 0:
        if color == None:
            fig = px.scatter(data_frame=df, x=col1, y=col2)
        else:
            fig = px.scatter(data_frame=df, x=col1, y=col2, color=color)
        return fig
    return fig

@app.callback(Output('pie-graph', "figure"), [Input('pie-btn', "n_clicks")],[State('col-1', "value"), State('color', "value")])
def appendPie(clicks, col1, color):
    print(clicks, col1, color)
    global df
    fig=px.pie()
    if clicks > 0:
        if color == None:
            fig = px.pie(data_frame=df, names=col1)
        else:
            fig = px.pie(data_frame=df, names=col1, color=color)
        return fig
    return fig

@app.callback(Output('bar-graph', "figure"), [Input('bar-btn', "n_clicks")],[State('col-1', "value"),State('col-2', "value"), State('color', "value")])
def appendBar(clicks, col1, col2, color):
    print(clicks, col1, col2, color)
    global df
    fig=px.bar()
    if clicks > 0:
        if color == None:
            fig = px.bar(data_frame=df, x=col1, y=col2)
        else:
            fig = px.bar(data_frame=df, x=col1, y=col2, color=color)
        return fig
    return fig

@app.callback(Output('histo-graph', "figure"), [Input('histo-btn', "n_clicks")],[State('col-1', "value"),State('color', "value")])
def appendBar(clicks, col1, color):
    print(clicks, col1, color)
    global df
    fig=px.histogram()
    if clicks > 0:
        if color == None:
            fig = px.histogram(data_frame=df, x=col1)
        else:
            fig = px.histogram(data_frame=df, x=col1, color=color)
        return fig
    return fig

@app.callback(Output('box-graph', "figure"), [Input('box-btn', "n_clicks")],[State('col-1', "value"),State('col-2', "value"),State('color', "value")])
def appendBox(clicks, col1, col2, color):
    print(clicks, col1, col2, color)
    global df
    fig=px.box()
    if clicks > 0:
        if color == None:
            fig = px.box(data_frame=df, x=col1, y=col2)
        else:
            fig = px.box(data_frame=df, x=col1, y=col2, color=color)
        return fig
    return fig

@app.callback(Output('3dscatter-graph', "figure"), [Input('3dscatter-btn', "n_clicks")],[State('col-1', "value"),State('col-2', "value"),State('col-3', "value"),State('color', "value")])
def appendBox(clicks, col1, col2, col3, color):
    print(clicks, col1, col2, col3, color)
    global df
    fig=px.scatter_3d()
    if clicks > 0:
        if color == None:
            fig = px.scatter_3d(data_frame=df, x=col1, y=col2, z=col3)
        else:
            fig = px.scatter_3d(data_frame=df, x=col1, y=col2, z=col3, color=color)
        return fig
    return fig
# @app.callback(Output('graph-container', "children"),
#               [Input ('pivot-table'), "data"])
# def update_graph(rows):
#     dff = pd.DataFrame(rows)

# Data Pivot - filtering function
@app.callback(
    Output('pivot-table', "data"),
    [Input('pivot-table', "sort_by"),
     Input('pivot-table', "filter_query")])
def update_table(sort_by, filter):
    global df
    filtering_expressions = filter.split(' && ')
    dff = df
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    if len(sort_by):
        dff = dff.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )


    return dff.to_dict('records')

# file upload function
@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children


if __name__ == '__main__':
    app.scripts.config.serve_locally = True
    app.run_server(host='localhost', port='8585', debug=True)