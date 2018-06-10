#!/usr/bin/env python3
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

import logging
import requests
import time
import datetime
import pytz
import croniter
import json
from functools import wraps
from unicron.common import config, celeryconfig, utils


def log_exception(func):
    '''Decorator for catching and logging exceptions'''
    @wraps(func)
    def f_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if config.stdlogs:
                logger.warning(func.__name__ + " error " + str(e))
    return f_wrapper


@log_exception
def run_scheduler(lock_key):
    '''Scheduler function for sending async tasks'''
    if config.stdlogs:
        logger.warning("running scheduler with key " + lock_key)
    rds = utils.redis_connect()
    # process scheduler lock
    slock = utils.convert2str(rds.get(config.scheduler_lock))
    # it is locked by another scheduler process
    if slock is not None and str(slock) != lock_key:
        if config.stdlogs:
            logger.warning("exiting scheduler. locked by " + slock)
        return
    # add or update lock and set new expiration
    if config.stdlogs:
        logger.warning("updating scheduler lock " + lock_key)
    rds.set(config.scheduler_lock, lock_key)
    rds.expire(config.scheduler_lock, config.scheduler_locktimer)
    # set now
    tz = pytz.timezone(celeryconfig.timezone)
    now = tz.localize(datetime.datetime.now())
    now = now.replace(second=0, microsecond=0)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    # process tasks
    for key in rds.scan_iter(config.scheduler_jobs + ":*"):
        key = key.decode()
        job = utils.convert2str(rds.hgetall(key))
        # skip if we have already created the job
        if job["last_run"] == now_str:
            if config.stdlogs:
                logger.warning("skip sent job")
            continue
        # just update last_run and go to next job
        if len(job["last_run"]) == 0:
            rds.hset(key, "last_run", now_str)
            continue
        # find the next run time
        job["last_run"] = tz.localize(
            datetime.datetime.strptime(job["last_run"], "%Y-%m-%d %H:%M:%S"))
        next_run = croniter.croniter(
            job["schedule"], job["last_run"]).get_next(datetime.datetime)
        next_run = next_run.replace(second=0, microsecond=0)
        while next_run < now:
            next_run = croniter.croniter(
                job["schedule"], next_run).get_next(datetime.datetime)
        # update last_run and create the job
        if next_run.strftime("%Y-%m-%d %H:%M:00") != now_str:
            continue
        try:
            # create async task to run once immediately
            r = requests.post(
                config.unicron_api + "/async/",
                json=utils.convert2str(json.loads(utils.decrypt(job["info"])))
            )
            if config.stdlogs:
                logger.warning("job scheduled: " + utils.convert2str(r.text))
            # update last_run of the job
            rds.hset(key, "last_run", now_str)
            rds.hincrby(key, "run_count")
        except Exception as e:
            if config.stdlogs:
                logger.warning("request error " + str(e))


def main():
    '''Run Scheduler every few seconds'''
    lock_key = utils.genrandkey()
    while True:
        run_scheduler(lock_key)
        time.sleep(config.scheduler_timer)


if __name__ == "__main__":
    if config.stdlogs:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)-8s %(message)s'))
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.warning("Starting scheduler...")
    # confirm cluster key or generate a new lock for fresh cluster
    utils.verify_cluster()
    main()
