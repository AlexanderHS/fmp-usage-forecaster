import datetime
import os
from typing import List, Optional
from flask import Flask, request

# modules
import configs
import logging
import e2_queries
import predictions
import models
from wait_days import (
    get_smooth_wait_dates,
    get_wait_days_with_missing,
    get_scatter_plot_data,
    get_lines_only,
)

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

logging.getLogger("prophet").setLevel(logging.DEBUG)
logging.getLogger("cmdstanpy").setLevel(logging.DEBUG)


@app.route("/")
def base_url():
    # handles base case with no item code
    return get_order(None)


def to_bool(value):
    """Converts a string to a boolean if necessary."""
    return value.lower() == "true" if isinstance(value, str) else bool(value)


@app.route("/wait/")
def wait_dates():
    return wait_times(None)


@app.route("/wait/<item_code>")
def wait_times(item_code: Optional[str] = None):
    # return {'none': 'none'}
    """Returns the wait times for each item."""
    if item_code == "-NONE-":
        item_code = None
    customer_code: Optional[str] = request.args.get("customer_code", default=None, type=str)
    if customer_code == "-NONE-":
        customer_code = None
    site_filter: Optional[str] = request.args.get("site_filter", default=None, type=str)
    if site_filter == "-NONE-":
        site_filter = None
    sales_territory: Optional[str] = request.args.get("sales_territory", default=None, type=str)
    if sales_territory == "-NONE-":
        sales_territory = None
    category: Optional[str] = request.args.get("category", default=None, type=str)
    if category == "-NONE-":
        category = None
    item_type: Optional[str] = request.args.get("type", default=None, type=str)
    if item_type == "-NONE-":
        item_type = None
    parent: Optional[str] = request.args.get("parent", default=None, type=str)
    if parent == "-NONE-":
        parent = None
    show_waits = request.args.get("show_waits", default=False, type=to_bool)
    smoothing = request.args.get("smoothing", default=None, type=int)
    lines_only = request.args.get("lines_only", default=False, type=to_bool)
    limit = request.args.get("limit", default=None, type=int)
    if lines_only:
        return get_lines_only(
            item_code=item_code,
            customer_code=customer_code,
            site_filter=site_filter,
            sales_territory=sales_territory,
            category=category,
            item_type=item_type,
            parent=parent,
            limit=limit,
        )
    mode = request.args.get("mode", default="mean", type=str)
    assert mode in ["mean", "median", "max", "min", "mode"]
    scatter_plot_group = request.args.get("scatter_plot_group", default=None, type=str)
    if scatter_plot_group:
        if scatter_plot_group == "-NONE-":
            scatter_plot_group = "customer_code"
        return get_scatter_plot_data(
            item_code=item_code,
            customer_code=customer_code,
            site_filter=site_filter,
            sales_territory=sales_territory,
            category=category,
            item_type=item_type,
            parent=parent,
            type=scatter_plot_group,
            mode=mode,
        )
    if smoothing:
        wait_dates = get_smooth_wait_dates(
            item_code,
            site_filter,
            customer_code,
            smoothing,
            mode,
            sales_territory,
            category,
            item_type,
            parent,
        )
    else:
        wait_dates = get_wait_days_with_missing(
            item_code,
            site_filter,
            customer_code,
            mode,
            sales_territory,
            category,
            item_type,
            parent,
        )
    if show_waits:
        raw_data = e2_queries.get_raw_wait_data()
        return {
            "wait_times": raw_data,
            "wait_dates": [
                {
                    "date": x.date,
                    "waits": [
                        {"qty": y.qty, "wait_time_days": y.wait_time_days}
                        for y in x.waits
                    ],
                }
                for x in wait_dates
            ],
        }
    return {
        #'wait_times': raw_data,
        "wait_dates": [
            {"date": x.date, "qty": x.total_est_value(), "wait_days": x.wait_days}
            for x in wait_dates
        ],
    }


