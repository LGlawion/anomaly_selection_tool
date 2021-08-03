import xarray as xr
import numpy as np
from netCDF4 import Dataset
import matplotlib.pyplot as plt
from functools import wraps
from ipywidgets import Button, VBox, HBox, interact, widgets
from datetime import datetime
import matplotlib.widgets as mwidgets 
import random



def ast_tool(ds, ast,rado, cml_id_shuf, ast_proc_shuf):

    #%matplotlib widget

    selected_area = []

    cml_list = []
    cml_id = list(cml_id_shuf)
    previous_list = []

    data_start = str(ds.time.values[0])
    data_end = str(ds.time.values[-1])

    buttons = ['next', 'periodical_mode', 'correct_periodical', 'flux_above_base', 'correct_flux_ab', 'flux_below_base', 'correct_flux_below', 'step', 'correct_step', 'previous']

    items = [Button(description=w, height = 200, width = 2000) for w in buttons]

    first_box = VBox([items[0], items[9]])
    sec_box = VBox([items[1], items[2]])
    tir_box = VBox([items[3], items[4]])
    fou_box = VBox([items[5], items[6]])
    fit_box = VBox([items[7], items[8]])


    display(HBox([first_box, sec_box,tir_box, fou_box, fit_box]))
    
    
    Leftclick = leftclick()
    rb = RunButton(Leftclick)





    @yield_for_change(items[0])
    def f():
        fig,ax = plt.subplots(2,1, figsize=(15,8), sharex=True)
        ax[0].set_xlabel('Date')
        ax[0].set_ylabel('TRSL [dB]')
        ax[0].tick_params(axis='both', which='major', labelsize=8)
        plt.subplots_adjust(hspace=0.3)
        
        

        index = 0
        while index <= len(cml_id):
            
            

            if np.isnan(ast_proc_shuf[index]) == False:
                print('cml anomaly processed')
                continue
                
            if rb.previous == True:
                index = index-2

            out=widgets.Output()
            rb.previous = False

            cml = cml_id_shuf[index]


            if index > 0:
                fill_between_col.remove()
                #plt.cla()


            id_loc = np.where(ast.variables['cml_id'][:] == cml)[0][0]
            cml_list.append(id_loc)

            data_txrx = np.array(ast.variables['txrx'][0,id_loc,][:])
            data_rado = rado.sel(cml_id = cml).values


            fill_between_col = pltsin(ax,fig, data_txrx, data_rado, ds) 

            plt.setp(ax[0].get_xticklabels(), rotation=20, horizontalalignment='center')

            span = mwidgets.SpanSelector(ax[0], Leftclick, 'horizontal', button=1, useblit=True) 
            
            
            plt.show()
            
            rb.ast = ast
            rb.cml_list = cml_list
  

            with out:
                clear_output(wait=True)
 
 
            x = yield


            index += 1


            data_ok = np.where((np.array(ast.variables['periodical_mode'][0,id_loc,:]) == 0) & 
                               (np.array(ast.variables['flux_above_base'][0,id_loc,:]) == 0) & 
                               (np.array(ast.variables['flux_below_base'][0,id_loc,:]) == 0) &
                               (np.array(ast.variables['step'][0,id_loc,:]) == 0)
                               )[0]
            if len(data_ok) > 0:
                ast.variables['OK'][0,id_loc,data_ok] = 1

            ast.variables['ast_processed'][id_loc] = datetime.now().timestamp()
            
            span.active=False  # !!!! spanselector is not suited for loops

    f()


    items[1].on_click(rb.periodical_mode)
    items[2].on_click(rb.correct_periodical)
    items[3].on_click(rb.flux_above_base)
    items[4].on_click(rb.correct_flux_above)
    items[5].on_click(rb.flux_below_base)
    items[6].on_click(rb.correct_flux_below)
    items[7].on_click(rb.step)
    items[8].on_click(rb.correct_step)
    items[9].on_click(rb.previous_button)

    return None


