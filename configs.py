import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def check_env_variables():
    required_vars = ["E2_DB_USER", "E2_DB_PW"]
    missing_vars = [var for var in required_vars if os.getenv(var) is None]

    if missing_vars:
        error_msg = "Error: Missing required environment variables.\n"
        error_msg += "Please make sure you have a .env file in the project root with the following variables:\n"
        error_msg += "\n".join(required_vars)
        error_msg += "\n\nYou can use the .env.template file as a starting point."
        raise EnvironmentError(error_msg)


check_env_variables()

db_user = os.getenv("E2_DB_USER")
db_pw = os.getenv("E2_DB_PW")

if os.name == "posix":
    read_connect_string = (
        "DRIVER={FreeTDS}; "
        "Server=192.168.0.13; "
        "PORT=49954; "
        "Database=AwareNewFairmont; "
        f"UID={db_user}; "
        f"PWD={db_pw}; "
        "TDS_Version=7.2"
    )
if os.name == "nt":
    read_connect_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        r"SERVER=fm-sql-01.fairmont.local\FAIRMONTSQL; "
        "PORT=49954; "
        "Database=AwareNewFairmont; "
        f"UID={db_user}; "
        f"PWD={db_pw}; "
        "TrustServerCertificate=yes;"
    )
