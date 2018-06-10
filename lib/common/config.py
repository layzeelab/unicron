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

version = 0.1

# this key is used to encrypt job info on Redis
# and it should be unique for each Unicron cluster
key = os.environ.get('UNICRON_KEY', None)
if not key:
    raise Exception("can't find UNICRON_KEY env variable")
if len(key) != 16:
    raise Exception("UNICRON_KEY must be 16 chars")

stdlogs = int(os.environ.get('DEBUG', 0))

scheduler_timer = 30
scheduler_locktimer = 60
cluster_lock = "unicron-lock"
scheduler_lock = "unicron-sched"
scheduler_jobs = "unicron-jobs"
celery_tasks = "celery-task-meta-"
unicron_api = "http://127.0.0.1/api"

email_from = os.environ.get('EMAIL_FROM', "")
smtp_host = os.environ.get('SMTP_HOST', "")
smtp_port = os.environ.get('SMTP_PORT', 25)
smtp_tls = os.environ.get('SMTP_TLS', 0)
smtp_user = os.environ.get('SMTP_USER', "")
smtp_password = os.environ.get('SMTP_PASSWORD', "")
email_enabled = True if len(email_from) > 0 and len(smtp_host) > 0 else False
