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

import subprocess
import json
from unicron.common import utils, config
from unicron.worker import celery


@celery.task(name="async.get", bind=True, acks_late=True)
def get(self, task_id):
    '''Get status and result for one async task on Redis'''
    rds = utils.redis_connect()
    res = rds.get(config.celery_tasks + task_id)
    if res is None:
        return None
    return json.loads(utils.convert2str(res))


@celery.task(name="async.run", bind=True, acks_late=True)
@utils.task_response
def run(
    self, job_id, name,
    http_url, http_method, http_headers, http_data,
    command,
    email,
    hook_url, hook_headers
):
    '''Run a new async task'''

    # first check if we need to run a shell command
    if len(command):
        cmd = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = cmd.communicate()
        result = {
            "job_id": job_id,
            "stdout": utils.convert2str(stdout),
            "stderr": utils.convert2str(stderr)
        }
        # run email and web hook
        utils.send_email(name, result, email)
        utils.call_url(hook_url, "post", result, hook_headers)
        return result

    # if we need to call a url
    if len(http_url):
        if http_method.lower() not in [
            "get", "post", "put", "delete", "head", "options", "patch"
        ]:
            raise Exception("http method not supported")
        resp = utils.call_url(http_url, http_method, http_data, http_headers)
        result = {
            "job_id": job_id,
            "status_code": resp.status_code,
            "text": utils.convert2str(resp.text)
        }
        # run email and web hook
        utils.send_email(name, result, email)
        utils.call_url(hook_url, "post", result, hook_headers)
        return result

    return None
