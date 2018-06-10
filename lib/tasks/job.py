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

import json
import croniter
from unicron.common import utils, config
from unicron.worker import celery


@celery.task(name="job.getAll", bind=True, acks_late=True)
def getAll(self):
    '''Get all scheduled jobs'''
    jobs = {}
    rds = utils.redis_connect()
    for key in rds.scan_iter(config.scheduler_jobs + ":*"):
        key = key.decode()
        job = utils.convert2str(rds.hgetall(key))
        if "info" not in job:
            continue
        # info saved as json in Redis
        job["info"] = utils.convert2str(json.loads(utils.decrypt(job["info"])))
        jobs[utils.remove_prefix(key, config.scheduler_jobs + ":")] = job
    return jobs


@celery.task(name="job.get", bind=True, acks_late=True)
def get(self, job_id):
    '''Get one scheduled job info'''
    rds = utils.redis_connect()
    job = utils.convert2str(rds.hgetall(config.scheduler_jobs + ":" + job_id))
    if "info" not in job:
        return None
    # data saved as json in Redis
    job["info"] = json.loads(utils.decrypt(job["info"]))
    return job


@celery.task(name="job.getResultAll", bind=True, acks_late=True)
def getResultAll(self):
    '''Get results for all scheduled jobs'''
    results = []
    rds = utils.redis_connect()
    for key in rds.scan_iter(config.celery_tasks + "*"):
        t = json.loads(utils.convert2str(rds.get(key.decode())))
        if "result" not in t:
            continue
        if "output" not in t["result"]:
            continue
        task_res = t["result"]["output"]
        if type(task_res) is not dict:
            continue
        # check if there is a job_id in the task output
        if "job_id" in task_res and task_res["job_id"] is not None:
                results.append(t["result"])
    return results


@celery.task(name="job.getResult", bind=True, acks_late=True)
def getResult(self, job_id):
    '''Get results for one scheduled job'''
    results = []
    rds = utils.redis_connect()
    for key in rds.scan_iter(config.celery_tasks + "*"):
        t = json.loads(utils.convert2str(rds.get(key.decode())))
        if "result" not in t:
            continue
        if "output" not in t["result"]:
            continue
        task_res = t["result"]["output"]
        if type(task_res) is not dict:
            continue
        # find results with the right job_id
        if "job_id" in task_res and task_res["job_id"] == job_id:
            results.append(t["result"])
    return results


@celery.task(name="job.create", bind=True, acks_late=True)
def create(self, schedule, **kwargs):
    '''Create a new scheduled job'''
    if not croniter.croniter.is_valid(schedule):
        raise Exception("bad cron expression")
    if kwargs["job_id"] is None or len(kwargs["job_id"]) == 0:
        raise Exception("job_id can not be empty")
    if len(kwargs["http_url"]) == 0 and len(kwargs["command"]) == 0:
        raise Exception("you need to provide http_url or command")
    rds = utils.redis_connect()
    result = rds.hmset(
        config.scheduler_jobs + ":" + kwargs["job_id"],
        {
            "last_run": "",
            "run_count": 0,
            "schedule": schedule,
            "info": utils.encrypt(json.dumps(utils.convert2str(kwargs)))
        }
    )
    if result:
        return kwargs["job_id"]
    return False


@celery.task(name="job.delete", bind=True, acks_late=True)
def delete(self, job_id):
    '''Delete scheduled job'''
    rds = utils.redis_connect()
    return rds.delete(config.scheduler_jobs + ":" + job_id)
