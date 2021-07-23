import json
import os
import time
from sds011 import SDS011
import redis

redis_client = redis.StrictRedis(host=os.environ.get('REDIS_HOST'), port=6379, db=0)


class AirQualityMonitor():

    def __init__(self):
        self.sds = SDS011(port='/dev/ttyUSB0')
        self.sds.set_working_period(rate=1)

    def get_current_value(self):
        return {
            'time': int(time.time()),
            'measurement': self.sds.read_measurement(),
        }

    def get_historic_values(self, granularity, n):
        """Returns the last 'n' datapoints from the 'granularity' redis"""
        return [json.loads(x) for x in redis_client.lrange(granularity, 0, n-1)]

    def get_average_value(self, granularity, n):
        """returns the average value from the last 'n' datapoints at 'granularity'"""
        list = self.get_historic_values(granularity, n)
        list_pm10 = [x['measurement']['pm10'] for x in list]
        list_pm2_5 = [x['measurement']['pm2.5'] for x in list]
        avg_pm10 = 0
        if len(list_pm10) > 0
            avg_pm10 = sum(list_pm10) / len(list_pm10)
        avg_pm2_5 = 0
        if len(list_pm2_5) > 0
            avg_pm2_5 = sum(list_pm2_5) / len(list_pm2_5)
        return {
            'time': list[0]['time'],
            'measurement': { 'pm10': avg_pm10, 'pm2.5': avg_pm2_5 },
        }

    def save_measurement_to_redis(self, granularity):
        """Saves measurement to redis db for the given 'granularity'"""
        if granularity == 'minute':
            redis_client.lpush(granularity, json.dumps(self.get_current_value(), default=str))
        elif granularity == 'hour':
            redis_client.lpush(granularity, json.dumps(self.get_average_value('minute', 60), default=str))
        elif granularity == 'day':
            redis_client.lpush(granularity, json.dumps(self.get_average_value('hour', 24), default=str))
