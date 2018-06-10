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

timezone = os.environ.get('TZ', 'UTC')

redis_host = os.environ.get('REDIS_HOST', None)
if not redis_host:
    raise Exception("can't find REDIS_HOST env variable")
redis_port = os.environ.get('REDIS_PORT', "6379")
redis_db = os.environ.get('REDIS_DB', "0")
redis_password = os.environ.get('REDIS_PASSWORD', "")
broker_url = "redis://:{pw}@{host}:{port}/{db}".format(
    pw=redis_password,
    host=redis_host,
    port=str(redis_port),
    db=str(redis_db))
result_backend = broker_url
result_expires = 3600 * 24
enable_utc = False
broker_transport_options = {'visibility_timeout': 1800}
imports = (
    "unicron.tasks.job",
    "unicron.tasks.async",
)