@app.route("/<item_code>")
def get_order(item_code):
    # Default parameters
    if item_code == "-NONE-":
        item_code = None
    reload_cache = request.args.get("reload_cache", default=False, type=to_bool)
    orders_placed_today = request.args.get(
        "orders_placed_today", default=False, type=to_bool
    )
    dollars = request.args.get("dollars", default=False, type=to_bool)
    if orders_placed_today:
        result = e2_queries.get_orders_placed_today(dollars)
        return (
            {"orders_placed_today": int(result)}
            if result
            else {"orders_placed_today": 0}
        )
    if reload_cache:
        predictions.get_orders.clear_cache()
        e2_queries.get_raw_order_data.clear_cache()
        print("Cleared cache")
        print("Cleared cache")
        print("Cleared cache")
    days = request.args.get("days", default=30, type=int)
    total_only = request.args.get("total_only", default=False, type=to_bool)
    total_past_only = request.args.get("total_past_only", default=False, type=to_bool)
    past_orders_only = request.args.get("past_orders_only", default=False, type=to_bool)
    future_orders_only = request.args.get(
        "future_orders_only", default=False, type=to_bool
    )
    all_dates_only = request.args.get("all_dates_only", default=False, type=to_bool)
    yearly_growth_only = request.args.get(
        "yearly_growth_only", default=False, type=to_bool
    )
    if yearly_growth_only:
        days = 365
    smoothing = request.args.get("smoothing", default=14, type=int)
    site_filter = request.args.get("site_filter", default=None, type=str)
    if site_filter == "-NONE-":
        site_filter = None
    site_filter2 = request.args.get("site_filter2", default=None, type=str)

    logging.info(f"days: {days}")
    logging.info(f"future_orders_only: {future_orders_only}")

    # Retrieve data
    past_orders = [
        (x.date, x.qty)
        for x in predictions.get_orders(
            item_code,
            site_filter=site_filter,
            site_filter2=site_filter2,
            dollars=dollars,
        )
    ]
    if not past_orders_only:
        predictions_model = predictions.get_predictions(
            item_code=item_code,
            days=days,
            site_filter=site_filter,
            site_filter2=site_filter2,
            dollars=dollars,
        )
        logging.info(f"predictions_model created: {len(predictions_model)}")

    data = {
        "item_code": item_code,
        "days": days,
        "predictions": predictions_model if not past_orders_only else None,
        "past_orders": past_orders,
        "prediction_period_total": (
            max(0, sum([x[1] for x in predictions_model]))
            if not past_orders_only
            else None
        ),
        "past_orders_total": sum([x[1] for x in past_orders]),
    }

    # Return data based on query params
    if total_only:
        return {"total": int(data["prediction_period_total"])}
    if total_past_only:
        # return the total of past orders using only the most recent days
        recent_past = data["past_orders"][-days:]
        return {"total_past": sum([x[1] for x in recent_past])}
    if yearly_growth_only:
        last_year_data = data["past_orders"][-days:]
        last_year_total = sum([x[1] for x in last_year_data])
        next_year_total = data["prediction_period_total"]
        growth_percentage = (next_year_total - last_year_total) / last_year_total
        return {"growth_percentage": growth_percentage}
    if past_orders_only:
        return predictions.smooth_predictions(
            data["past_orders"], smoothing_days=smoothing
        )
    if future_orders_only:
        return predictions.smooth_predictions(
            data["predictions"], smoothing_days=smoothing
        )
    if smoothing > 0 and all_dates_only:
        return predictions.smooth_predictions(
            data["past_orders"] + data["predictions"], smoothing
        )
    if all_dates_only:
        return data["past_orders"] + data["predictions"]
    return data


if __name__ == "__main__":

    # PRODUCTION ENVIRONMENT
    if os.name == "posix":
        # app.run(host='0.0.0.0', port=8099, debug=True)
        from waitress import serve

        serve(app, host="0.0.0.0", port=8099)
    # TESTING ENVIRONMENT
    if os.name == "nt":
        app.run(host="0.0.0.0", port=8099, debug=True)
