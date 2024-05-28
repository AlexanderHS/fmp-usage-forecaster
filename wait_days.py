

from typing import List

# modules
import models
from cache import time_limited_cache, CACHE_SECONDS

def get_wait_dates(lines: List[models.WaitDatabaseLine]) -> List[models.WaitDate]:
    dates = {}
    for line in lines:
        if line.date_str not in dates:
            dates[line.date_str] = []
        dates[line.date_str].append(models.Wait(line.qty_eaches_sent, line.wait_time_days))
    wait_dates = []
    for date_str, waits in dates.items():
        wait_dates.append(models.WaitDate(
            date=date_str,
            waits=waits))
    return wait_dates


def smooth_wait_dates(wait_dates: List[models.WaitDate], smoothing: int) -> List[models.WaitDate]:
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
            waits=waits))
    return smoothed_dates
