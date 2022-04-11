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
from bokeh.models import Band, CheckboxButtonGroup, Button, ColumnDataSource, PreText, Select, CustomJS, Legend
from bokeh.plotting import figure
from bokeh.events import ButtonClick
import xarray as xr
import glob
import netCDF4

DATA_DIR = join(dirname(__file__), 'daily')

MONTHS = [s.split('_')[-1].split('.')[0] for s in glob.glob('/pd/data/CML/data/reference/anomaly_flags/2022.01.BY1412_2_BY1298_2_2019_*')]
MONTHS.sort()
DEFAULT_TICKERS = list(xr.open_dataset('/pd/data/CML/data/reference/anomaly_flags/2022.01.cml_list.nc').cml_id.values)

# @lru_cache()
def get_data(cml_id, month):
    ds = xr.open_dataset('/pd/data/CML/data/reference/anomaly_flags/2022.01.'+cml_id+'_2019_'+month+'.nc').isel(channel_id=0).load()
    data = ds.to_pandas()
    ds.close()
    data['date'] = data.index
    data = data.rename(columns={'txrx':'trsl1', 'rainfall_amount':'R'})
    ds2 = xr.open_dataset('/pd/data/CML/data/reference/anomaly_flags/2022.01.'+cml_id+'_2019_'+month+'.nc').isel(channel_id=1).txrx.load()
    df2 = ds2.to_pandas()
    ds2.close()
    trsl2 = df2.values.copy()
    data.loc[:,'trsl2'] = trsl2
    data = data.set_index('date')
    for i, label in enumerate(LABELS):
        val = data[label].values.copy()
        data.loc[:,label] = val*(i+1)/len(LABELS)
    return data


# set up widgets

stats = PreText(text='', width=500)
ticker1 = Select(value=MONTHS[0], options=MONTHS)
ticker2 = Select(value=DEFAULT_TICKERS[0], options=DEFAULT_TICKERS)

button1 = Button(label="Save flags", button_type="success")
button2 = Button(label="Delete all flags", button_type="success")
button2a = Button(label="Delete selected type of flags", button_type="success")
button2b = Button(label="Delete selected type of flags", button_type="success")
button3 = Button(label="Flag period", button_type="success")
LABELS = ["Dry", "Wet", "Anomaly", "Dew", "LOL"]

checkbox_button_group = CheckboxButtonGroup(labels=LABELS, active=[])
checkbox_button_group.js_on_click(CustomJS(code="""
    console.log('checkbox_button_group: active=' + this.active, this.toString())
"""))

def callback1(event):
    data = source.to_df()
    cml_id = ticker2.value
    month = ticker1.value
    with netCDF4.Dataset('/pd/data/CML/data/reference/anomaly_flags/2022.01.'+cml_id+'_2019_'+month+'.nc', 'a') as nc_fh:
        for label in LABELS:
            nc_fh[label][:] = (data[label]>0).astype(bool)
    print('saved')

def callback2(event):
    for label in LABELS:
        patches = {
            label : [ (slice(0,None), np.zeros_like(source.data[label])) ],
        }

        source.patch(patches)
        
def callback2a(event):
    ind = checkbox_button_group.to_json(True)['active']
    for i, label in enumerate(LABELS):
        if i in ind:
            patches = {
                label : [ (slice(0,None), np.zeros_like(source.data[label])) ],
            }
            source.patch(patches)
        
def callback2b(event):
    selected = source.selected.indices
    for i, label in enumerate(LABELS):
        patches = {
            label : [(s,0) for s in selected],
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
button2a.on_event(ButtonClick, callback2a)
button2a.on_event(ButtonClick, callback2b)
button3.on_event(ButtonClick, callback3)

# set up plots

source = ColumnDataSource(data=dict(date=[], t1=[], t2=[],))
source_static = ColumnDataSource(data=dict(date=[], t1=[], t2=[],))
tools = 'pan,wheel_zoom,xbox_select,reset,box_zoom'

corr = figure(width=250, height=250,
              tools='pan,box_zoom,box_select,reset')
corr.circle('trsl1', 'R', size=2, source=source,
            selection_color="orange", alpha=1, nonselection_alpha=1, selection_alpha=1)

ts1 = figure(width=1800, height=250, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts1.line('date', 'trsl1', legend_label="channel 1", source=source_static)
ts1.circle('date', 'trsl1', size=5, source=source, color=None, selection_color="green")
ts1.line('date', 'trsl2', legend_label="channel 2", source=source_static, color="gray")


ts2 = figure(width=1800, height=100, tools=tools, x_axis_type='datetime', active_drag="xbox_select", y_range=(0.1, 1.1))
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
ts2.legend.orientation = "horizontal"
ts2.legend.location = "top_right"
ts2.legend.border_line_color = None
ts2.legend.background_fill_alpha = 0

ts3 = figure(width=1800, height=250, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts3.x_range = ts1.x_range
ts3.line('date', 'R', source=source_static, color='red', legend_label="R_CML")
ts3.line('date', 'RADOLAN_RW', source=source_static, color='blue', legend_label="RADOLAN-RW")
ts3.line('date', 'RADKLIM_YW', source=source_static, color='green', legend_label="RADKLIM-YW")

ts4 = figure(width=1800, height=150, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts4.x_range = ts1.x_range
ts4.line('date', 'era5_t2m', source=source_static, legend_label="Surface temperature", color='red')
ts4.line('date', 'era5_d2m', source=source_static, legend_label="Dew point tempreature")

ts5 = figure(width=1800, height=100, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts5.x_range = ts1.x_range
ts5.line('date', 'era5_wind_speed', source=source_static)

ts6 = figure(width=1800, height=100, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts6.x_range = ts1.x_range
ts6.line('date', 'era5_ssrd', source=source_static)

# set up callbacks

def ticker1_change(attrname, old, new):
    ticker2.options = DEFAULT_TICKERS
    update()

def ticker2_change(attrname, old, new):
    ticker2.options = DEFAULT_TICKERS
    update()

def update(selected=None):
    cml_id = ticker2.value
    month = ticker1.value
    data = get_data(cml_id, month)
    source.data = data
    source_static.data = data

    update_stats(data, ['trsl1', 'trsl2', 'R'])

#     corr.title.text = 'TRSL channel 1 vs. Path averaged rainfall'
#     ts1.title.text, ts2.title.text, ts3.title.text = 'Transmitted minus received signal level [dB]', 'Anomaly flags', 'Path averaged CML rainfall [mm/h] after combined methods from Graf et al. 2020 and Polz et al. 2020'

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
widgets = column(ticker1, ticker2,button1, button3)
buttons2 = column(button2, button2a, button2b)
main_row = row(widgets, stats,buttons2, corr,)
series = column(ts1, ts2, ts3,
                ts4, 
                ts5, 
                ts6
               )
layout = column(main_row, checkbox_button_group, series)

# initialize
update()

curdoc().add_root(layout)
curdoc().title = "CML viewer"