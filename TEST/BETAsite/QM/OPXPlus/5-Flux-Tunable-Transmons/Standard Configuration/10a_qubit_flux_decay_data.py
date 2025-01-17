
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from configuration import save_dir

def plot_sub( x, y, data, ax=None ):
    """
    data shape ( 2, N, M )
    2 is I,Q
    N is fluxes
    M is freq
    """
    idata = data[0]
    qdata = data[1]
    zdata = idata +1j*qdata
    print(x.shape, y.shape, zdata.shape)
    if ax==None:
        fig, ax = plt.subplots()
        ax.set_title('pcolormesh')
        fig.show()
    ax.pcolormesh( x, y, np.abs(zdata), cmap='RdBu')# , vmin=z_min, vmax=z_max)


dataset = xr.open_dataset(save_dir/"qb_flux_decay_dr2a_q5_(2Xpi).nc")

# Plot
dfs = dataset.coords["frequency"].values
time = dataset.coords["time"].values
for ro_name, data in dataset.data_vars.items():
    fig, ax = plt.subplots()
    plot_sub( time, dfs, data.values, ax )
    ax.set_title(ro_name)
    ax.set_xlabel("time (ns)")
    ax.set_ylabel("additional IF freq (MHz)")
plt.show()

