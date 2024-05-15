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
    return get_order(None)


def to_bool(value):
    """Converts a string to a boolean if necessary."""
    return value.lower() == 'true' if isinstance(value, str) else bool(value)


@app.route('/<item_code>')
def get_order(item_code):
    # Default parameters
    if item_code == '-NONE-':
        item_code = None
    days = request.args.get('days', default=30, type=int)
    total_only = request.args.get('total_only', default=False, type=to_bool)
    neural = request.args.get(
        'neural', default=False, type=to_bool)
    total_past_only = request.args.get(
        'total_past_only', default=False, type=to_bool)
    past_orders_only = request.args.get(
        'past_orders_only', default=False, type=to_bool)
    future_orders_only = request.args.get(
        'future_orders_only', default=False, type=to_bool)
    all_dates_only = request.args.get(
        'all_dates_only', default=False, type=to_bool)
    yearly_growth_only = request.args.get(
        'yearly_growth_only', default=False, type=to_bool)
    if yearly_growth_only:
        days = 365
    smoothing = request.args.get('smoothing', default=14, type=int)
    site_filter = request.args.get('site_filter', default=None, type=str)
    if site_filter == '-NONE-':
        site_filter = None
    site_filter2 = request.args.get('site_filter2', default=None, type=str)
    dollars = request.args.get('dollars', default=False, type=to_bool)

    logging.info(f"days: {days}")
    logging.info(f"future_orders_only: {future_orders_only}")

    # Retrieve data
    past_orders = [(x.date, x.qty) for x in predictions.get_orders(item_code, site_filter=site_filter, site_filter2=site_filter2, dollars=dollars)]
    
    predictions_model = predictions.get_predictions(
        item_code=item_code, days=days, site_filter=site_filter, site_filter2=site_filter2, dollars=dollars)
    if neural:
        predictions_model = predictions.get_predictions_neural(
            item_code=item_code, days=days, site_filter=site_filter, site_filter2=site_filter2, dollars=dollars)

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
    if total_past_only:
        # return the total of past orders using only the most recent days
        recent_past = data['past_orders'][-days:]
        return {'total_past': sum([x[1] for x in recent_past])}
    if yearly_growth_only:
        last_year_data = data['past_orders'][-days:]
        last_year_total = sum([x[1] for x in last_year_data])
        next_year_total = data['prediction_period_total']
        growth_percentage = (next_year_total - last_year_total) / last_year_total
        return {'growth_percentage': growth_percentage}
    if past_orders_only:
        return predictions.smooth_predictions(data['past_orders'], smoothing_days=smoothing)
    if future_orders_only:
        return predictions.smooth_predictions(data['predictions'], smoothing_days=smoothing)
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
