duration_name = 'duration'
interval_name = 'interval'


def parse_duration_level(f):
    """parse duration level from filename f"""
    from pathlib import Path
    stem = Path(f).stem
    return stem.split('_')[2]

def kog(f):
    """parse KOG from filename f"""
    from pathlib import Path
    stem = Path(f).stem
    try:
        return stem.split('_')[3] == "KOG"
    except:
        return False
    
def create_table(f):
    """read table and add meta data
    
    reads a single tables, adds duration level from filename
    and grid info from geoinfo table.
    
    """
    df = pd.read_csv(f, delimiter=";", index_col='INDEX_RC')
    df[duration_name] = parse_duration_level(f)
    df = df.join(geoinfo[['X_CENT_GEO', 'Y_CENT_GEO', 'Col', 'Row']])
    df = df.rename(columns={"Col":"x", "Row": "y", "X_CENT_GEO": "lon", "Y_CENT_GEO": "lat"})
    return df

def to_xarray(df):
    ds = df.set_index([duration_name, 'y', 'x']).to_xarray() # convert to gridded data
    ds = ds.where(ds != -99.9) # set nans
    ds = ds.assign_coords(lon=ds.lon.squeeze(drop=True), lat=ds.lat.squeeze(drop=True))#.drop(('x', 'y'))
    ds[duration_name] = [int(i[1:]) for i in ds[duration_name].values]
    ds[duration_name].attrs['units'] = 'minutes'
    return ds


def derive_varname(varname):
    if "KOG" in varname:
        return "HN_KOG"
    return "HN"


def interval_coord(ds, numeric=True):
    interval = xr.DataArray([i[-4:] for i in list(ds.data_vars)], dims=interval_name)
    if numeric is True:
        interval[:] = [int(i[:-1]) for i in interval.values]
    interval.attrs['units'] = 'years'
    return interval

def duration_level(ds, numeric=True):
    return


def add_coords(ds):
    """merge intervals into coordinate"""
    ds = ds.copy()
    data_vars = list(ds.data_vars)
    varname = derive_varname(data_vars[0])
    ds[varname] = xr.concat([ds[var] for var in ds.data_vars], dim=interval_coord(ds))
    ds = ds.drop_vars(data_vars)
    ds[varname].attrs={'long_name': 'Bemessungsniederschlagswert', 'units': 'mm'}
    return ds.transpose(duration_name, interval_name, 'y', 'x')

def combine(dsets):
    HN_KOG = xr.concat([ds for ds in dsets if "HN_KOG" in ds], dim=duration_name)
    HN = xr.concat([ds for ds in dsets if "HN" in ds], dim=duration_name)
    #return HN.sortby(HN.duration_level), HN_KOG.sortby(HN_KOG.duration_level)
    return xr.merge([HN, HN_KOG]).sortby(HN[duration_name])