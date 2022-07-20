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
from bokeh.models import Band, CheckboxButtonGroup, Button, ColumnDataSource, PreText, Select, CustomJS, Legend, LinearAxis, Range1d
from bokeh.plotting import figure
from bokeh.events import ButtonClick
import xarray as xr
import glob
import netCDF4
import time
# DATA_DIR = join(dirname(__file__), 'daily')

MONTHS = list(np.unique([s.split('_')[-1].split('.')[0] for s in glob.glob('data/2022.02.*_2019_*')]))
MONTHS.sort()
DEFAULT_TICKERS = list(xr.open_dataset('data/2022.02.cml_list.nc').cml_id.values)

# @lru_cache()
def get_data(cml_id, month):
    ds = xr.open_dataset('data/2022.02.'+cml_id+'_2019_'+month+'.nc').isel(channel_id=0).load()
    meta = str(np.round(ds.length.values, decimals=2))+' '+str(np.round(ds.frequency.values/1e9, decimals=2))
    data = ds.to_pandas()
    ds.close()
    data['date'] = data.index
    data = data.rename(columns={'txrx':'trsl1', 'rainfall_amount':'R'})
    ds2 = xr.open_dataset('data/2022.02.'+cml_id+'_2019_'+month+'.nc').isel(channel_id=1).txrx.load()
    df2 = ds2.to_pandas()
    ds2.close()
    trsl2 = df2.values.copy()
    data.loc[:,'trsl2'] = trsl2
    data = data.set_index('date')
    for i, label in enumerate(LABELS):
        val = data[label].values.copy()
        data.loc[:,label] = val*(i+1)/len(LABELS)
    return data, meta


# set up widgets

stats = PreText(text='', width=500)
ticker1 = Select(value=MONTHS[0], options=MONTHS)
ticker2 = Select(value=DEFAULT_TICKERS[0], options=DEFAULT_TICKERS)

button1 = Button(label="Save flags", button_type="success", height=25)
button2 = Button(label="Delete all flags", button_type="success", height=25)
button2a = Button(label="Delete selected type of flags", button_type="success", height=25)
button2b = Button(label="Delete flags in current selection", button_type="success", height=25)
button3 = Button(label="Flag period", button_type="success", height=25)
LABELS = ["Jump", "Dew", "Fluctuation", "Unknown anomaly"]

checkbox_button_group = CheckboxButtonGroup(labels=LABELS, active=[])
checkbox_button_group.js_on_click(CustomJS(code="""
    console.log('checkbox_button_group: active=' + this.active, this.toString())
"""))

def callback1(event):
    data = source.to_df()
    cml_id = ticker2.value
    month = ticker1.value
    with netCDF4.Dataset('data/2022.02.'+cml_id+'_2019_'+month+'.nc', 'a') as nc_fh:
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
button2b.on_event(ButtonClick, callback2b)
button3.on_event(ButtonClick, callback3)

# set up plots

source = ColumnDataSource(data=dict(date=[], t1=[], t2=[],))
source_static = ColumnDataSource(data=dict(date=[], t1=[], t2=[],))
tools = 'pan,wheel_zoom,xbox_select,reset,box_zoom'

