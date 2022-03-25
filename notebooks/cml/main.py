''' 
CML viewer based on 
https://github.com/bokeh/bokeh/blob/master/examples/app/stocks
https://github.com/bokeh/bokeh/tree/branch-3.0/examples/app/export_csv

Use the ``bokeh serve`` command to run the example by executing:
    bokeh serve cml
at your command prompt. Then navigate to the URL
    http://localhost:5006/cml

On a remote server "B" (e.g. HPC) use
    bokeh serve --allow-websocket-origin=localhost:XXXX stocks
and ssh port forwarding to redirect localhost:5006 to to your localhost:XXXX, i.e. 
    ssh -L XXXX:localhost:5006 user@B
'''
from functools import lru_cache
from os.path import dirname, join

import pandas as pd
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import CheckboxButtonGroup, Button, ColumnDataSource, PreText, Select, CustomJS
from bokeh.plotting import figure
import xarray as xr

DATA_DIR = join(dirname(__file__), 'daily')

DEFAULT_TICKERS = xr.open_dataset('../data/ast_example_cml_raw.nc').cml_id.values
# print(DEFAULT_TICKERS)

def nix(val, lst):
    return [x for x in lst if x != val]
#     return [x for x in lst]

@lru_cache()
def load_ticker(cml_id, channel_id):
    data = xr.open_dataset('../data/ast_example_cml_raw.nc').sel(cml_id=cml_id).isel(channel_id=channel_id).to_pandas()
    data['date'] = data.index
    data = data.set_index('date')
    return data

@lru_cache()
def get_data(cml_id):
    df1 = load_ticker(cml_id, 0)
    df2 = load_ticker(cml_id, 1)
    data=pd.DataFrame()
    data['t1'] = df1.txrx
    data['t2'] = df2.txrx
    data['R'] = df1.R
# ... append more variables if you like
#     print(data.head())
    return data

# set up widgets

stats = PreText(text='', width=500)
# ticker1 = Select(value='1', options=nix('R', DEFAULT_TICKERS))
ticker2 = Select(value='example_1', options=nix('example_1', DEFAULT_TICKERS))

button1 = Button(label="Save CML flags", button_type="success")
button2 = Button(label="Delete CML flags", button_type="success")
LABELS = ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5"]

checkbox_button_group = CheckboxButtonGroup(labels=LABELS, active=[0, 1])
checkbox_button_group.js_on_click(CustomJS(code="""
    console.log('checkbox_button_group: active=' + this.active, this.toString())
"""))

# set up plots

source = ColumnDataSource(data=dict(date=[], t1=[], t2=[],))
source_static = ColumnDataSource(data=dict(date=[], t1=[], t2=[],))
tools = 'pan,wheel_zoom,xbox_select,reset'

corr = figure(width=250, height=250,
              tools='pan,wheel_zoom,box_select,reset')
corr.circle('t1', 'R', size=2, source=source,
            selection_color="orange", alpha=1, nonselection_alpha=1, selection_alpha=1)

ts1 = figure(width=1800, height=250, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts1.line('date', 't1', source=source_static)
ts1.circle('date', 't1', size=1, source=source, color=None, selection_color="orange")
ts1.line('date', 't2', source=source_static, color="gray")
ts1.circle('date', 't2', size=1, source=source, color=None, selection_color="orange")

ts2 = figure(width=1800, height=150, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts2.x_range = ts1.x_range

ts3 = figure(width=1800, height=150, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts3.x_range = ts1.x_range
ts3.line('date', 'R', source=source_static)
ts3.circle('date', 'R', size=1, source=source, color=None, selection_color="orange")

# set up callbacks

# def ticker1_change(attrname, old, new):
#     ticker2.options = nix(new, DEFAULT_TICKERS)
#     update()

def ticker2_change(attrname, old, new):
    ticker2.options = nix(new, DEFAULT_TICKERS)
    update()

def update(selected=None):
    t2 = ticker2.value

    df = get_data(t2)
    data = df[['t1', 't2', 'R']]
    source.data = data
    source_static.data = data

    update_stats(df, ['t1', 't2', 'R'])

    corr.title.text = 'TRSL channel 1 vs. Path averaged radar rainfall'
    ts1.title.text, ts2.title.text, ts3.title.text = 'TRSL channel 1', 'TRSL channel 2', 'Path averaged radar rainfall'

def update_stats(data, c_list):
    stats.text = str(data[c_list].describe())

# ticker1.on_change('value', ticker1_change)
ticker2.on_change('value', ticker2_change)

def selection_change(attrname, old, new):
    t2 = ticker2.value
    data = get_data(t2)
    selected = source.selected.indices
    if selected:
        data = data.iloc[selected, :]
    update_stats(data, ['t1', 't2', 'R'])

source.selected.on_change('indices', selection_change)

# set up layout
widgets = column(ticker2, button1, button2)
main_row = row(widgets, stats, corr)
series = column(ts1, ts2, ts3)
layout = column(main_row, checkbox_button_group, series)

# initialize
update()

curdoc().add_root(layout)
curdoc().title = "CML viewer"