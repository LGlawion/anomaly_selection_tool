import xarray as xr
import numpy as np
from netCDF4 import Dataset
import matplotlib.pyplot as plt



# Plot anomaly Selection tool
def pltsin(ax,fig, data, rado, ds):
    
 
    x_tick = np.arange(0, len(data), 5000)
    #x_tick_label = [str(ds.values[i])[0:13] for i in x_tick]
    x_tick_label = np.datetime_as_string(ds.values[x_tick], unit='h')
    x = range(0, len(data))
    y_mid = np.nanmean(data)
    
    if ax[0].lines: # if axes exist create overwriting new ones

        for line in ax[0].lines:
            line.set_xdata(x)
            y1 = data
            line.set_ydata(y1) 
    else:
        
        y1 = data
        
    if ax[1].lines: # if axes exist create overwriting new ones

        for line in ax[1].lines:
            line.set_xdata(x)
            y1 = data
            line.set_ydata(y1)  

    if np.isnan(y_mid) != True:
        
        ax[0].set_ylim(y_mid-5,y_mid+12)
        
    p1 = ax[0].plot(x, y1, color='steelblue')
    
    fill_between_col = ax[0].fill_between(x, y_mid-5, y_mid+12, where=rado>0.1, step='mid', color='orange', alpha=0.5)
    
    ax[0].set_xticks(x_tick)
    ax[0].set_xticklabels(x_tick_label)
    ax[0].legend([p1[0], fill_between_col],["dry", "wet"], loc=1)
    
    
    ax[1].set_xlim(x[0], x[-1])
    ax[1].set_ylim(-0.5,3.5)
    ax[1].xaxis.tick_top()
    #ax[1].set_xticklabels([])
    ax[1].set_yticks(range(0,4))
    ax[1].set_yticklabels(['periodical_mode', 'flux_above', 'flux_below', 'step'])
    
    
    fig.canvas.draw()
    
    return fill_between_col





def load_data(in_file, out_file, rado_file):
    
    """open CML file for anomaly selection. If an
    
    Parameters
    ----------
    in_file : string
    path for the raw .nc file containing cmls and a txrx variable
    
    out_file : string
    copy of in_file for saving the anomaly information
    
    rado_file : string
    path for the .nc file containing the radolan reference
    
    Returns
    -------
    
    Note
    ----      
    
    """
    
    assert in_file!=out_file, 'in_file=out_file. You were about to save to the raw data file!'
        
    try:
        ds_ast = xr.open_dataset(out_file)
        ds_ast.close()

    except IOError:

        ds_ast = xr.open_dataset(in_file)

        #ds_ast['ast_processed'] = ('cml_id'), np.zeros_like(ds_ast.cml_id.values, dtype=bool)
        ds_ast['ast_processed'] = ('cml_id'), np.full_like(ds_ast.cml_id.values, np.datetime64("NaT"))
        ds_ast['periodical_mode'] = ('channel_id', 'cml_id', 'time'), np.zeros_like(ds_ast.txrx.values, dtype=bool)
        ds_ast['flux_above_base'] = ('channel_id', 'cml_id', 'time'), np.zeros_like(ds_ast.txrx.values, dtype=bool)
        ds_ast['flux_below_base'] = ('channel_id', 'cml_id', 'time'), np.zeros_like(ds_ast.txrx.values, dtype=bool)
        ds_ast['step'] = ('channel_id', 'cml_id', 'time'), np.zeros_like(ds_ast.txrx.values, dtype=bool)
        ds_ast['OK'] = ('channel_id', 'cml_id', 'time'), np.zeros_like(ds_ast.txrx.values, dtype=bool)

        ds_ast.to_netcdf(out_file)
    
    ast_file = out_file
    ast = Dataset(ast_file,'r+',format="NETCDF4")
    
    ds = xr.open_dataset(in_file)
    ds = ds.time
    ds.load()
    t_min = np.min(ds.values)
    t_max = np.max(ds.values)
    
    rado = xr.open_dataset(rado_file)
    rado = rado.sel(time=slice(t_min,t_max))
    rado.load()
    
    rado = rado.reindex({'time': ds}, method = 'backfill', copy=False).rainfall_amount
    
    return ast, ds, rado