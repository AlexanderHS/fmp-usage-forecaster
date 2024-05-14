# fmp-usage-forecaster

## Setting up Environment Variables

Depending on your operating system, follow the guidelines below to set up the required environment variables:

### Windows

To set the environment variables on Windows, run the following commands in Command Prompt:

```cmd
setx E2_DB_USER "your_db_user_here"
setx E2_DB_PW "your_db_pw_here"
```

These commands will permanently set the `XERO_CLIENT_ID` and `XERO_CLIENT_SECRET` environment variables.

### Linux/MacOS

For Linux and MacOS, use the following commands to set the environment variables:

nano ~/.bash_profile

Add these lines to the file:

export XERO_CLIENT_ID="your_client_id_here"
export XERO_CLIENT_SECRET="your_client_secret_here"
export E2_DB_USER="your_db_user_here"
export E2_DB_PW="your_db_pw_here"

Save and exit the editor, then source the file:

```
source ~/.bash_profile
```

This will apply the environment variables to your current session and all future sessions.