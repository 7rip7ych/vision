"""
Read and export to files
"""
# from IPython.display import display
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

VIEW_QUERY = '''
SELECT 
ms.Counter,
ms.DateTime,
ms.Ms,
ms.TimeDiff,
ms.MsgNr,
ms.Class,
replace(replace(cs.Classname, 'Errore', 'Error'), 'Sistema', 'System') AS Classname,
ms.Type,
ms.State,
replace(rt.StateText, 'Sistema di riconoscimento', 'R') AS StateText,
rt.Text1
FROM MsArcLong AS ms
	JOIN AlgRtTextsENG AS rt
		ON ms.Counter = rt.Counter
    LEFT JOIN AlgCSDataENG AS cs
	    ON ms.MsgNr = cs.NR
;
'''

ALL_DATA_QUERY = '''
SELECT 
ms.Counter,
ms.DateTime,
ms.Ms,
ms.TimeDiff,
ms.MsgNr,
ms.Class,
replace(replace(cs.Classname, 'Errore', 'Error'), 'Sistema', 'System') AS Classname,
ms.Type,
cs.Typename,
ms.State,
ms.Flags1,
ms.PValueUsed,
ms.Computername,
ms.Application,
ms.Username,
ms.Comment,
ms.Instance,
ms.PValue1,
ms.PValue2,
ms.PValue3,
ms.PValue4,
ms.PValue5,
ms.PValue6,
ms.PValue7,
ms.PValue8,
ms.PValue9,
ms.PValue10,
ms.PText1,
ms.PText2,
ms.PText3,
ms.PText4,
ms.PText5,
ms.PText6,
ms.PText7,
ms.PText8,
ms.PText9,
ms.PText10,
ms.ServerID,
ms.CrForeColor,
ms.CrBackColor,
ms.AG_NR,
ms.CPU_NR,
ms.Priority,
ms.AP_type,
ms.AP_name,
ms.AP_par,
ms.InfoText,
ms.AlarmTag,
ms.AckType,
ms.Params,
replace(rt.StateText, 'Sistema di riconoscimento', 'R') AS StateText,
rt.Text1,
rt.Text2,
rt.Text3,
rt.Text4,
rt.Text5,
rt.Text6,
rt.Text7,
rt.Text8,
rt.Text9,
rt.Text10,
rt.ClassName,
rt.TypeName,
rt.CmtText1,
rt.CmtText2,
rt.CmtText3,
rt.CmtText4,
rt.CmtText5,
rt.CmtText6,
rt.CmtText7,
rt.CmtText8,
rt.CmtText9,
rt.CmtText10
FROM MsArcLong AS ms
	JOIN AlgRtTextsENG AS rt
		ON ms.Counter = rt.Counter
    LEFT JOIN AlgCSDataENG AS cs
	    ON ms.MsgNr = cs.NR
;
'''

INFO_QUERY = """
SELECT NR,
      Class,
      Type,
      Text1,
      replace(replace(Classname, 'Errore', 'Error'), 'Sistema', 'System') AS Classname,
      Typename,
      iClass,
      iText1,
      AlarmTag
FROM AlgCSDataENG
;
"""

def create_alchemy_engine(connection_string):
    connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
    engine = create_engine(connection_url)
    return engine

def load_file(path, query="view"):
    """load all files"""
    fpath = path.replace("/", "\\")
    qry = VIEW_QUERY if query == "view" else ALL_DATA_QUERY
    # print(fpath)
    # print(rf'AttachDbFileName={fpath};')
    cnxn_str = (
        r'DRIVER=ODBC Driver 17 for SQL Server;'
        r'SERVER=(local)\SQLEXPRESS;'
        r'Trusted_Connection=yes;'
        r'User Instance=True;'
        rf'AttachDbFileName={fpath};'
    )
    # cnxn = pyodbc.connect(cnxn_str)
    # df = pd.read_sql("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';", cnxn)
    engine = create_alchemy_engine(cnxn_str)
    with engine.begin() as conn:
        msarc = pd.read_sql(VIEW_QUERY, conn)

    # display(msarc)

    return msarc

def load_files(files, query="view", load_info=False):
    """load all files"""
    data = []
    qry = VIEW_QUERY if query == "view" else ALL_DATA_QUERY
    for path in files:
        fpath = path.replace("/", "\\")
        # print(fpath)
        # print(rf'AttachDbFileName={fpath};')
        cnxn_str = (
            r'DRIVER=ODBC Driver 17 for SQL Server;'
            r'SERVER=(local)\SQLEXPRESS;'
            r'Trusted_Connection=yes;'
            r'User Instance=True;'
            rf'AttachDbFileName={fpath};'
        )
        # cnxn = pyodbc.connect(cnxn_str)
        # with pyodbc.connect(cnxn_str) as cnxn:
        #     table = pd.read_sql(qry, cnxn)
        engine = create_alchemy_engine(cnxn_str)
        with engine.begin() as conn:
            table = pd.read_sql(qry, conn)
            if load_info:
                info = pd.read_sql(INFO_QUERY, conn)

        data.append(table)
    return (data, info) if load_info else data


def readfile(file):
    """reads file and returns lines, takes file as arg"""
    with open(file, encoding="utf-8") as filehandle:
        content = filehandle.readlines()
    return content

def load_config():
    try:
        alarm_list = pd.read_excel(r".\config\HMIAlarms.xlsx")
        zone_list = pd.read_excel(r".\config\PLCTags_o_textgenereringar_20260405.xlsx", "ZonerStationer")
    except FileNotFoundError:
        print("Missing config files")
        return []
    return [alarm_list, zone_list]
