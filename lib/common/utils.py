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

import time
import string
import random
import json
import redis
import smtplib
import hashlib
import base64
from flask import Response
from functools import wraps
from unicron.common import celeryconfig, config
from celery.task.control import revoke
from email.message import Message
from requests import Request, Session
from Crypto.Cipher import AES
from Crypto import Random


def task_response(func):
    '''Decorator for setting Celery task responses'''
    @wraps(func)
    def f_wrapper(*args, **kwargs):
        time_start = time.time()
        try:
            revoke(args[0].request.id, terminate=False)
            result = func(*args, **kwargs)
            return {
                'success': True,
                'output': result,
                'start': time_start,
                'end': time.time()}
        except Exception as e:
            return {
                'success': False,
                'output': str(e),
                'start': time_start,
                'end': time.time()}
    return f_wrapper


def api_response(func):
    '''Decorator for setting Flask API responses'''
    @wraps(func)
    def f_wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return send_resp({'success': True, 'msg': '', 'result': result})
        except Exception as e:
            return send_resp({'success': False, 'msg': str(e)}, statuscode=500)
    return f_wrapper


def convert2str(obj):
    if isinstance(obj, (bytes, bytearray)):
        return obj.decode()
    if isinstance(obj, dict):
        objnew = {}
        for key, value in obj.items():
            if isinstance(key, (bytes, bytearray)):
                key = key.decode()
            if isinstance(value, (bytes, bytearray)):
                value = value.decode()
            if isinstance(value, dict):
                value = convert2str(value)
            objnew[key] = value
        return objnew
    return obj


def send_resp(payload, statuscode=200):
    return Response(
        json.dumps(convert2str(payload)),
        status=statuscode,
        mimetype='application/json')


def remove_prefix(s, prefix):
    return s[len(prefix):] if s.startswith(prefix) else s


def redis_connect():
    return redis.StrictRedis(
        host=celeryconfig.redis_host,
        port=celeryconfig.redis_port,
        db=celeryconfig.redis_db,
        password=celeryconfig.redis_password)


def genrandkey(keysize=16):
    return ''.join(random.choice(
        string.ascii_letters + string.digits) for _ in range(keysize))


def encrypt(raw):
    # pad the input string
    raw = raw + (16 - len(raw) % 16) * chr(16 - len(raw) % 16)
    # encrypt the padded raw string
    key = hashlib.sha256(config.key.encode('utf-8')).digest()
    iv = Random.new().read(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(raw))


def decrypt(enc):
    key = hashlib.sha256(config.key.encode('utf-8')).digest()
    enc = base64.b64decode(enc)
    iv = enc[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    raw = cipher.decrypt(enc[16:])
    # remove the padding from the text string
    return raw[:-ord(raw[len(raw) - 1:])]


def verify_cluster():
    '''confirm cluster key or generate a new lock for fresh cluster'''
    rds = redis_connect()
    c_lock = rds.get(config.cluster_lock)
    if c_lock is None:
        # this is a new cluster
        c_lock = genrandkey(16)
        return rds.set(config.cluster_lock, convert2str(encrypt(c_lock)))
    try:
        c_lock = decrypt(convert2str(c_lock))
        if len(c_lock) != 16:
            raise
    except Exception:
        raise Exception("wrong cluster key")


def send_email(subject, result, email):
    if not config.email_enabled or len(email) == 0 or type(result) is not dict:
        return
    try:
        body = "<html><body>"
        for k, v in result.items():
            body = body + str(k) + ": " + str(v) + "<br>"
        body = body + "</body></html>"
        msg = Message()
        msg.add_header('Content-Type', 'text/html')
        msg.set_payload(body, charset="utf-8")
        msg['Subject'] = subject
        msg['From'] = config.email_from
        msg['To'] = email
        s = smtplib.SMTP(config.smtp_host, config.smtp_port)
        s.ehlo()
        if config.smtp_tls:
            s.starttls()
        if len(config.smtp_user) > 0 and len(config.smtp_password) > 0:
            s.login(config.smtp_user, config.smtp_password)
        s.sendmail(msg['From'], [msg['To']], msg.as_string())
        s.quit()
    except Exception:
        raise


def call_url(url, method, data, headers):
    if len(url) == 0:
        return None
    s = Session()
    req = Request(method, url, data=data, headers=headers)
    prepped = s.prepare_request(req)
    return s.send(prepped)
