from typing import List
import pyodbc

# modules
import configs
import models
from cache import time_limited_cache

@time_limited_cache(max_age_seconds=1600)
def get_raw_order_data() -> List[models.OrderLine]:
    cnxn = pyodbc.connect(configs.read_connect_string)
    cursor = cnxn.cursor()
    query = """
DECLARE @CurrentDate DATE = GETDATE();
DECLARE @DateLimit DATE = DATEADD(year, -7, getdate());
SELECT 
    itm.ItemCode, 
    sol.QtyOrdered, 
    ipkg.ConversionUnits, 
    CONVERT(VARCHAR(10), sol.DateRequired, 120) AS DateRequired,
	si.SiteName
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
    so.DivisionID = 1 
    AND sol.DateRequired < @CurrentDate 
    AND sol.DateRequired > @DateLimit
    AND ets.IsCancelled = 0 
    AND ets.IsOnHold = 0
    AND sol.QtyOrdered > 0
	AND cu.CustomerCode != 'FAI101';
    """
    orders: List[models.OrderLine] = []
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        order_line = models.OrderLine(
            code= row.ItemCode,
            base_qty= int(row.QtyOrdered * row.ConversionUnits),
            date= row.DateRequired,
            site= row.SiteName
            )
        orders.append(order_line)
    return orders
