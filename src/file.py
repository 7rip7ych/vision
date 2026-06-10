"""
Read and export to files
"""
# from IPython.display import display
import re
import os
import stat
import subprocess
import sys
import pyuac
import pandas as pd
import pyodbc
from scrapy.signals import engine_stopped
from sqlalchemy import create_engine, exc
import sqlalchemy
from sqlalchemy.engine import URL
from PyQt6.QtCore import QEventLoop
from PyQt6.QtWidgets import * # pyright: ignore[reportWildcardImportFromLibrary]
from src.warning import WarningWindow

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
pyodbc.pooling = False
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
        r'DRIVER={SQL Server};'
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

def load_files(files, query="view", load_info=False, recur=0):
    """load all files"""
    data = []
    qry = VIEW_QUERY if query == "view" else ALL_DATA_QUERY
    for path in files:
        fpath = path.replace("/", "\\")
        # print(fpath)
        # print(rf'AttachDbFileName={fpath};')
        cnxn_str = (
            r'DRIVER={SQL Server};'
            r'SERVER=(local)\SQLEXPRESS;'
            r'Trusted_Connection=yes;'
            r'User Instance=True;'
            rf'AttachDbFileName={fpath};'
        )
        # cnxn = pyodbc.connect(cnxn_str)
        # with pyodbc.connect(cnxn_str) as cnxn:
        #     table = pd.read_sql(qry, cnxn)
        try:
            engine = create_alchemy_engine(cnxn_str)
            with engine.connect() as conn:
                table = pd.read_sql(qry, conn)
                if load_info:
                    info = pd.read_sql(INFO_QUERY, conn)
                conn.close()
            data.append(table)
            return (data, info) if load_info else data
        except (exc.OperationalError, exc.ProgrammingError) as e:
            print(e._message())
            if recur > 1:
                return (None, None) if load_info else None

            win = EnvWindow(e._message(), files)
            win.exec()

            return load_files(files, query, load_info, recur+1)



def reload_file(files, query="view", load_info=False):
    """load all files"""
    data = []
    qry = VIEW_QUERY if query == "view" else ALL_DATA_QUERY
    for path in files:
        fpath = path.replace("/", "\\")
        # print(fpath)
        # print(rf'AttachDbFileName={fpath};')
        cnxn_str = (
            r'DRIVER={SQL Server};'
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
            conn.close()
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



class EnvWindow(QDialog):
    def __init__(self, e, files):
        super().__init__()
        self.err = e
        self.files = files
        self.setWindowTitle("Troubleshoot")
        self.setMinimumWidth(500)
        layt = QVBoxLayout()
        self.setLayout(layt)
        self.message = QLabel("Something went wrong :/", self)
        self.message.setWordWrap(True)
        layt.addWidget(self.message)

        btn_group = QWidget()
        group_layout = QHBoxLayout()
        btn_group.setLayout(group_layout)

        self.leftb = QPushButton("Manual fix")
        self.leftb.pressed.connect(self.instructions)
        self.rightb = QPushButton("Automatic fix")
        self.rightb.pressed.connect(self.auto_fix)
        self.rightb.setFocus()
        group_layout.addWidget(self.leftb)
        group_layout.addWidget(self.rightb)
        layt.addWidget(btn_group)

        self.message.setText('Something went wrong when communicating with SQL Express. '
                             'The program can try to solve this automatically (requires admin privileges)'
                             ' or you could follow the instructions available to solve the problem manually.')
        self.show()


    def instructions(self):
        self.leftb.pressed.disconnect()
        self.rightb.pressed.disconnect()
        self.leftb.setText("Automatic fix")
        self.leftb.pressed.connect(self.auto_fix)
        self.rightb.setText("Done")
        self.rightb.pressed.connect(self.accept)
        self.rightb.setFocus()

        if '08001' in self.err:
            # service not running
            msg = '''
            The program did not find an instance of SQL Express running on the computer. \n
            If you have not yet installed SQL Express make sure to do so on Microsoft's download page: 
            https://www.microsoft.com/sv-se/sql-server/sql-server-downloads
            \n
            If you have installed Express, make sure the service is running by following the steps below.
                1. Press the Windows key + R to open the Run window.
                2. Type in 'services.msc' and press enter.
                3. In the opened Services window, scroll down to find a service titled 'SQL Server (SQLEXPRESS).
                4. Right click the service and select 'start' or 'restart' if the service is already running.
                5. Press the 'Done' button below to try reading the file again.
            '''
        elif '42000' in self.err:
            # no permissions
            msg = f'''
            The SQL Express do not have the required permissions to open the selected file(s).
            To solve this the permissions for each file or their parent directories need to be changed.
            For each file/directory follow the steps below:
                1. Navigate to the file/folder in file explorer.
                2. Right click on the file/folder and select properties from the context menu.
                3. In the Properties window, navigate to the Security tab and press the 'Edit' button 
                   to change permissions (requires admin privileges).
                4. If SQLExpress is not in the list of users press the 'Add' button
            
            The selected file(s):
            {"\n".join(self.files)}
            '''
        self.message.setText(msg)

    def auto_fix(self):
        res = subprocess.Popen(['py', 'src/change_environment.py', self.err, str(self.files)])
        res.communicate()
        self.accept()


