from dash import html, dcc, Input, Output, callback, callback_context, State
from .utils import utils, querys
from db_utils import load_data_from_psql
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import dash_daq as daq
import pandas as pd
import numpy as np
import dash
import joblib
import tensorflow as tf
from datetime import timedelta, datetime
import pytz
from .utils.kerasWrapper import KerasWrapper

import __main__
__main__.KerasWrapper = KerasWrapper

dash.register_page(__name__)

def get_data_day(start, end) -> pd.DataFrame:
    print("NOT CACHED DAY")
    fbk_data=  load_data_from_psql(testnewdf(start, end))
    #print(fbk_data)
    return (fbk_data)

def testnewdf(start, end, node=1):
    
    return f"""WITH sensor_data AS (
    SELECT
        p.node_id,
        s.name AS sensor_description,
        p.sensor_ts AS ts,
        pd.r1 AS heater_res,
        pd.r2 AS signal_res,
        pd.volt AS volt,
        p.p,
        p.t,
        p.rh
    FROM packet_data pd
        LEFT JOIN packet p ON p.id = pd.packet_id
        LEFT JOIN sensor s ON s.id = pd.sensor_id
    where p.sensor_ts BETWEEN '{start}' AND '{end}' and p.node_id = {node}
)
SELECT
    ts,
    MAX(p) AS p,
    MAX(t) AS t,
    MAX(rh) AS rh,
    MAX(CASE WHEN sensor_description = 'S1_ID' THEN heater_res END) AS S1_R1,
    MAX(CASE WHEN sensor_description = 'S1_ID' THEN signal_res END) AS S1_R2,
    MAX(CASE WHEN sensor_description = 'S1_ID' THEN volt END) AS S1_Voltage,
    MAX(CASE WHEN sensor_description = 'S2_ID' THEN heater_res END) AS S2_R1,
    MAX(CASE WHEN sensor_description = 'S2_ID' THEN signal_res END) AS S2_R2,
    MAX(CASE WHEN sensor_description = 'S2_ID' THEN volt END) AS S2_Voltage,
    MAX(CASE WHEN sensor_description = 'S3_ID' THEN heater_res END) AS S3_R1,
    MAX(CASE WHEN sensor_description = 'S3_ID' THEN signal_res END) AS S3_R2,
    MAX(CASE WHEN sensor_description = 'S3_ID' THEN volt END) AS S3_Voltage,
    MAX(CASE WHEN sensor_description = 'S4_ID' THEN heater_res END) AS S4_R1,
    MAX(CASE WHEN sensor_description = 'S4_ID' THEN signal_res END) AS S4_R2,
    MAX(CASE WHEN sensor_description = 'S4_ID' THEN volt END) AS S4_Voltage,
    MAX(CASE WHEN sensor_description = 'S5_ID' THEN heater_res END) AS S5_R1,
    MAX(CASE WHEN sensor_description = 'S5_ID' THEN signal_res END) AS S5_R2,
    MAX(CASE WHEN sensor_description = 'S5_ID' THEN volt END) AS S5_Voltage,
    MAX(CASE WHEN sensor_description = 'S6_ID' THEN heater_res END) AS S6_R1,
    MAX(CASE WHEN sensor_description = 'S6_ID' THEN signal_res END) AS S6_R2,
    MAX(CASE WHEN sensor_description = 'S6_ID' THEN volt END) AS S6_Voltage,
    MAX(CASE WHEN sensor_description = 'S7_ID' THEN heater_res END) AS S7_R1,
    MAX(CASE WHEN sensor_description = 'S7_ID' THEN signal_res END) AS S7_R2,
    MAX(CASE WHEN sensor_description = 'S7_ID' THEN volt END) AS S7_Voltage,
    MAX(CASE WHEN sensor_description = 'S8_ID' THEN heater_res END) AS S8_R1,
    MAX(CASE WHEN sensor_description = 'S8_ID' THEN signal_res END) AS S8_R2,
    MAX(CASE WHEN sensor_description = 'S8_ID' THEN volt END) AS S8_Voltage
FROM sensor_data
GROUP BY ts
ORDER BY ts;"""
import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""  


pipeline2 = joblib.load('data/pipeline.pkl')

# Load the Keras model separately

model = tf.keras.models.load_model('data/model.h5')
#predictions = inference_func(input_data)['output'].numpy()

# Assign the loaded model to the pipeline
pipeline2.steps[-1][1].model = model

print(pipeline2.steps[-1][1].model)

pipeline2.steps[-1][1].model.compile(loss='mean_absolute_error', optimizer='adam', metrics=['mean_squared_error'])

