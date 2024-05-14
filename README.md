# fmp-usage-forecaster

## Overview
This API service provides predictions and historical data on orders based on a given item_code. The service allows the client to retrieve various views of order data, including predictions, past orders, and a combination of both. Customizable query parameters can refine the response to include totals, apply filters, and perform data smoothing. Results cover all divisions of the company but exclude orders with Customer Code FAI101 to avoid double counting.

## Endpoint
```
GET /{item_code}
```

This endpoint retrieves order-related data for a specified item.

#### URL Parameters:
item_code (path parameter): A unique identifier for the item. This parameter must be included in the URL path.
#### Query Parameters:
- __days (integer, optional)__: Number of days into the future for which predictions should be calculated. Defaults to 30 days.
- __total_only__ (boolean, optional): If set to true, returns only the total predicted quantity for the specified period. Defaults to false.
- __past_orders_only__ (boolean, optional): If set to true, returns only the data for past orders. Defaults to false.
- __future_orders_only__ (boolean, optional): If set to true, returns only the predicted future orders. Defaults to false.
- __all_dates_only__ (boolean, optional): If set to true, returns both past and future orders. If smoothing is applied, data will be smoothed. Defaults to false.
- __smoothing__ (integer, optional): Smoothing factor to apply to the combined data of past and future orders. Applies only if all_dates_only is true. Defaults to 9.
- __site_filter__ (string, optional): A filter to apply for selecting orders from a specific site. No default.
- __site_filter2__ (string, optional): A secondary filter to include orders matching another site condition. No default.

#### Examples
__Basic Usage__:
```
GET /DIF7002
```
Retrieves all data (predictions and past orders) for the item with code DIF7002 for the next 30 days.

__Total Predictions Only__:
```
GET /MIX1001?total_only=true
```
Returns the total predicted quantity for item MIX1001 over the default period of 30 days.

__Past Orders with Specific Site Filter__:
```
GET /DCC8007?past_orders_only=true&site_filter=90%20Prosperity
```
Retrieves all past orders for item DCC8007 that are from '90 Prosperity'.

__Future Orders with Smoothing Applied__:
```
GET /LISS4122?future_orders_only=true&smoothing=5
```
Returns smoothed prediction data for item LISS4122 for the next 30 days, using a smoothing factor of 5.

__All Dates with Two Site Filters__:
```
GET /DIF7002?all_dates_only=true&site_filter=WA%20Warehouse&site_filter2=Rotterdam%20Warehouse
```
Retrieves both past and future orders for item DIF7002 from 'WA Warehouse' and also including orders that match 'Rotterdam Warehouse'.

This API is designed to be flexible, allowing for various combinations of parameters to suit different data retrieval needs. It is essential to ensure proper usage of the parameters to obtain accurate and relevant data.

## Setting up Environment Variables

Depending on your operating system, follow the guidelines below to set up the required environment variables:

### Windows

To set the environment variables on Windows, run the following commands in Command Prompt:

```cmd
setx E2_DB_USER "your_db_user_here"
setx E2_DB_PW "your_db_pw_here"
```

These commands will permanently set the `E2_DB_USER` and `E2_DB_PW` environment variables.

### Linux/MacOS

For Linux and MacOS, use the following commands to set the environment variables:

nano ~/.bash_profile

Add these lines to the file:

export E2_DB_USER="your_db_user_here"
export E2_DB_PW="your_db_pw_here"

Save and exit the editor, then source the file:

```
source ~/.bash_profile
```

This will apply the environment variables to your current session and all future sessions.