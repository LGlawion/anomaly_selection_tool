import xarray as xr
import numpy as np
from netCDF4 import Dataset


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