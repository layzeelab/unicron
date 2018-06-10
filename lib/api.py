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
from flask import Flask
from unicron.common import utils, config
from unicron.routes.job import job
from unicron.routes.async import async

# confirm cluster key or generate a lock for fresh cluster
utils.verify_cluster()

app = Flask("unicron.api")
app.register_blueprint(job, url_prefix="/api/job")
app.register_blueprint(async, url_prefix="/api/async")


@app.route("/api/", methods=['GET'])
@utils.api_response
def version():
    return "LayzeeLab Unicron v" + str(config.version)


if __name__ == "__main__":
    if config.stdlogs:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)-8s %(message)s'))
        app.logger.addHandler(handler)
    app.run(host='0.0.0.0', port=80, threaded=True)
