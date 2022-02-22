import os
import glob
from pathlib import Path

import pandas as pd
import xarray as xr


__version__ = "0.1.0"


duration_name = "duration"
interval_name = "interval"

geoinfo = pd.read_excel(
    "./raw/KOSTRA-DWD-2010R_geog_Bezug.xlsx",
    sheet_name="Raster_geog_Bezug",
    index_col="index_rc",
)


def parse_duration_level(f):
    """parse duration level from filename f"""
    stem = Path(f).stem
    return stem.split("_")[2]


def kog(f):
    """parse KOG from filename f"""
    stem = Path(f).stem
    try:
        return stem.split("_")[3] == "KOG"
    except:
        return False


def create_table(f):
    """read table and add meta data

    reads a single tables, adds duration level from filename
    and grid info from geoinfo table.

    """
    bounds_cols = ['X1_NW_GEO', 'Y1_NW_GEO', 'X2_SW_GEO', 'Y2_SW_GEO', 
                   'X3_SE_GEO', 'Y3_SE_GEO', 'X4_NE_GEO', 'Y4_NE_GEO']
    df = pd.read_csv(f, delimiter=";", index_col="INDEX_RC")
    df[duration_name] = parse_duration_level(f)
    df = df.join(geoinfo[["X_CENT_GEO", "Y_CENT_GEO", "Col", "Row"]])
    df = df.join(geoinfo[bounds_cols])
    df = df.rename(
        columns={"Col": "x", "Row": "y", "X_CENT_GEO": "lon", "Y_CENT_GEO": "lat"}
    )
    return df


def add_coord_attrs(ds):
    ds = ds.copy()
    ds["lon"].attrs["long_name"] = "longitude"
    ds["lon"].attrs["units"] = "degrees_east"
    ds["lat"].attrs["long_name"] = "latitude"
    ds["lat"].attrs["units"] = "degrees_north"
    return ds


def to_xarray(df):
    ds = df.set_index([duration_name, "y", "x"]).to_xarray()  # convert to gridded data
    ds = ds.where(ds != -99.9)  # set nans
    ds = ds.assign_coords(
        lon=ds.lon.squeeze(drop=True), lat=ds.lat.squeeze(drop=True)
    )  # .drop(('x', 'y'))
    ds[duration_name] = [int(i[1:]) for i in ds[duration_name].values]
    ds[duration_name].attrs["units"] = "minutes"
    ds = add_coord_attrs(ds)
    return ds


def derive_varname(varname):
    if "KOG" in varname:
        return "HN_KOG"
    elif "HN" in varname:
        return "HN"
    else:
        return None


def interval_coord(data_vars):
    interval = xr.DataArray(
        [int(i[-4:-1]) for i in list(data_vars)], dims=interval_name
    )
    interval.attrs["units"] = "years"
    return interval


def duration_level(ds, numeric=True):
    return


def add_coords(ds):
    """merge intervals into coordinate"""
    ds = ds.copy()
    data_vars = [v for v in ds.data_vars if derive_varname(v) is not None]
    varname = derive_varname(data_vars[0])
    ds[varname] = xr.concat([ds[var] for var in data_vars], dim=interval_coord(data_vars))
    ds = ds.drop_vars(data_vars)
    ds[varname].attrs = {"long_name": "Bemessungsniederschlagswert", "units": "mm"}
    return ds.transpose(duration_name, interval_name, "y", "x")


def combine(dsets):
    HN_KOG = xr.concat([ds for ds in dsets if "HN_KOG" in ds], dim=duration_name)
    HN = xr.concat([ds for ds in dsets if "HN" in ds], dim=duration_name)
    # return HN.sortby(HN.duration_level), HN_KOG.sortby(HN_KOG.duration_level)
    return xr.merge([HN, HN_KOG]).sortby(HN[duration_name])


def unzip(f, targetdir):
    """unzip file f to targetdir"""
    import zipfile

    with zipfile.ZipFile(f, "r") as zip_ref:
        zip_ref.extractall(targetdir)


def get_csv_files(raw_dir="./raw", unzip_dir="./unzip"):
    url = os.path.join(raw_dir, "*.zip")
    zip_files = glob.glob(url)
    for f in zip_files:
        unzip(f, unzip_dir)
    return glob.glob(os.path.join(unzip_dir, "*.csv"))


def kostra_to_dataset(csv_files=None, path="raw"):
    if csv_files is None:
        csv_files = get_csv_files(path)
    tables = [create_table(f) for f in csv_files]
    dsets = [to_xarray(df) for df in tables]
    dsets = [add_coords(ds) for ds in dsets]
    return encode(combine(dsets))


def encode(ds):
    """encode meta data for netcdf"""
    for var in ds.data_vars.values():
        var.encoding["_FillValue"] = 1.0e20
        var.encoding["coordinates"] = "lon lat"
    for coord in ds.coords.values():
        coord.encoding["_FillValue"] = None
    return ds
