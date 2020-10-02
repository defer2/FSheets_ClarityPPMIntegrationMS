from flask import Blueprint, request, jsonify, Response, abort
from flask_cors import CORS, cross_origin
import controllers

view_blueprint = Blueprint('view_blueprint', __name__)
CORS(view_blueprint, resources={r'/*': {"origins": "192.168.0.50:5015"}})


@view_blueprint.route('/', methods=['GET'])
@cross_origin()
def hello_world():
    return 'Hello World'


@view_blueprint.route('/timesheet', methods=['POST'])
@cross_origin()
def submit_timesheet():
    timesheet = request.json
    result = controllers.submit_timesheet(timesheet)
    if result['error']:
        abort(Response(result['message'], 403))
    else:
        return result['message']