df = utils.get_prediction_data()
df["Time"] = pd.to_datetime(df["Time"])

# add static station to simulate query
df["Station"] = "Parco S. Chiara"

# add random noise to dataframe
df["NO2_pred"] += np.random.rand(len(df)) * 10 - 5
df["CO_pred"] += np.random.rand(len(df)) - 0.5
df["O3_pred"] += np.random.rand(len(df)) * 10 - 5

fbk_stations = [{'label':'Parco S. Chiara','value':'Parco S. Chiara'},
                {'label':'Via Bolzano','value':'Via Bolzano', 'disabled':True}]
pollutants = [
    dict(label="Ozone", value="O3"),
    dict(label="Nitrogen Dioxide", value="NO2"),
    dict(label="PM10", value="PM10"),
    dict(label="Sulfur Dioxide", value="SO2"),
]

title = html.Div("Fitted FBK Data", className="header-title", style={"text-align": "center", "margin-bottom": "0.25rem"},)

# build dropdown of stations
dropdown_station = dcc.Dropdown(
    fbk_stations, id="selected-station", className="dropdown", value='Parco S. Chiara'
)
dropdown_wrapper = html.Div(
    [
        dropdown_station,
    ],
    className="dropdownWrapper",
)

download_btn = dbc.Button(
    [html.I(className="fa-solid fa-download"), " Download full data"],
    color="primary",
    id="btn_fbk_fitted",
    class_name="download-btn",
)
download_it = dcc.Download(id="download-fbk-fitted")

#periods = ["last 6 months", "last month", "last week", "last day", "last hour"]
periods = [
    {"label" : "last 6 months", "value" : "last 6 months"},
    {"label" : "last month", "value" : "last month"},
    {"label" : "last week",  "value" : "last week"},
    {"label" : "last day",   "value" : "last day"},
    {"label" : "last hour",  "value" : "last hour", 'disabled': True},
]

dropdown_period = dcc.Dropdown(
    periods, id="selected-period", className="dropdown", value='last week'
)

date_range = dcc.DatePickerRange(
    id="my-date-picker-range",
    month_format="MMMM Y",
    start_date_placeholder_text="Start Period",
    end_date_placeholder_text="End Period",
    clearable=True,
)

search = dbc.Button(
    children=html.I(className="fas fa-search"),
    id="btn_search_date",
    color="secondary",
    outline=True,
    className="me-1",
    size="sm",
    style={"width": "100%", "border": "1px solid #ccc"},
)

toast = dbc.Toast(
    [
        html.H4("Filter by:", style={"font-weight": "bold"}),
        dropdown_period,
        date_range,
        search,
        daq.ToggleSwitch(
            id="toggle-comparison",
            label="Compare with APPA",
            color="#0d6efd",
            className="ml-auto toggle",
            value=True,
        ),
    ],
    id="toast",
    header=html.P([html.I(className="fa-solid fa-gear"), " Settings"]),
    # body_style={"margin-bottom":"2rem"},
    style={"height": "100%"},
)


@callback(
    Output("download-fbk-fitted", "data"),
    Input("btn_fbk_fitted", "n_clicks"),
    prevent_initial_call=True,
)
def create_download_file(n_clicks):
    global df
    return dcc.send_data_frame(df.to_csv, "fbk_fitted_data.csv")


# build gas buttons
gas_btns = html.Div(
    dbc.RadioItems(
        id="selected-fbk-pollutant",
        class_name="btn-group",
        input_class_name="btn-check",
        label_class_name="btn btn-outline-primary",
        label_checked_class_name="active",
        options=pollutants,
        value="O3",
    ),
    className="radio-group dropdownWrapper",
)

header = html.Div(
    [title, dropdown_wrapper, download_btn, download_it, gas_btns], className="section-header"
)

graph_selectors = html.Div(
    [
        html.Div(
            [
                "Display: ",
                dcc.Dropdown(
                    id="selected-period-1",
                    options=["March","April", "May", "June", "July"],
                    className="dropdown",
                    value="April",
                ),
            ],
            className="graph-dropdown",
        ),
        daq.ToggleSwitch(
            id="toggle-comparison",
            label="Compare with APPA",
            color="#0d6efd",
            className="ml-auto toggle",
            value=True,
        ),
    ],
    className="d-flex flex-grow justify-content-between",
)

comparison_graph = html.Div(
    [
        dcc.Graph(
            id="comparison-graph",
            style=dict(height="50vh"),
            config={
                "displayModeBar": False,
                "displaylogo": False,
            },
            className="pretty_container",
        ),
        graph_selectors,
    ],
   
)

