import os
from flask import Flask, request

# modules
import configs
import logging
import e2_queries
import predictions

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

@app.route('/')
def hello_world():
    return e2_queries.get_raw_order_data()


def to_bool(value):
    """Converts a string to a boolean if necessary."""
    return value.lower() == 'true' if isinstance(value, str) else bool(value)


@app.route('/<item_code>')
def get_order(item_code):
    # Default parameters
    days = request.args.get('days', default=30, type=int)
    total_only = request.args.get('total_only', default=False, type=to_bool)
    past_orders_only = request.args.get(
        'past_orders_only', default=False, type=to_bool)
    future_orders_only = request.args.get(
        'future_orders_only', default=False, type=to_bool)
    all_dates_only = request.args.get(
        'all_dates_only', default=False, type=to_bool)
    smoothing = request.args.get('smoothing', default=14, type=int)
    site_filter = request.args.get('site_filter', default=None, type=str)
    site_filter2 = request.args.get('also_include_site_matching', default=None, type=str)

    logging.info(f"days: {days}")
    logging.info(f"future_orders_only: {future_orders_only}")

    # Retrieve data
    past_orders = [(x.date, x.qty) for x in predictions.get_orders(item_code, site_filter=site_filter, site_filter2=site_filter2)]
    predictions_model = predictions.get_predictions(
        item_code=item_code, days=days, site_filter=site_filter, site_filter2=site_filter2)

    data = {
        'item_code': item_code,
        'days': days,
        'predictions': predictions_model,
        'past_orders': past_orders,
        'prediction_period_total': max(0, sum([x[1] for x in predictions_model])),
        'past_orders_total': sum([x[1] for x in past_orders])
    }

    # Return data based on query params
    if total_only:
        return {'total': int(data['prediction_period_total'])}
    if past_orders_only:
        return data['past_orders']
    if future_orders_only:
        return data['predictions']
    if smoothing > 0 and all_dates_only:
        return predictions.smooth_predictions(data['past_orders'] + data['predictions'], smoothing)
    if all_dates_only:
        return data['past_orders'] + data['predictions']
    return data

if __name__ == "__main__":

    # PRODUCTION ENVIRONMENT
    if os.name == "posix":
        # app.run(host='0.0.0.0', port=8086, debug=True)
        from waitress import serve
        serve(app, host="0.0.0.0", port=8099)
    # TESTING ENVIRONMENT
    if os.name == "nt":
        app.run(host='0.0.0.0', port=8099, debug=True)