# Loop interruption
def yield_for_change(widget):
    def f(iterator):
        @wraps(iterator)
        def inner():
            i = iterator()
            def next_i(change):
                try:
                    i.send(change)
                except StopIteration as e:
                    widget.unobserve(next_i, attribute)
            widget.on_click(next_i)
            # start the generator
            next(i) 
        return inner
    return f



class RunButton(Button):

    def __init__(self,Leftclick, *args, **kwargs):

        self.variable = "Foo" #instance attribute.
        
        super(RunButton, self).__init__(*args, **kwargs)
        self.process = "process"
        
        self.ast = 'ast'
        self.cml_list = 'cml_list'
        self.Leftclick = Leftclick
        self.previous = False

    def periodical_mode(self, arg1):
        
        self.ast.variables['periodical_mode'][0,self.cml_list[-1],self.Leftclick.coords['x']:self.Leftclick.coords['y']] = 1
        plt.plot(np.arange(self.Leftclick.coords['x'], self.Leftclick.coords['y']), 
             np.array([0]*(self.Leftclick.coords['y']-self.Leftclick.coords['x'])), 
             color='seagreen', 
             linewidth=7, 
             alpha=0.6)
        
    def flux_above_base(self, arg1):
    
        self.ast.variables['flux_above_base'][0,self.cml_list[-1],self.Leftclick.coords['x']:self.Leftclick.coords['y']] = 1
        plt.plot(np.arange(self.Leftclick.coords['x'], self.Leftclick.coords['y']),
             np.array([1]*(self.Leftclick.coords['y']-self.Leftclick.coords['x'])), 
             color='seagreen', 
             linewidth=7, 
             alpha=0.6)
        
    def flux_below_base(self, arg1):
    
        self.ast.variables['flux_below_base'][0,self.cml_list[-1],self.Leftclick.coords['x']:self.Leftclick.coords['y']] = 1
        plt.plot(np.arange(self.Leftclick.coords['x'], self.Leftclick.coords['y']),
             np.array([2]*(self.Leftclick.coords['y']-self.Leftclick.coords['x'])), 
             color='seagreen', 
             linewidth=7, 
             alpha=0.6)
        
        
    def step(self,arg1):

        self.ast.variables['step'][0,self.cml_list[-1],self.Leftclick.coords['x']:self.Leftclick.coords['y']] = 1
        plt.plot(np.arange(self.Leftclick.coords['x'], self.Leftclick.coords['y']),
             np.array([3]*(self.Leftclick.coords['y']-self.Leftclick.coords['x'])), 
             color='seagreen', 
             linewidth=7, 
             alpha=0.6)
        
    def correct_periodical(self,arg1):
    
        self.ast.variables['periodical_mode'][0,self.cml_list[-1],:] = 0

        plt.plot(np.arange(0, self.ast.variables['txrx'].shape[2]), 
                    np.array([0]*(self.ast.variables['txrx'].shape[2])), 
                    color='white', 
                    linewidth=8)
        
        
    def correct_flux_above(self,arg1):
    
        self.ast.variables['flux_above_base'][0,self.cml_list[-1],:] = 0

        plt.plot(np.arange(0, self.ast.variables['txrx'].shape[2]), 
                    np.array([1]*(self.ast.variables['txrx'].shape[2])), 
                    color='white', 
                    linewidth=8)
        
        
    def correct_flux_below(self,arg1):
    
        self.ast.variables['flux_below_base'][0,self.cml_list[-1],:] = 0
    
        plt.plot(np.arange(0, self.ast.variables['txrx'].shape[2]), 
                np.array([2]*(self.ast.variables['txrx'].shape[2])), 
                color='white', 
                linewidth=8)
    
    
    def correct_step(self,arg1):
    
        self.ast.variables['step'][0,self.cml_list[-1],:] = 0
    
        plt.plot(np.arange(0, self.ast.variables['txrx'].shape[2]), 
                np.array([3]*(self.ast.variables['txrx'].shape[2])), 
                color='white', 
                linewidth=8)

        
    def previous_button(self, arg1):
        self.previous = True
        
        
        

