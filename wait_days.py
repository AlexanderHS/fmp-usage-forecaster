

from typing import List, Set

# modules
import models
from cache import time_limited_cache, CACHE_SECONDS
import e2_queries
from predictions import generate_date_range

def get_wait_dates(lines: Set[models.WaitDatabaseLine], mode: str = 'mean') -> List[models.WaitDate]:
    dates = {}
    for line in lines:
        if line.date_str not in dates:
            dates[line.date_str] = []
        dates[line.date_str].append(models.Wait(line.qty_eaches_sent, line.wait_time_days))
    wait_dates = []
    for date_str, waits in dates.items():
        wait_dates.append(models.WaitDate(
            date=date_str,
            waits=waits,
            mode=mode))
    return wait_dates


def smooth_wait_dates(wait_dates: List[models.WaitDate], smoothing: int, mode: str = 'mean') -> List[models.WaitDate]:
    smoothed_dates = []
    total_dates = len(wait_dates)
    for i in range(total_dates):
        waits = []
        start_index = max(0, i - smoothing)
        end_index = min(total_dates, i + smoothing + 1)
        for j in range(start_index, end_index):
            waits.extend(wait_dates[j].waits)
        smoothed_dates.append(models.WaitDate(
            date=wait_dates[i].date,
            waits=waits,
            mode=mode))
    return smoothed_dates

@time_limited_cache(max_age_seconds=CACHE_SECONDS)
def get_filtered_data(item_code: str = None, site_filter: str = None, customer_code: str = None) -> List[models.WaitDatabaseLine]:
    raw_data = e2_queries.get_raw_wait_data()
    raw_data: List[models.WaitDatabaseLine] = [
        x for x in raw_data if x.item_code == item_code] if item_code else raw_data
    raw_data: List[models.WaitDatabaseLine] = [
        x for x in raw_data if x.site.startswith(site_filter)] if site_filter else raw_data
    raw_data: List[models.WaitDatabaseLine] = [
        x for x in raw_data if x.customer_code == customer_code] if customer_code else raw_data
    return raw_data


@time_limited_cache(max_age_seconds=CACHE_SECONDS)
def get_sorted_wait_dates(item_code: str = None, site_filter: str = None, customer_code: str = None, mode: str = 'mean') -> List[models.WaitDate]:
    raw_data = get_filtered_data(
        item_code=item_code, site_filter=site_filter, customer_code=customer_code)
    wait_dates = get_wait_dates(raw_data, mode)
    wait_dates = sorted(wait_dates, key=lambda x: x.date)
    return wait_dates

@time_limited_cache(max_age_seconds=CACHE_SECONDS)
def get_wait_days_with_missing(item_code: str = None, site_filter: str = None, customer_code: str = None, mode: str = 'mean') -> List[models.WaitDate]:
    wait_dates = get_sorted_wait_dates(
        item_code, site_filter, customer_code, mode)

    # insert missing days
    if wait_dates:
        start_date = wait_dates[0].date
        end_date = wait_dates[-1].date
        all_dates = generate_date_range(start_date, end_date)
        all_dates = [x for x in all_dates if x not in [y.date for y in wait_dates]]
        for date in all_dates:
            wait_dates.append(models.WaitDate(date=date, waits=[], mode=mode))
        wait_dates = sorted(wait_dates, key=lambda x: x.date)
    return wait_dates

@time_limited_cache(max_age_seconds=CACHE_SECONDS)
def get_smooth_wait_dates(item_code: str = None, site_filter: str = None, customer_code: str = None, smoothing: int = 3, mode: str = 'mean') -> List[models.WaitDate]:
    wait_days = get_wait_days_with_missing(
        item_code, site_filter, customer_code, mode)
    wait_days = smooth_wait_dates(wait_days, smoothing, mode)
    return wait_days
