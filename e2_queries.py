from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Union
import pyodbc
import logging

# modules
import configs
import models
from cache import time_limited_cache
from cache import CACHE_SECONDS

logging.basicConfig(level=logging.DEBUG)


@time_limited_cache(max_age_seconds=120)
def get_orders_placed_today(dollars: bool) -> Decimal:
    cnxn = pyodbc.connect(configs.read_connect_string)
    cursor = cnxn.cursor()
    query = """
-- Calculate the total value of orders entered today excluding specified customer
SELECT 
    SUM(itm.[AvgPriceAUDEach] * ip.ConversionUnits * sol.QtyOrdered) AS TotalValue
FROM 
    [SalesOrderLine] AS sol
    INNER JOIN [SalesOrder] AS so ON so.[SalesOrderID] = sol.[SalesOrderID]
    INNER JOIN [Customer] AS cust ON cust.[CustomerID] = so.[CustomerID]
	inner join [item] as i on i.ItemID = sol.ItemID
	inner join [ItemPackaging] as ip on ip.ItemPackagingID = sol.ItemPackagingID
    INNER JOIN [ManagementPortal].[dbo].[Item] AS itm ON itm.Code = i.ItemCode
WHERE 
    CONVERT(DATE, sol.[CreatedDate]) = CAST(GETDATE() AS DATE)
    AND cust.[CustomerCode] <> 'FAI101';
"""
    if not dollars:
        query = """
-- Calculate the total value of orders entered today excluding specified customer
SELECT 
    SUM(ip.ConversionUnits * sol.QtyOrdered) AS TotalValue
FROM 
    [SalesOrderLine] AS sol
    INNER JOIN [SalesOrder] AS so ON so.[SalesOrderID] = sol.[SalesOrderID]
    INNER JOIN [Customer] AS cust ON cust.[CustomerID] = so.[CustomerID]
	inner join [item] as i on i.ItemID = sol.ItemID
	inner join [ItemPackaging] as ip on ip.ItemPackagingID = sol.ItemPackagingID
    INNER JOIN [ManagementPortal].[dbo].[Item] AS itm ON itm.Code = i.ItemCode
WHERE 
    CONVERT(DATE, sol.[CreatedDate]) = CAST(GETDATE() AS DATE)
    AND cust.[CustomerCode] <> 'FAI101;
        """
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        return row.TotalValue
        

@time_limited_cache(max_age_seconds=CACHE_SECONDS)
def get_raw_order_data(dollars: bool = False) -> List[models.OrderLine]:
    logging.info("Connecting to database")
    logging.info(f'connect string: {configs.read_connect_string}')
    cnxn = pyodbc.connect(configs.read_connect_string)
    logging.info("Connected to database")
    cursor = cnxn.cursor()
    query = """
SET NOCOUNT ON;
SELECT 
    itm.ItemCode, 
    sol.QtyOrdered, 
    ipkg.ConversionUnits, 
    CONVERT(VARCHAR(10), sol.DateRequired, 120) AS DateRequired,
    CASE 
        WHEN si.SiteName = '11 Warehouse' THEN '90 Prosperity'
        WHEN si.SiteName = '17 Warehouse' THEN '90 Prosperity'
        ELSE si.SiteName 
    END AS SiteName
FROM 
    SalesOrderLine AS sol
INNER JOIN 
    SalesOrder AS so ON so.SalesOrderID = sol.SalesOrderID
INNER JOIN 
    EntityTypeTransactionStatus AS ets ON ets.EntityTypeTransactionStatusID = so.EntityTypeTransactionStatusID
INNER JOIN 
    Item AS itm ON itm.ItemID = sol.ItemID
INNER JOIN 
    ItemPackaging AS ipkg ON ipkg.ItemPackagingID = sol.ItemPackagingID
INNER JOIN
    Site as si on si.SiteID = so.SiteID
INNER JOIN
    Customer as cu on cu.CustomerID = so.CustomerID
WHERE 
    sol.DateRequired < GETDATE()
    AND sol.DateRequired > DATEADD(year, -7, GETDATE())
    AND ets.IsCancelled = 0 
    AND ets.IsOnHold = 0
    AND sol.QtyOrdered > 0
    AND cu.CustomerCode != 'FAI101'
	AND si.SiteName not like '%SAMPLE%';
    """
    orders: List[models.OrderLine] = []
    cursor.execute(query)
    rows = cursor.fetchall()
    if dollars:
        item_costs: Dict[str, Decimal] = get_item_costs()
    for row in rows:
        if dollars == False or row.ItemCode in item_costs:
            qty_or_value = int(int(row.QtyOrdered * row.ConversionUnits) * item_costs[row.ItemCode]) if dollars else int(
                row.QtyOrdered * row.ConversionUnits)
        order_line = models.OrderLine(
            code= row.ItemCode,
            base_qty=qty_or_value,
            date= row.DateRequired,
            site= row.SiteName
            )
        orders.append(order_line)
    return orders


