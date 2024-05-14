import os

db_user = os.getenv('E2_DB_USER')
db_pw = os.getenv('E2_DB_PW')

if os.name == "posix":
    read_connect_string = ("DRIVER={FreeTDS}; "
                           "Server=192.168.0.13; "
                           "PORT=49954; "
                           "Database=AwareNewFairmont; "
                           f"UID={db_user}; "
                           f"PWD={db_pw}; "
                           "TDS_Version=7.2")
if os.name == "nt":
    read_connect_string = ("DRIVER={SQL Server Native Client 11.0};"
                           r"SERVER=fm-sql-01.fairmont.local\FAIRMONTSQL; "
                           "PORT=49954; "
                           "Database=AwareNewFairmont; "
                           f"UID={db_user}; "
                           f"PWD={db_pw}; "
                           "Trusted_Connection=yes;")
