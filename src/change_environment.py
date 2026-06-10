import re
import os
import stat
import subprocess
import sys
import pyuac
from pyuac import main_requires_admin


@main_requires_admin
def main(e, files):
    print("hand")
    if '08001' in e:
        start_express()
    elif '42000' in e:
        files = files.strip("[]")
        files = files.split(',')
        give_permissions(files)

def handle_db_error(e, files):
    print("hand")
    if '08001' in e:
        start_express()
    elif '42000' in e:
        give_permissions(list(files))


def start_express():
    """ Start or restart the sql express service. """
    print("serv")
    # SQL Server (SQLEXPRESS)
    # MSSQL$SQLEXPRESS
    # service = subprocess.run(['sc', 'qc', 'MSSQL$SQLEXPRESS', '5000'])
    # mat = re.search(r'C:\\.*\.exe', str(service))
    # if not mat:
    #     return
    # path = mat.group()
    # print(path)

    return subprocess.run(['sc', 'start', 'MSSQL$SQLEXPRESS'])


def give_permissions(files):
    """ Give read/write permissions to sql express """
    print("files")
    for file in files:
        fpath = file.replace("/", "\\")
        fpath = fpath.replace("'", "")
        print(fpath)
        os.chmod(fpath, 0o777)
        file_stat = os.stat(fpath)
        permissions = oct(file_stat.st_mode)[-3:]
        print(f"New permissions: {permissions}")


if __name__ == '__main__':

    main(sys.argv[1], sys.argv[2])