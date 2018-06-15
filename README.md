# Unicron

![Travis CI build](https://travis-ci.com/layzeelab/unicron.svg?branch=master)

Unicron is a task queue and a replacement for Cron Unix service. It can be distributed to several machines using Docker, or any other Docker based platform (e.g. Docker Swarm, Kubernetes, Amazon ECS).

Unicron uses Redis as the backend to store time-based scheduled jobs and to manage the Unicron cluster. It is designed to be always available.

At any given moment all nodes are workers, meaning that all nodes can run scheduled jobs and asynchronous tasks, but only one of them is The Scheduler. If the scheduler node fails, another node replaces it in a few seconds automatically.

### Installation
Unicron saves its data on Redis, so we need a Redis server installed (just make sure you have persistent storage for Redis when using in production).
```
docker run --name=redis-unicron -d redis:alpine
```

Next you need a random key for initializing the Unicron cluster. We use this key to add new nodes to the cluster, or to recover a failed node. Without this key Unicron would not be able to decrypt the saved data, and all scheduled jobs will be lost.

Just generate a 16 char string with your preferred tool.
```
openssl rand -base64 16 | md5 | head -c16; echo
f5f86b9c043ed03a
```

Now you can start the first node using `layzeelab/unicron` Docker image.
```
docker run --name=unicron_01 --link=redis-unicron -p 8185:80 \
  -e "UNICRON_KEY=f5f86b9c043ed03a" \
  -e "TZ=Europe/Amsterdam" \
  -e "REDIS_HOST=redis-unicron" \
  -e "REDIS_PORT=6379" \
  -e "REDIS_DB=0" \
  -e "REDIS_PASSWORD=" \
  -e "EMAIL_FROM=example@gmail.com" \
  -e "SMTP_HOST=smtp.gmail.com" \
  -e "SMTP_PORT=587" \
  -e "SMTP_TLS=1" \
  -e "SMTP_USER=example@gmail.com" \
  -e "SMTP_PASSWORD=p4ssw0rd" \
  -d layzeelab/unicron
```
You can set optional SMTP environment variables to be able to receive emails from Unicron.
To add new nodes to the cluster you should use the same `UNICRON_KEY` and `REDIS_HOST` as the backend storage for new nodes.


### Development
`run_tests.sh` and `run_devel.sh` scripts can be used to test and run the development environment.

```
./run_tests.sh

============================= test session starts ==============================
platform linux -- Python 3.6.5, pytest-3.6.0, py-1.5.3, pluggy-0.6.0
rootdir: /var, inifile:
plugins: flake8-1.0.1, celery-4.1.1
collected 13 items
unicron/api.py .                                                         [ 30%]
unicron/scheduler.py .                                                   [ 38%]
unicron/worker.py .                                                      [ 46%]
unicron/routes/async.py .                                                [ 76%]
unicron/routes/job.py .                                                  [ 84%]
unicron/tasks/async.py .                                                 [ 92%]
unicron/tasks/job.py .                                                   [100%]
========================== 13 passed in 95.68 seconds ==========================
Cleaning up containers...
unicron-test
redis-unicron-test
```

`run_devel.sh` also starts the dev env and exposes the Unicron API on port `8185`.
```
./run_devel.sh

Successfully built 480dfe5cb6e2
Unicron is up!
API URL http://localhost:8185/api/
Press any key to clean up and quit dev environment.
```

### API

#### Job
Create a new job to post some data to a URL every minute, and send the result to your email and to your logs service (optional).
```
PAYLOAD='{
  "name": "MyJob",
  "schedule": "* * * * *",
  "http_url": "https://myservice/importanttask",
  "http_method": "post",
  "http_headers": {"Authorization": "xxxxxx"},
  "http_data": {"var1": "xxx", "var2": "yyy"},
  "email": "me@example.com",
  "hook_url": "http://myservice/mylogs",
  "hook_headers": {"Authorization": "Basic xxx"}
}'
curl -X POST -d "$PAYLOAD" http://localhost:8185/api/job/
```
Unicron encodes job information before saving in Redis, encryption is specially important if you use an unsecure or shared Redis server.

Instead of calling a URL you can set the job to run a shell command by adding `command` option into the payload.
```
PAYLOAD='{
  "name": "MyJob",
  "schedule": "0 0 * * *",
  "command": "/bin/sh /var/unicron/scripts/date.sh",
  "email": "me@example.com",
  "hook_url": "http://myservice/mylogs",
  "hook_headers": {"Authorization": "Basic xxx"}
}'
```

If the task is successful it returns the job ID:
```
{"success": true, "msg": "", "result": "51TYVmfJGgQGAmyc"}
```

Use the job ID to get the info from API:
```
curl http://localhost:8185/api/job/51TYVmfJGgQGAmyc
```

Or get all jobs:
```
curl http://localhost:8185/api/job/
```

To get results for one or all jobs in the past 24 hours:
```
curl http://localhost:8185/api/job/result/51TYVmfJGgQGAmyc
curl http://localhost:8185/api/job/result
```

To remove the scheduled job completely:
```
curl -X DELETE http://localhost:8185/api/job/51TYVmfJGgQGAmyc
```

#### Async
Unicron can also be used to run asynchronous tasks. To run a task immediately on the Unicron cluster, you need to create an async task instead of an scheduled job.
```
PAYLOAD='{
  "name": "MyAsyncTask",
  "http_url": "https://myservice/importanttask",
  "http_method": "get",
  "http_headers": {"Authorization": "xxxxxx"},
  "http_data": {"var1": "xxx", "var2": "yyy"},
  "email": "me@example.com",
  "hook_url": "http://myservice/mylogs",
  "hook_headers": {"Authorization": "Basic xxx"}
}'
curl -X POST -d "$PAYLOAD" http://localhost:8185/api/async/
```
You can also use a shell `command` instead of a URL. Using an email and http-hook is optional.

If adding the async task is successful it returns the task ID:
```
{"success": true, "msg": "", "result": "291ef0d7-bc08-4a54-8057-d600e5a2fe7d"}
```

To check the status/result of the task, use the ID returned by the previous call:
```
curl http://localhost:8185/api/async/291ef0d7-bc08-4a54-8057-d600e5a2fe7d

{
  "success": true,
  "msg": "",
  "result": {
    "status": "SUCCESS",
    "task_id": "291ef0d7-bc08-4a54-8057-d600e5a2fe7d",
    "traceback": null,
    "children": [],
    "result": {
      "success": true,
      "start": 1528506638.7152123,
      "end": 1528506641.3089178,
      "output": {
        "job_id": null,
        "status_code": 200,
        "text": "my task response body"
      }
    }
  }
}
```
`start` and `end` values are epoch timestamps.

If the task hasn't started or finished yet:
```
{
  "success": true,
  "msg": "",
  "result": {
    "task_id": "291ef0d7-bc08-4a54-8057-d600e5a2fe7d",
    "status": "PENDING",
    "result": null
  }
}
```

Possible states are:
```
PENDING: The task is waiting for execution.
STARTED: The task has been started.
RETRY: The task is to be retried, possibly because of failure.
FAILURE: The task raised an exception, or has exceeded the retry limit.
SUCCESS: The task executed successfully.
```

### Docker Image
Docker Image is available on Docker Hub [layzeelab/unicron](https://hub.docker.com/r/layzeelab/unicron/).

### License
GNU General Public License v3.0

See `LICENSE` to see the full text.
