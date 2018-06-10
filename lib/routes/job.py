# (c) layzeelab.com 2018, Armin Ranjbar Daemi (@rmin)
#
# This file is part of Unicron (@layzeelab).
# Unicron is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from unicron.common import utils
from flask import Blueprint, request
from jsonschema import validate
from unicron.tasks import job as job_task

job = Blueprint("job", __name__)


@job.route("/", methods=['GET'])
@utils.api_response
def getAll():
    '''Get all scheduled jobs'''
    return job_task.getAll.delay().get()


@job.route("/<job_id>", methods=['GET'])
@utils.api_response
def get(job_id):
    '''Get single scheduled job by its unique key string'''
    return job_task.get.delay(job_id).get()


@job.route("/result", methods=['GET'])
@utils.api_response
def getResultAll():
    '''Get all job results in the past 24 hours'''
    return job_task.getResultAll.delay().get()


@job.route("/result/<job_id>", methods=['GET'])
@utils.api_response
def getResult(job_id):
    '''Get single scheduled job results by its unique key string'''
    return job_task.getResult.delay(job_id).get()


@job.route("/", methods=['POST'])
@utils.api_response
def create():
    '''Create a new scheduled job'''
    payload = request.get_json(force=True, silent=True)
    schema = {
        "properties": {
            "name": {"type": "string"},
            "schedule": {"type": "string"},
            "http_url": {"type": "string", "default": ""},
            "http_method": {"type": "string", "default": "get"},
            "http_headers": {"type": "object", "default": {}},
            "http_data": {"type": "object", "default": {}},
            "command": {"type": "string", "default": ""},
            "email": {"type": "string", "default": ""},
            "hook_url": {"type": "string", "default": ""},
            "hook_headers": {"type": "object", "default": {}},
        },
        "required": ["name", "schedule"]
    }
    validate(payload, schema)
    attrs = {"job_id": utils.genrandkey()}
    for key, val in schema["properties"].items():
        attrs[key] = payload[key] if key in payload else val["default"]
    return job_task.create.delay(**attrs).get()


@job.route("/<job_id>", methods=['DELETE'])
@utils.api_response
def delete(job_id):
    '''De-schedule a scheduled job'''
    return job_task.delete.delay(job_id).get()
