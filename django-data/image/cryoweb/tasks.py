#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 11:33:09 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Inspired from

http://docs.celeryproject.org/en/latest/tutorials/task-cookbook.html

"""

import time
from contextlib import contextmanager

import redis
from celery import task
from celery.five import monotonic
from celery.utils.log import get_task_logger
from image_app.models import Submission

logger = get_task_logger(__name__)

LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes


@contextmanager
def redis_lock(lock_id, blocking=False):
    REDIS_CLIENT = redis.StrictRedis(host='redis', port=6379, db=0)

    timeout_at = monotonic() + LOCK_EXPIRE - 3

    lock = REDIS_CLIENT.lock(lock_id, timeout=LOCK_EXPIRE)
    status = lock.acquire(blocking=blocking)

    try:
        yield status

    finally:
        # we take advantage of using add() for atomic locking
        if monotonic() < timeout_at and status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            lock.release()


@task(bind=True)
def import_from_cryoweb(self, submission_id, blocking=True):
    # The cache key consists of the task name and the MD5 digest
    # of the feed URL.
    lock_id = 'ImportFromCryoWeb'
    logger.info("Start import from cryoweb for submission: %s" % submission_id)

    # get a submission object
    submission = Submission.objects.get(pk=submission_id)

    # get statuses
    loaded = Submission.STATUSES.get_value('loaded')

    # forcing blocking cndition: Wait until a get a lock object
    with redis_lock(lock_id, blocking=blocking) as acquired:
        if acquired:
            # do some stuff
            time.sleep(60)

            # TODO: catch exception and write it into submission.errors

            # modify database status
            logger.debug("Updating submission %s" % (submission_id))

            message = "Cryoweb import completed for submission: %s" % (
                submission_id)

            submission.message = message
            submission.status = loaded
            submission.save()

            logger.info(message)

            # always return something
            return "success"

    logger.warning(
        "Cryoweb import already running!")