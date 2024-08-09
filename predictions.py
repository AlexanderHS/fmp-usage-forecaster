from joblib import Parallel, delayed
import datetime
import pandas as pd
import numpy as np
from prophet import Prophet
from typing import List
import logging

# modules
import e2_queries
import models
from cache import time_limited_cache
from cache import CACHE_SECONDS

logging.basicConfig(level=logging.INFO)


@time_limited_cache(max_age_seconds=CACHE_SECONDS)
def generate_date_range(start_date: str, end_date: str) -> List[str]:
    """Generates a list of dates from start_date to end_date in ISO 8601 format."""
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    return [
        (start + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range((end - start).days + 1)
    ]


@time_limited_cache(max_age_seconds=CACHE_SECONDS)
def get_orders(
    item_code: str,
    site_filter: str = None,
    site_filter2: str = None,
    dollars: bool = False,
) -> List[models.OrderDay]:
    # Get raw order data
    raw_data = e2_queries.get_raw_order_data(dollars=dollars)

    # Filter raw data for the specified item code
    if item_code:
        filtered_data = [order for order in raw_data if order.code == item_code]
    else:
        filtered_data = raw_data
    if site_filter and not site_filter2:
        filtered_data = [order for order in filtered_data if site_filter in order.site]
    if site_filter and site_filter2:
        filtered_data = [
            order
            for order in filtered_data
            if site_filter in order.site or site_filter2 in order.site
        ]

    # Group orders by date and sum the quantities
    grouped_data = {}
    for order in filtered_data:
        if order.date in grouped_data:
            grouped_data[order.date] += order.base_qty
        else:
            grouped_data[order.date] = order.base_qty

    # Determine the start date and end date
    if grouped_data:
        start_date = min(grouped_data.keys())
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")

        # Generate all dates within the range
        all_dates = generate_date_range(start_date, end_date)

        # Ensure all dates in the range have an entry
        full_data = {date: grouped_data.get(date, 0) for date in all_dates}
    else:
        # If no orders, return empty list
        return []

    # Convert the grouped data to a list of OrderDay objects
    orders = [models.OrderDay(date=date, qty=qty) for date, qty in full_data.items()]

    return orders


def smooth_predictions(data, smoothing_days):
    n = len(data)
    values = [d[1] for d in data]
    dates = [d[0] for d in data]

    # Compute cumulative sums
    cumsum = [0] * (n + 1)
    for i in range(1, n + 1):
        cumsum[i] = cumsum[i - 1] + values[i - 1]

    half_window = smoothing_days // 2
    smoothed_data = []

    for i in range(n):
        # Calculate the start and end of the window
        start = max(0, i - half_window)
        # +1 because slicing is exclusive on the upper bound
        end = min(n, i + half_window + 1)

        # Calculate the sum using cumulative sums
        window_sum = cumsum[end] - cumsum[start]
        window_length = end - start

        # Compute the average for the current day
        avg_value = window_sum / window_length

        # Store the result with the current date
        smoothed_data.append([dates[i], avg_value])

    return smoothed_data


@time_limited_cache(max_age_seconds=CACHE_SECONDS)
def get_predictions(
    item_code: str,
    days: int = 30,
    site_filter: str = None,
    site_filter2: str = None,
    dollars: bool = False,
) -> List[tuple]:
    order_history = get_orders(
        item_code, site_filter=site_filter, site_filter2=site_filter2, dollars=dollars
    )

    # Create a dataframe from the order history
    df = pd.DataFrame(
        {
            "ds": [order.date for order in order_history],
            "y": [order.qty for order in order_history],
        }
    )

    # Make sure the dataset includes all dates in the range, filling missing dates with zero
    df.set_index("ds", inplace=True)
    df.index = pd.to_datetime(df.index)
    start_date = df.index.min()
    end_date = df.index.max()

    # if none or nat, make it seven years ago from today
    if pd.isna(start_date):
        start_date = datetime.datetime.now() - datetime.timedelta(days=7 * 365)

    # if none or nat, make it today
    if pd.isna(end_date):
        end_date = datetime.datetime.now()

    idx = pd.date_range(start_date, end_date)
    df = df.reindex(idx, fill_value=0).reset_index().rename(columns={"index": "ds"})

    # Initialize the Prophet model
    model = Prophet()

    # Fit the model with the data
    model.fit(df)

    # Create a dataframe to store future dates for prediction
    last_date = df["ds"].max()
    future_dates = model.make_future_dataframe(periods=days, include_history=False)
    future_dates = future_dates[future_dates["ds"] > last_date]

    # Use the model to make predictions
    forecast = model.predict(future_dates)

    # Extract date and forecasted value, and convert to list of tuples
    predictions = list(zip(forecast["ds"].dt.strftime("%Y-%m-%d"), forecast["yhat"]))

    return predictions


if __name__ == "__main__":
    # Create a synthetic dataset: dates and corresponding values
    df = pd.DataFrame(
        {
            "ds": pd.date_range(start="2023-01-01", periods=100, freq="D"),
            "y": (0.05 * (np.arange(100) % 24) + np.random.randn(100) * 0.2).cumsum(),
        }
    )

    # Initialize the Prophet model
    model = Prophet()

    # Fit the model with the data
    model.fit(df)

    # Create a dataframe to store future dates for prediction
    future_dates = model.make_future_dataframe(periods=30)

    # Use the model to make predictions
    forecast = model.predict(future_dates)

    # Plot the forecast
    # fig = model.plot(forecast)

    # Show the components (trend, yearly seasonality, and weekly seasonality) of the model
    # fig_components = model.plot_components(forecast)

    # Extract date and forecasted value, and convert to list of tuples
    predictions = list(zip(forecast["ds"].dt.strftime("%Y-%m-%d"), forecast["yhat"]))

    # Output the predictions list
    print(predictions)
