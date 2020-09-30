import json
import math
from datetime import datetime, timedelta
import requests
from flask import jsonify
from requests.auth import HTTPBasicAuth

ppm_username = ''
ppm_password = ''
ppm_url = 'http://xxxxxx/ppm/rest/v1/'


def submit_timesheet(timesheet):
    try:
        timesheet_date = timesheet['date'] + 'T00:00:00'
        dTimesheet_date = datetime.strptime(timesheet_date, '%Y-%m-%dT00:00:00')
        dTimesheet_week_start_date = dTimesheet_date - timedelta(days=dTimesheet_date.weekday())
        dTimesheet_week_end_date = dTimesheet_week_start_date + timedelta(days=6)
        resource_id = __get_resource_id(timesheet['resource_name'])
        timesheet_id = __get_timesheet(resource_id, dTimesheet_week_start_date.strftime('%Y-%m-%dT00:00:00'))

        if not timesheet_id:
            timeperiod_id = __get_timeperiod_id(dTimesheet_week_start_date.strftime('%Y-%m-%dT00:00:00'))
            timesheet_id = __create_timesheet(timeperiod_id, resource_id)

        for task in timesheet['Tasks']:
            project_id = task['project']
            task_name = task['task_name']
            duration = task['duration']

            task_id = __get_task_id(project_id, task_name)
            if not task_id:
                task_id = __create_task(project_id, task_name, task['slot_hour'], task['slot_hour'])

            timeentry = __get_timeentry(timesheet_id, task_id)

            if not timeentry:
                request = __generate_request_for_create_timeentry(dTimesheet_week_start_date,
                                                                  dTimesheet_week_end_date, timesheet_date,
                                                                  task_id, duration)

                __create_timeentry(timesheet_id, request)
            else:
                request = __generate_request_for_update_timeentry(timesheet_date, task_id,
                                                                  duration, timeentry['actuals'])

                __update_timeentry(timesheet_id, timeentry['_internalId'], request)

        __update_timesheet_last_sync(timesheet['id'])

        result = {
            "error": False,
            "message": "OK"
        }
    except Exception as e:
        result = {
            "error": True,
            "message": str(e)
        }
    finally:
        return result


def __calculate_duration(start_date, end_date):
    duration = (end_date - start_date)
    return math.ceil(duration.total_seconds())


def __get_timesheet(resource_id, start_date):
    resource = 'timesheets'
    timeperiod_id = __get_timeperiod_id(start_date)
    query = {'filter': '( timePeriodId = ' + str(timeperiod_id) + ' ) and ( resourceId = ' + str(resource_id) + ' )'}
    response = requests.get(ppm_url + resource, params=query, auth=HTTPBasicAuth(ppm_username, ppm_password))
    data = response.json()
    try:
        return data['_results'][0]['_internalId']
    except:
        return False


def __create_timeentry(timesheet_id, request):
    resource = 'timesheets'
    resource += '/' + str(timesheet_id)
    resource += '/' + 'timeEntries'
    payload = request
    response = requests.post(ppm_url + resource, data=payload, auth=HTTPBasicAuth(ppm_username, ppm_password))
    return response


def __update_timeentry(timesheet_id, timeentry_id, request):
    resource = 'timesheets'
    resource += '/' + str(timesheet_id)
    resource += '/' + 'timeEntries'
    resource += '/' + str(timeentry_id)

    payload = request
    response = requests.patch(ppm_url + resource, data=payload, auth=HTTPBasicAuth(ppm_username, ppm_password))
    return response


def __create_timesheet(timeperiod_id, resource_id):
    resource = 'timesheets'
    payload = {"timePeriodId": timeperiod_id, "resourceId": resource_id}
    response = requests.post(ppm_url + resource, json=payload, auth=HTTPBasicAuth(ppm_username, ppm_password))
    data = response.json()
    return data['_results'][0]['_internalId']


