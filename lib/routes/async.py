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
from unicron.tasks import async as async_task

async = Blueprint("async", __name__)


@async.route("/<task_id>", methods=['GET'])
@utils.api_response
def get(task_id):
    '''Get single async task by its unique key'''
    return async_task.get.delay(task_id).get()


@async.route("/", methods=['POST'])
@utils.api_response
def run():
    '''Run a new async task to run immediately'''
    payload = request.get_json(force=True, silent=True)
    schema = {
        "properties": {
            "name": {"type": "string"},
            "job_id": {"type": "string", "default": None},
            "http_url": {"type": "string", "default": ""},
            "http_method": {"type": "string", "default": "get"},
            "http_headers": {"type": "object", "default": {}},
            "http_data": {"type": "object", "default": {}},
            "command": {"type": "string", "default": ""},
            "email": {"type": "string", "default": ""},
            "hook_url": {"type": "string", "default": ""},
            "hook_headers": {"type": "object", "default": {}},
        },
        "required": ["name"]
    }
    validate(payload, schema)
    attrs = {}
    for key, val in schema["properties"].items():
        attrs[key] = payload[key] if key in payload else val["default"]
    task = async_task.run.delay(**attrs)
    return task.id
