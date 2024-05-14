from decimal import Decimal
from typing import Dict, List
import pyodbc
import logging

# modules
import configs
import models
from cache import time_limited_cache

logging.basicConfig(level=logging.DEBUG)

@time_limited_cache(max_age_seconds=1600)
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


@time_limited_cache(max_age_seconds=1600)
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