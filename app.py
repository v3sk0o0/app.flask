import sys
import requests
import pdb
import datetime
import os
import json
from optparse import OptionParser
from functools import reduce
from operator import itemgetter
from flask import Flask, request, jsonify

parser = OptionParser()
usage = "usage: %prog [options] "
parser = OptionParser(usage=usage)

parser.add_option("--port", "-p", default="5000", action="store", help="port")
(options, args) = parser.parse_args()
app = Flask(__name__)

attributes = (
    'severity_level',
    'alert_type',
    'snooze_reason',
    'alert_category',
)
headers = {'x-api-key': 'PlexopExamAPIkey1PlexopExamAPIkey1 '}
url_funnels = 'https://9zrfwd2w7a.execute-api.us-east-1.amazonaws.com/dev/funnels'
funnels_enum = 'https://9zrfwd2w7a.execute-api.us-east-1.amazonaws.com/dev/funnels/enums'


def timeit(function):
    def wrapper(*args, **kwargs):

        start = datetime.datetime.now()
        result = function(*args, **kwargs)
        stop = datetime.datetime.now()
        difference = stop - start
        message = "{0}  was called with arg {2} and kward {3}  \ and took {1} seconds to complete".format(
            function.__name__, difference.total_seconds(), args, kwargs)
        print(message)
        return result

    return wrapper


@timeit
def decorate_request(url, headers):
    result = requests.get(url, headers=headers)
    return result.json() if result.status_code == 200 else {}


#number_of_alerts
def number_of_alerts(funnel):
    return len(funnel['alerts'])


#number_of_snoozed_alerts
def number_of_snoozed_alerts(funnel):
    return len(
        list(filter(lambda x: x['is_snoozed'] == True, funnel['alerts'])))


#exposure_sum:
def exposure_sum(funnel):
    return sum(i for i in map(lambda x: x['exposure'], funnel['alerts']))


#max_exposure_alert_id
def max_exposure_alert_id(funnel):
    return reduce(lambda x, y: x if (x['exposure'] >= y['exposure']) else y,
                  funnel['alerts'])['alert_id']


class Funnel_enum(object):
    def __init__(self, funnels_enum):
        self.alert_category = funnels_enum.get('alert_categories', None)
        self.alert_type = funnels_enum.get('alert_types', None)
        self.severity_level = funnels_enum.get('severity_levels', None)
        self.snooze_reason = funnels_enum.get('snooze_reasons', None)
        self.zone_type = funnels_enum.get('zone_types', None)

    def get_value(self, attribute, value):
        try:
            mappings = eval("self." + attribute)

        except:
            return None

        for item in mappings:
            if str(item['id']) == str(value):
                return item['name']

        return None


@app.route('/funnel/', methods=['GET'])
def give_modified_funnel():
    global headers, url_funnels, funnels_enum
    #Request to be moved to another function/class and decorated for log for the both request
    funnels = decorate_request(url_funnels, headers=headers)
    fun_enum = decorate_request(funnels_enum, headers=headers)
    enum_obj = Funnel_enum(fun_enum)

    for funnel in funnels:
        for alert in funnel['alerts']:
            for attribute in attributes:
                potential_id = alert[attribute + "_id"]
                alert[attribute + "_name"] = enum_obj.get_value(
                    attribute=attribute, value=potential_id)

    return jsonify(funnels)


@app.route('/funnel/summary/', methods=['GET'])
def give_modified_funnel_summary():
    global headers, url_funnels, funnels_enum

    funnels = decorate_request(url_funnels, headers=headers)
    fun_enum = decorate_request(funnels_enum, headers=headers)
    enum_obj = Funnel_enum(fun_enum)

    for funnel in funnels:

        funnel['number_of_alerts'] = number_of_alerts(funnel)
        funnel['number_of_snoozed_alerts'] = number_of_snoozed_alerts(funnel)
        funnel['max_exposure_alert_id'] = max_exposure_alert_id(funnel)
        funnel['exposure_sum'] = exposure_sum(funnel)
        funnel['zone_type_names'] = enum_obj.get_value(
            attribute="zone_type",
            value=funnel['extended_info']['zone_type_id'])

        for key, value in funnel['extended_info'].items():
            funnel[key] = value

        for delete_field in ('actions_history', 'alerts', 'extended_info'):


            del funnel[delete_field]

    return jsonify(sorted(funnels, key=itemgetter('exposure_sum'), reverse=True))


if __name__ == '__main__':
    # opts
    # sys.argv[1]
    # port=<Id>
    app.run(debug=True, port=int(options.port))