ts1 = figure(width=1900, height=250, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts1.line('date', 'trsl1', legend_label="channel 1", source=source_static)
ts1.circle('date', 'trsl1', size=5, source=source, color=None, selection_color="green")
ts1.line('date', 'trsl2', legend_label="channel 2", source=source_static, color="gray")

ts2 = figure(width=1900, height=100, tools=tools, x_axis_type='datetime', active_drag="xbox_select", y_range=(0.1, 1.1))
colors = ['red','blue','pink','gray', 'orange', 'green', 'black']
for i, label in enumerate(LABELS):
    ts2.circle('date', label, size=7, source=source, legend_label=label, color=colors[i])
    band = Band(base='date', lower=0, upper=label, source=source, level='underlay',
            fill_alpha=1.0, line_width=1, line_color=colors[i])
    ts1.add_layout(band)
ts2.x_range = ts1.x_range
ts2.legend.orientation = "horizontal"
ts2.legend.location = "top_right"
ts2.legend.border_line_color = None
ts2.legend.background_fill_alpha = 0

ts3 = figure(width=1900, height=150, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts3.x_range = ts1.x_range
ts3.line('date', 'R', source=source_static, color='red', legend_label="R_CML")
ts3.line('date', 'RADOLAN_RW', source=source_static, color='blue', legend_label="RADOLAN-RW")
ts3.line('date', 'RADKLIM_YW', source=source_static, color='green', legend_label="RADKLIM-YW")
ts3.legend.location = "top_right"
ts3.legend.border_line_color = None
ts3.legend.background_fill_alpha = 0

ts4 = figure(width=1900, height=150, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts4.x_range = ts1.x_range
ts4.line('date', 'era5_t2m', source=source_static, legend_label="Surface temperature", color='red')
ts4.line('date', y=0, source=source_static, legend_label="Zero degrees", color='purple')
ts4.line('date', 'era5_d2m', source=source_static, legend_label="Dew point tempreature")
ts4.legend.location = "top_right"
ts4.legend.border_line_color = None
ts4.legend.background_fill_alpha = 0

ts5 = figure(width=1900, height=100, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts5.y_range = Range1d(0, 10)
# ts5.y_range = Range1d()
ts5.extra_y_ranges = {"foo": Range1d(start=0, end=900)}
# ts5.extra_y_ranges = {"foo": Range1d()}
ts5.add_layout(LinearAxis(y_range_name="foo"), 'right')
ts5.x_range = ts1.x_range
ts5.line('date', 'era5_wind_speed', source=source_static, legend_label="Wind speed")
ts5.line('date', 'era5_ssrd', source=source_static, y_range_name="foo", color='red', legend_label="Surface solar radiation")
ts5.legend.location = "top_right"
ts5.legend.border_line_color = None
ts5.legend.background_fill_alpha = 0

# set up callbacks

def ticker1_change(attrname, old, new):
    ticker2.options = DEFAULT_TICKERS
    update()
#     ts1.y_range = Range1d(np.nanmin([np.nanmin(pd.DataFrame(source.data)['trsl1'])-5, 
#                                      np.nanmin(pd.DataFrame(source.data)['trsl2'])-5,
#                                      50
#                                     ]), 
#                           np.nanmax([np.nanmax(pd.DataFrame(source.data)['trsl1'])+5, 
#                                      np.nanmax(pd.DataFrame(source.data)['trsl2'])+5,
#                                      70
#                                     ]))

def ticker2_change(attrname, old, new):
    ticker2.options = DEFAULT_TICKERS
    update()
#     ts1.y_range = Range1d(start = np.nanmin([np.nanmin(pd.DataFrame(source.data)['trsl1'])-5, 
#                                      np.nanmin(pd.DataFrame(source.data)['trsl2'])-5,
#                                      50
#                                     ]), 
#                           end = np.nanmax([np.nanmax(pd.DataFrame(source.data)['trsl1'])+5, 
#                                      np.nanmax(pd.DataFrame(source.data)['trsl2'])+5,
#                                      70
#                                     ]),
#                           reset_start = np.nanmin([np.nanmin(pd.DataFrame(source.data)['trsl1'])-5, 
#                                      np.nanmin(pd.DataFrame(source.data)['trsl2'])-5,
#                                      50
#                                     ]), 
#                           reset_end = np.nanmax([np.nanmax(pd.DataFrame(source.data)['trsl1'])+5, 
#                                      np.nanmax(pd.DataFrame(source.data)['trsl2'])+5,
#                                      70
#                                     ]),
#                          )

def update(selected=None):
    cml_id = ticker2.value
    month = ticker1.value
    data, meta = get_data(cml_id, month)
    source.data = data
    source_static.data = data
#     ts1.y_range.destroy()
    ts1.y_range.update(start=np.nanmin([np.nanmin(pd.DataFrame(source.data)['trsl1'])-2, 
                                     np.nanmin(pd.DataFrame(source.data)['trsl2'])-2,
                                     60
                                    ]), 
                          end=np.nanmax([np.nanmax(pd.DataFrame(source.data)['trsl1'])+2, 
                                     np.nanmax(pd.DataFrame(source.data)['trsl2'])+2,
                                     70
                                    ]))

    update_stats(data, meta, ['trsl1', 'trsl2', 'R'])

#     corr.title.text = 'TRSL channel 1 vs. Path averaged rainfall'
#     ts1.title.text, ts2.title.text, ts3.title.text = 'Transmitted minus received signal level [dB]', 'Anomaly flags', 'Path averaged CML rainfall [mm/h] after combined methods from Graf et al. 2020 and Polz et al. 2020'

def update_stats(data, meta, c_list):
#     print(data[c_list].describe().head(4))
    stats.text = str(data[c_list].describe().head(4))+'  Length: '+meta[0]+'km, Frequency: '+meta[1]+'GHz'

ticker1.on_change('value', ticker1_change)
ticker2.on_change('value', ticker2_change)

def selection_change(attrname, old, new):
    cml_id = ticker2.value
    month = ticker1.value
    _, meta = get_data(cml_id, month)
    data = source.to_df()
    selected = source.selected.indices
    if selected:
        data = data.iloc[selected, :]
    update_stats(data, meta, ['trsl1', 'trsl2', 'R'])

source.selected.on_change('indices', selection_change)

# set up layout
widgets = column(ticker1, ticker2)
buttons1 = column(button1, button3)
buttons2 = column(button2, button2a, button2b)
main_row = row(widgets, stats, buttons1, buttons2,)
series = column(ts1, ts2, ts3,
                ts4, 
                ts5, 
#                 ts6
               )
layout = column(main_row, checkbox_button_group, series)

# initialize
update()

curdoc().add_root(layout)
curdoc().title = "CML viewer"