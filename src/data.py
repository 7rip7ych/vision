"""
Handle and analyze data
"""
import pandas as pd
from io import StringIO
def view_data():
    """ view data with colors n such """
    

def draw():
    """Draw graph"""

def filter_data(data, filter):
    """ filter data """

def create_visual():
    """Create visual representation of system and data"""

def get_info(df):
    """Get general info about data"""
    buffer = StringIO()
    df.info(buf=buffer)
    info = buffer.getvalue()
    return info

def get_mem_info(df):
    """Get memory usage info about data"""
    mem = df.memory_usage()
    return mem.to_frame()

def get_unique_values(df, exceptions=[]):
    """d"""
    cols = df.columns.to_list()
    res = {}
    headers = [col for col in cols if col not in exceptions]
    for col in headers:
        data = df[col].value_counts()
        frame = data.to_frame().reset_index()
        res[col] = frame

    return res

def sort_dict_by_val(dictionary):
    """sorts dictionary by values"""
    lst = []
    lst2 = []
    for key, val in list(dictionary.items()):
        lst.append((val, key))
    lst.sort(reverse=True)
    for val, key in lst:
        lst2.append((key, val))
    return lst2

def get_value_sums(data, column1, column2) -> pd.Series:
    """ Get sum of column2 values for each column1 value"""
    # df = pd.DataFrame()
    indx = data[column1].unique()
    vals = []
    for i in indx:
        sm = data[data[column1] == i][column2].sum()
        vals.append(sm)
    # df[column1] = indx
    # df[column2] = vals
    return pd.Series(vals, indx)

def format_time(val, unit):
    # if not isinstance(val, (int, float)):
    #     try:
    #         val = float(val) if "." in val else int(val)
    #     except ValueError:
    #         return
    match unit[0]:
        case "s":
            h = val // 3600
            m = (val - h*3600) // 60
            s = val - h*3600 - m*60
            return f"{h}h {m}m {s}s"
        case "m":
            s = 0
            if isinstance(val, float):
                s = (val - int(val//1)) * 60
            h = val // 60
            m = val - h*60 - s/60
            return f"{h}h {m}m {s}s"
        case "h":
            if not isinstance(val, float):
                return f"{val}h"
            m = (val - int(val//1)) * 60
            s = 0
            if isinstance(m, float):
                s = (m - int(m//1)) * 60
                m = m - s/60

            h = val - m/60 - s/3600
            return f"{h}h {m}m {s}s"



if __name__ == '__main__':
    import file as f
    df = f.load_file('E:/Savelli_larmanalys/20251104_Z39A_Main/HMI_33IR/ArchiveManager/AlarmLogging/DESKTOP-HFS4KSQ_HMI#33IR_ALG_202511062300_202511072232.mdf')
    print(get_unique_values(df))
    print(get_info(df))
    print(5.467603, format_time(5.467603, 'h'))
    print(546.7603, format_time(546.7603, 'm'))
    print(54676030345, format_time(54676030345, 's'))