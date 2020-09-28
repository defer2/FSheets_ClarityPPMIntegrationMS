import math
from datetime import datetime

import requests
from flask import jsonify

from ppm import utils


def submit_timesheet(timesheet):
    new_tasks = []
    for slot in timesheet['Slots']:
        for subslot in slot['Subslots']:
            exists = False
            duration = __calculate_duration(datetime.strptime(subslot["start_date"], '%Y-%m-%dT%H:%M:%S'),
                                            datetime.strptime(subslot["end_date"], '%Y-%m-%dT%H:%M:%S'))
            for new_subslot in new_tasks:
                if new_subslot['task_name'] == subslot["task_name"]:
                    new_subslot['duration'] += duration
                    exists = True

            if not exists:
                new_tasks.append({"task_name": subslot["task_name"],
                                  "project": subslot["project"]["ppm_project_id"],
                                  "duration": duration,
                                  "slot_hour": slot["hour"]})

    new_timesheet = {"date": timesheet['date'],
                     "resource_name": timesheet['resource_name'],
                     "Tasks": new_tasks,
                     "id": timesheet['id']}
    return utils.submit_timesheet(new_timesheet)


def __calculate_duration(start_date, end_date):
    duration = (end_date - start_date)
    return math.ceil(duration.total_seconds())

