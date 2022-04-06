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
from bokeh.models import Band, CheckboxButtonGroup, Button, ColumnDataSource, PreText, Select, CustomJS
from bokeh.plotting import figure
from bokeh.events import ButtonClick
import xarray as xr
import glob
import netCDF4

DATA_DIR = join(dirname(__file__), 'daily')

MONTHS = [s.split('/')[-1] for s in glob.glob('../data/raw*')]
MONTHS.sort()
DEFAULT_TICKERS = xr.open_dataset('../data/raw01.nc').cml_id.values
# print(DEFAULT_TICKERS)

def nix(val, lst):
#     return [x for x in lst if x != val]
    return [x for x in lst]

# @lru_cache()
def load_ticker(cml_id, month):
    data = xr.open_dataset('../data/'+month).sel(cml_id=cml_id).isel(channel_id=0).load()
    data = data.to_pandas()
    data['date'] = data.index
    data = data.rename(columns={'txrx':'trsl1', 'rainfall_amount':'R'})
    df2 = xr.open_dataset('../data/'+month).sel(cml_id=cml_id).isel(channel_id=1).txrx.to_pandas()
    data.loc[:,'trsl2'] = df2.values
    data = data.set_index('date')
    return data

# @lru_cache()
def get_data(cml_id, month):
    data = load_ticker(cml_id, month)
#     print(data.head())
    return data


# set up widgets

stats = PreText(text='', width=500)
ticker1 = Select(value='raw01.nc', options=nix('raw01.nc', MONTHS))
ticker2 = Select(value='BY0081_2_BY1150_2', options=nix('BY0081_2_BY1150_2', DEFAULT_TICKERS))

button1 = Button(label="Save CML flags", button_type="success")
button2 = Button(label="Delete CML flags", button_type="success")
button3 = Button(label="Flag period", button_type="success")
LABELS = ["Dry", "Wet", "Anomaly", "Dew", "LOL"]

checkbox_button_group = CheckboxButtonGroup(labels=LABELS, active=[])
checkbox_button_group.js_on_click(CustomJS(code="""
    console.log('checkbox_button_group: active=' + this.active, this.toString())
"""))

def callback1(event):
    data = source.to_df()
    print(data.head())

def callback2(event):
    for label in LABELS:
        patches = {
            label : [ (slice(0,None), np.zeros_like(source.data[label])) ],
        }

        source.patch(patches)

def callback3(event):
    selected = source.selected.indices
#     print(selected)
    ind = checkbox_button_group.to_json(True)['active']
    for i, label in enumerate(LABELS):
        if i in ind:
            patches = {
                label : [(s,(i+1)/len(LABELS)) for s in selected],
            }
            source.patch(patches)

button1.on_event(ButtonClick, callback1)
button2.on_event(ButtonClick, callback2)
button3.on_event(ButtonClick, callback3)

# set up plots

source = ColumnDataSource(data=dict(date=[], t1=[], t2=[],))
source_static = ColumnDataSource(data=dict(date=[], t1=[], t2=[],))
tools = 'pan,wheel_zoom,xbox_select,reset,box_zoom'

# corr = figure(width=250, height=250,
#               tools='pan,box_zoom,box_select,reset')
# corr.circle('trsl1', 'R', size=2, source=source,
#             selection_color="orange", alpha=1, nonselection_alpha=1, selection_alpha=1)

ts1 = figure(width=1800, height=250, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts1.line('date', 'trsl1', legend_label="channel 1", source=source_static)
ts1.circle('date', 'trsl1', size=5, source=source, color=None, selection_color="green")
ts1.line('date', 'trsl2', legend_label="channel 2", source=source_static, color="gray")
ts1.circle('date', 'trsl2', size=2, source=source, color=None, selection_color="green")


ts2 = figure(width=1800, height=200, tools=tools, x_axis_type='datetime', active_drag="xbox_select", y_range=(0.1, 1.1))
colors = ['red','blue','pink','gray', 'orange']
for i, label in enumerate(LABELS):
#     ts2.line('date', y=source.data[label]*i/len(LABELS), legend_label=label, color=colors[i], source=source, line_width=10)
#     print(source.data[label])
#     ts2.circle('date', y=source.data[label]*i/len(LABELS), size=10, source=source, color=colors[i], selection_color="green")
    ts2.circle('date', label, size=10, source=source, legend_label=label, color=colors[i])
    band = Band(base='date', lower=0, upper=label, source=source, level='underlay',
            fill_alpha=1.0, line_width=1, line_color=colors[i])
    ts1.add_layout(band)
ts2.x_range = ts1.x_range

ts3 = figure(width=1800, height=150, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts3.x_range = ts1.x_range
ts3.line('date', 'R', source=source_static)
ts3.circle('date', 'R', size=2, source=source, color=None, selection_color="green")

# set up callbacks

def ticker1_change(attrname, old, new):
    ticker2.options = nix(new, DEFAULT_TICKERS)
    update()

def ticker2_change(attrname, old, new):
    ticker2.options = nix(new, DEFAULT_TICKERS)
    update()

def update(selected=None):
    cml_id = ticker2.value
    month = ticker1.value
    data = get_data(cml_id, month)
    source.data = data
    source_static.data = data

    update_stats(data, ['trsl1', 'trsl2', 'R'])

#     corr.title.text = 'TRSL channel 1 vs. Path averaged radar rainfall'
    ts1.title.text, ts2.title.text, ts3.title.text = 'TRSL channel 1', 'Anomaly', 'Path averaged radar rainfall'

def update_stats(data, c_list):
    stats.text = str(data[c_list].describe())

ticker1.on_change('value', ticker1_change)
ticker2.on_change('value', ticker2_change)

def selection_change(attrname, old, new):
#     cml_id = ticker2.value
#     month = ticker1.value
#     data = get_data(cml_id, month)
    data = source.to_df()
    selected = source.selected.indices
    if selected:
        data = data.iloc[selected, :]
    update_stats(data, ['trsl1', 'trsl2', 'R'])

source.selected.on_change('indices', selection_change)

# set up layout
widgets = column(ticker1, ticker2, button1, button2)
main_row = row(widgets, 
               stats, 
#                corr,
              )
series = column(ts1, ts2, ts3)
layout = column(main_row, button3, checkbox_button_group, series)

# initialize
update()

curdoc().add_root(layout)
curdoc().title = "CML viewer"