class leftclick():

    def __init__(self):
        self.coords = {}

    def __call__(self, start, end):
        if start < 0:
            start = 0
            
        self.coords['x'] = int(start)
        self.coords['y'] = int(end)
       
        selected_area.append((int(start), int(end)))




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

'''
# Buttons and selections
def periodical_mode(b):
    
    ast.variables['periodical_mode'][0,cml_list[-1],selected_area[-1][0]:selected_area[-1][1]] = 1
    plt.plot(np.arange(selected_area[-1][0], selected_area[-1][1]), 
             np.array([0]*(selected_area[-1][1]-selected_area[-1][0])), 
             color='seagreen', 
             linewidth=7, 
             alpha=0.6)
    # better for correction
    #plt.plot(np.where(ast.variables['periodical_mode'][0,cml_list[-1]] == 1)[0], 
    #         np.array([0]*len(np.where(ast.variables['periodical_mode'][0,cml_list[-1]] == 1)[0])), 
    #         color='seagreen', 
    #         linewidth=7, 
    #         alpha=0.6)


def flux_above_base(b):
    
    ast.variables['flux_above_base'][0,cml_list[-1],selected_area[-1][0]:selected_area[-1][1]] = 1
    plt.plot(np.arange(selected_area[-1][0], selected_area[-1][1]), 
             np.array([1]*(selected_area[-1][1]-selected_area[-1][0])), 
             color='seagreen', 
             linewidth=7, 
             alpha=0.6)
    
    
def flux_below_base(b):
    
    ast.variables['flux_below_base'][0,cml_list[-1],selected_area[-1][0]:selected_area[-1][1]] = 1
    plt.plot(np.arange(selected_area[-1][0], selected_area[-1][1]), 
             np.array([2]*(selected_area[-1][1]-selected_area[-1][0])), 
             color='seagreen', 
             linewidth=7, 
             alpha=0.6)
    
    
  
def step(b):
    
    ast.variables['step'][0,cml_list[-1],selected_area[-1][0]:selected_area[-1][1]] = 1
    plt.plot(np.arange(selected_area[-1][0], selected_area[-1][1]), 
             np.array([3]*(selected_area[-1][1]-selected_area[-1][0])), 
             color='seagreen',
             linewidth=7, 
             alpha=0.6)
    
    
def correct_periodical(b):
    
    ast.variables['periodical_mode'][0,cml_list[-1],:] = 0
    
    plt.plot(np.arange(0, ast.variables['txrx'].shape[2]), 
                np.array([0]*(ast.variables['txrx'].shape[2])), 
                color='white', 
                linewidth=8)
    
def correct_flux_above(b):
    
    ast.variables['flux_above_base'][0,cml_list[-1],:] = 0
    
    plt.plot(np.arange(0, ast.variables['txrx'].shape[2]), 
                np.array([1]*(ast.variables['txrx'].shape[2])), 
                color='white', 
                linewidth=8)
    
   
def correct_flux_below(b):
    
    ast.variables['flux_below_base'][0,cml_list[-1],:] = 0
    
    plt.plot(np.arange(0, ast.variables['txrx'].shape[2]), 
                np.array([2]*(ast.variables['txrx'].shape[2])), 
                color='white', 
                linewidth=8)
    
    
def correct_step(b):
    
    ast.variables['step'][0,cml_list[-1],:] = 0
    
    plt.plot(np.arange(0, ast.variables['txrx'].shape[2]), 
                np.array([3]*(ast.variables['txrx'].shape[2])), 
                color='white', 
                linewidth=8)
 
    
def previous(b):
    previous_list.append(True)
    
    
def leftclick(start, end):
    
    if start < 0:
        start = 0
       
    selected_area.append((int(start), int(end)))

    
    
'''   
