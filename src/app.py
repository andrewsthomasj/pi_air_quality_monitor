import os
import time
from flask import Flask, request, jsonify, render_template
from AirQualityMonitor import AirQualityMonitor
from apscheduler.schedulers.background import BackgroundScheduler
import redis
import atexit
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
aqm = AirQualityMonitor()

scheduler = BackgroundScheduler()
scheduler.add_job(func=aqm.save_measurement_to_redis, args=['minute'], trigger='interval', seconds=60)
scheduler.add_job(func=aqm.save_measurement_to_redis, args=['hour'], trigger='interval', seconds=3600)
scheduler.add_job(func=aqm.save_measurement_to_redis, args=['day'], trigger='cron', hour=12)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


def reconfigure_data(measurement):
    """Reconfigures data for chart.js"""
    current = int(time.time())
    measurement.reverse()
    return {
        'labels': [x['measurement']['timestamp'] for x in measurement],
        'pm10': {
            'label': 'pm10',
            'data': [x['measurement']['pm10'] for x in measurement],
            'backgroundColor': '#cc0000',
            'borderColor': '#cc0000',
            'borderWidth': 3,
        },
        'pm2': {
            'label': 'pm2.5',
            'data': [x['measurement']['pm2.5'] for x in measurement],
            'backgroundColor': '#42C0FB',
            'borderColor': '#42C0FB',
            'borderWidth': 3,
        },
    }

@app.route('/')
def index():
    """Index page for the application"""
    context = {
        'hour': reconfigure_data(aqm.get_historic_values('minute', 60)),
        'day': reconfigure_data(aqm.get_historic_values('hour', 24)),
        'month': reconfigure_data(aqm.get_historic_values('day', 31)),
        'year': reconfigure_data(aqm.get_historic_values('day', 365)),
    }
    return render_template('index.html', context=context)


@app.route('/api/')
@cross_origin()
def api():
    """Returns historical data from the sensor"""
    context = {
        'hour': reconfigure_data(aqm.get_historic_values('minute', 60)),
        'day': reconfigure_data(aqm.get_historic_values('hour', 24)),
        'month': reconfigure_data(aqm.get_historic_values('day', 31)),
        'year': reconfigure_data(aqm.get_historic_values('day', 365)),
    }
    return jsonify(context)

@app.route('/avg/')
@cross_origin()
def avg():
    """Returns avg data"""
    context = {
        'hour': aqm.get_average_value('minute', 60),
        'day': aqm.get_average_value('hour', 24)
    }
    return jsonify(context)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=int(os.environ.get('PORT', '8001')))