def period_to_interval(period):
    now = datetime.now() + timedelta(days=1)
    if period == "last hour":
        pass
    elif period == "last day":
        day = datetime.now() - timedelta(days=1)
    elif period == "last week":
        day = datetime.now() - timedelta(days=7)
    elif period == "last month":
        day = datetime.now() - timedelta(days=30)
    elif period == "last 6 months":
        day = datetime.now() - timedelta(days=180)
    
    return day.date(), now.date()

LAST_CLICKED = None

@callback(
    Output("comparison-graph", "figure"),
    State("my-date-picker-range", "start_date"),
    State("my-date-picker-range", "end_date"),
    Input("selected-station", "value"),
    Input("selected-fbk-pollutant", "value"),
    Input("toggle-comparison", "value"),
    Input("selected-period", "value"),
    Input("btn_search_date", "n_clicks"),
)
def update_comparison_graph(
    start_date : str,
    end_date : str,
    selected_station: str,
    selected_pollutant: str,
    toggle_comparison: str,
    selected_period: str,
    btn_search : int
) -> go.Figure:
    """
    Updates the graph representing the comparison between
    APPA data and model prediction

    Args:
        slected_station (str): station name
        selected_pollutant (str): pollutant name
        selected_period (str): H: hour; D: day; W: week; M: month; Y: year
        toggle_comparison (bool): wether to add a line of APPA"s data or not

    Returns:
        plotly.graph_objs.Figure: the graph
    """
    
    global LAST_CLICKED

    if (
        (
            "btn_search_date" == callback_context.triggered_id
            or 
            ("selected-fbk-pollutant" == callback_context.triggered_id and LAST_CLICKED == "btn_search_date")
        )
        and start_date
        and end_date
    ):
        LAST_CLICKED = "btn_search_date"
        start = start_date
        end= end_date
    else:
        LAST_CLICKED = "else"
        start, end = period_to_interval(selected_period)
    
    raw_data = get_data_day(start, end)    
    raw_data['ts'] = raw_data['ts'].apply(lambda x: x + timedelta(hours=2) if (x.month >= 4 and x.month <= 10) else x + timedelta(hours=1))
    test = raw_data.drop('ts',axis=1)
    
    y_pred=pipeline2.predict(test.values)
    
    #np.savetxt('data.csv', y_pred, delimiter=',')

    appa_data = load_data_from_psql(querys.q_custom_appa(start=start, end=end))
    
    fig = go.Figure()
    
    new_df = pd.DataFrame()
    new_df['ts'] = raw_data['ts'].copy()

    new_df['O3'] = y_pred[:,3].tolist()
    new_df['PM10'] = y_pred[:,0].tolist()
    new_df['NO2'] = y_pred[:,1].tolist()
    new_df['SO2'] = y_pred[:,2].tolist()
    
    
    new_df= new_df.set_index('ts').resample('1H').mean().reset_index()
    data = appa_data[(appa_data['stazione'] == 'Parco S. Chiara') & (appa_data['inquinante'] == selected_pollutant) & (['avg'])] 
    df = new_df.merge(data[['min','avg']], left_on='ts', right_on='min', how="left").drop('min',axis=1)
    
    #df.to_csv('export_dataframe.csv', header=True, )
    
    fig.add_trace(
        go.Scatter(
            x=df["ts"], y=df[selected_pollutant], mode="lines+markers", name="FBK", line=dict(color="red")
        )
    )

    title = "Pollutant concentration prediction"

    if toggle_comparison:
        # appa data graph
        fig.add_trace(
            go.Scatter(
                x=df["ts"],
                y=df['avg'],
                mode="lines+markers",
                name="APPA",
                line=dict(color="blue")
            )
        )

        title += " compared to APPA readings"

    fig.update_layout(
        margin=dict(l=5, r=5, t=20, b=0),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        title=dict(
            x=0.5,
            text=title,
            font_family="Sans serif",
            xanchor="center",
            yanchor="top",
        ),
        legend={
            "bgcolor": "rgba(0,0,0,0)",
        },
        modebar=dict(bgcolor="#ffffff")
    )
    fig.update_yaxes(title_text="Value", fixedrange=True)

    return fig


layout = html.Div(
    [header, 
     dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        id="comparison-graph",
                        config={
                            "displayModeBar": False,
                            "displaylogo": False,
                        },
                        style={
                            "height": "55vh",
                        },
                        className="pretty_container",
                    ),
                    style={"width": "80%"},
                ),
                dbc.Col(
                    [
                        toast,
                    ],
                    width=1,
                    style={"min-width": "200px"},
                ),
            ]
        ),
     
    ],
    className="section fullHeight",
    style={'height':'100vh'}
)

