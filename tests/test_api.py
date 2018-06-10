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

import os
import json
import time
from unicron.api import app


class TestApi:

    def test_00_async(self):
        client = app.test_client()
        # create a new async task
        resp = client.post(
            '/api/async/',
            json={"name": "_", "command": "echo $TZ"}
        )
        r = json.loads(resp.data.decode())
        assert resp.status_code == 200
        assert r["success"] is True
        assert len(r["result"]) > 0
        task_id = r["result"]
        # wait 2s to get the result
        time.sleep(2)
        # get the result
        resp = client.get('/api/async/' + task_id)
        r = json.loads(resp.data.decode())
        assert resp.status_code == 200
        assert r["success"] is True
        assert r["result"]["status"] == "SUCCESS"
        assert r["result"]["result"]["output"]["stderr"].strip() == ""
        assert r["result"]["result"]["output"]["stdout"].strip() == \
            os.environ['TZ']

    def test_01_job(self):
        client = app.test_client()
        # create a new job
        resp = client.post(
            '/api/job/',
            json={"name": "_", "schedule": "* * * * *", "command": "echo $TZ"}
        )
        r = json.loads(resp.data.decode())
        assert resp.status_code == 200
        assert r["success"] is True
        assert len(r["result"]) > 0
        job_id = r["result"]
        # get job info
        resp = client.get('/api/job/' + job_id)
        r = json.loads(resp.data.decode())
        assert resp.status_code == 200
        assert r["success"] is True
        assert r["result"]["info"]["command"] == "echo $TZ"
        # wait 91s to make sure we have a result
        time.sleep(91)
        # get a result
        resp = client.get('/api/job/result/' + job_id)
        r = json.loads(resp.data.decode())
        assert resp.status_code == 200
        assert r["success"] is True
        assert r["result"][0]["output"]["stderr"].strip() == ""
        assert r["result"][0]["output"]["stdout"].strip() == os.environ['TZ']
        # delete the job
        resp = client.delete('/api/job/' + job_id)
        r = json.loads(resp.data.decode())
        assert resp.status_code == 200
        assert r["success"] is True
        assert r["result"] == 1