def __create_task(project_id, task_name, start_date, end_date):
    resource = 'projects'
    resource += '/' + project_id
    resource += '/' + 'tasks'
    payload = {'name': task_name, 'startDate': start_date, 'finishDate': end_date}
    response = requests.post(ppm_url + resource, json=payload, auth=HTTPBasicAuth(ppm_username, ppm_password))
    data = response.json()
    return data['_internalId']


def __get_timeentry(timesheet_id, task_id):
    resource = 'timesheets'
    resource += '/' + str(timesheet_id)
    resource += '/' + 'timeEntries'
    query = {'filter': '( taskId = ' + str(task_id) + ' )'}

    response = requests.get(ppm_url + resource, params=query, auth=HTTPBasicAuth(ppm_username, ppm_password))
    data = response.json()
    try:
        timeentry_id = data['_results'][0]['_internalId']
        resource += '/' + str(timeentry_id)

        response = requests.get(ppm_url + resource, params=query, auth=HTTPBasicAuth(ppm_username, ppm_password))
        return response.json()
    except:
        return False


def __get_resource_id(resource_name):
    resource = 'resources'
    query = {'filter': '( uniqueName = \'' + resource_name + '\' )'}
    response = requests.get(ppm_url + resource, params=query, auth=HTTPBasicAuth(ppm_username, ppm_password))
    data = response.json()
    return data['_results'][0]['_internalId']


def __get_task_id(project_id, task_name):
    resource = 'projects'
    resource += '/' + project_id
    resource += '/' + 'tasks'
    query = {'filter': '( name = \'' + task_name + '\' )'}

    response = requests.get(ppm_url + resource, params=query, auth=HTTPBasicAuth(ppm_username, ppm_password))
    data = response.json()
    try:
        if data['_results'][0]['_internalId']:
            return data['_results'][0]['_internalId']
    except:
        return False


def __get_timeperiod_id(start_date):
    resource = 'timePeriods'
    query = {'filter': '( startDate = \'' + start_date + '\' )'}
    response = requests.get(ppm_url + resource, params=query, auth=HTTPBasicAuth(ppm_username, ppm_password))
    data = response.json()
    return data['_results'][0]['_internalId']


def __generate_request_for_create_timeentry(dtimesheet_week_start_date, dtimesheet_week_end_date, timesheet_date,
                                            task_id, duration):
    segments = []
    for day in range(7):
        calculated_date = dtimesheet_week_start_date + timedelta(days=day)
        calculated_date = calculated_date.strftime('%Y-%m-%dT00:00:00')

        if calculated_date == timesheet_date:
            segments.append(
                {"start": calculated_date,
                 "finish": calculated_date,
                 "value": duration})
        else:
            segments.append(
                {"start": calculated_date,
                 "finish": calculated_date,
                 "value": 0})

    actuals = {"isFiscal": False,
               "curveType": "value",
               "total": 0,
               "dataType": "numeric", "_type": "tsv",
               "workEffortUnit": "none",
               "start": dtimesheet_week_start_date.strftime('%Y-%m-%dT00:00:00'),
               "finish": dtimesheet_week_end_date.strftime('%Y-%m-%dT00:00:00'),
               "segmentList": {"total": 0, "defaultValue": 0, "segments": segments}}

    request = {"taskId": task_id, "actuals": actuals}
    return json.dumps(request)


def __generate_request_for_update_timeentry(timesheet_date, task_id, duration, actuals):
    segments = actuals['segmentList']['segments']
    for segment in segments:
        if segment['start'] == timesheet_date:
            segment['value'] = duration

    request = {"taskId": task_id, "actuals": actuals}
    return json.dumps(request)


def __update_timesheet_last_sync(timesheet_id):
    try:
        params = {'operation': 'update_ppm_sync'}
        timesheetResponse = requests.put('http://192.168.0.50:5012/timesheets/' + str(timesheet_id), params=params)
        timesheet = timesheetResponse.json()
        return jsonify(timesheet[0])
    except:
        return jsonify('{}')