@time_limited_cache(max_age_seconds=CACHE_SECONDS)
def get_item_costs() -> Dict[str, Decimal]:
    cnxn = pyodbc.connect(configs.read_connect_string)
    cursor = cnxn.cursor()
    query = """
SELECT [t0].[Code], [t0].[AvgPriceAUDEach], [t0].[ListPriceAUDEach]
FROM [ManagementPortal].[dbo].[Item] AS [t0]
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    item_costs = {}
    for row in rows:
        if row.AvgPriceAUDEach or row.ListPriceAUDEach:
            item_costs[row.Code] = Decimal(row.AvgPriceAUDEach) if row.AvgPriceAUDEach else Decimal(row.ListPriceAUDEach)
    return item_costs


# WAIT TIMES

@time_limited_cache(max_age_seconds=CACHE_SECONDS)
def get_raw_wait_data(years: int = 7) -> List[models.WaitDatabaseLine]:
    print("Connecting to database")
    print("Connecting to database")
    print("Connecting to database")
    cnxn = pyodbc.connect(configs.read_connect_string)
    cursor = cnxn.cursor()
    query = """
-- Select the relevant columns with calculated quantity in each
SELECT 
cast(cdl.ProcessedDate as date) as ProcessedDate, 
i.ItemCode, 
c.CustomerCode, 
cdl.QtyDespatched * ip.ConversionUnits AS QtyEachDespatched, 
s.SiteName, 
cast(sol.DateRequired as date) as DateRequired,
cd.CustomerDespatchNo,
st.SalesTerritoryName
FROM 
CustomerDespatchLine AS cdl
INNER JOIN EntityTypeTransactionStatus AS etts ON etts.EntityTypeTransactionStatusID = cdl.EntityTypeTransactionStatusID
INNER JOIN Item AS i ON i.ItemID = cdl.ItemID
INNER JOIN ItemPackaging AS ip ON ip.ItemPackagingID = cdl.ItemPackagingID
INNER JOIN CustomerDespatch AS cd ON cd.CustomerDespatchID = cdl.CustomerDespatchID
INNER JOIN Customer AS c ON cd.CustomerID = c.CustomerID
INNER JOIN Site AS s ON s.SiteID = cd.SiteID
LEFT OUTER JOIN SalesOrderLine AS sol ON sol.SalesOrderLineID = cdl.SalesOrderLineID
LEFT OUTER JOIN CustomerInvoiceLine as cil on cil.CustomerDespatchLineID = cdl.CustomerDespatchLineID
LEFT OUTER JOIN SalesTerritory as st on st.SalesTerritoryID = cil.SalesTerritoryID
WHERE 
etts.IsDespatched = 1 
AND cdl.ProcessedDate IS NOT NULL 
AND cdl.ProcessedDate > DATEADD(year, -7, GETDATE())
ORDER BY
cdl.ProcessedDate desc
"""
    cursor.execute(query)
    rows = cursor.fetchall()
    wait_times: List[models.WaitDatabaseLine] = []
    item_costs = get_item_costs()
    for row in rows:
        wait_time_line = models.WaitDatabaseLine(
            site= '90 Prosperity' if row.SiteName.startswith('11') or row.SiteName.startswith('17') else row.SiteName,
            item_code=row.ItemCode,
            customer_code=row.CustomerCode,
            wait_time_days=(parse_date(row.ProcessedDate) -
                            parse_date(row.DateRequired)).days,
            qty_eaches_sent=row.QtyEachDespatched,
            date_required=row.DateRequired,
            date_despatched=row.ProcessedDate,
            date_str=to_iso8601_date(
                row.ProcessedDate),
            cda= row.CustomerDespatchNo,
            month=parse_date(row.ProcessedDate).month,
            year=parse_date(row.ProcessedDate).year,
            day=parse_date(row.ProcessedDate).day,
            required_str=to_iso8601_date(row.DateRequired),
            sales_territory=row.SalesTerritoryName
        )
        wait_times.append(wait_time_line)
    return wait_times

@time_limited_cache(max_age_seconds=CACHE_SECONDS)
def parse_date(date_value: Union[str, datetime, date, None]) -> datetime:
    if date_value is None:
        raise ValueError("None is not a valid date value")
    if isinstance(date_value, datetime):
        return date_value
    if isinstance(date_value, date):
        return datetime.combine(date_value, datetime.min.time())
    if isinstance(date_value, str):
        try:
            return datetime.fromisoformat(date_value)
        except ValueError:
            raise ValueError(f"Invalid date string format: {date_value}")
    raise TypeError(f"Unsupported date type: {type(date_value)}")

@time_limited_cache(max_age_seconds=CACHE_SECONDS)
def to_iso8601_date(input_value):
    """
    Convert input to ISO 8601 date string.
    
    Parameters:
    input_value (any): The input value to be converted. Can be a datetime, string, or other type.
    
    Returns:
    str: ISO 8601 formatted date string.
    
    Raises:
    ValueError: If the input cannot be converted to a date.
    """
    if isinstance(input_value, datetime):
        return input_value.date().isoformat()
    elif isinstance(input_value, date):
        return input_value.isoformat()
    elif isinstance(input_value, str):
        try:
            # Try parsing the string to a date
            parsed_date = datetime.fromisoformat(input_value).date()
            return parsed_date.isoformat()
        except ValueError:
            # Try different formats if ISO format fails
            try:
                parsed_date = datetime.strptime(input_value, "%Y-%m-%d").date()
                return parsed_date.isoformat()
            except ValueError:
                try:
                    parsed_date = datetime.strptime(
                        input_value, "%d/%m/%Y").date()
                    return parsed_date.isoformat()
                except ValueError:
                    raise ValueError(
                        f"String {input_value} is not a valid date format")
    else:
        raise ValueError(f"Cannot convert type",
                        f"{type(input_value)} to ISO 8601 date string")
