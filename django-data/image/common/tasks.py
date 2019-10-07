#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 16:42:24 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis

from contextlib import contextmanager
from celery.five import monotonic
from celery.utils.log import get_task_logger

from django.conf import settings
from django.utils import timezone
from django.core import management

from image.celery import app as celery_app
from submissions.helpers import send_message
from validation.helpers import construct_validation_message
from common.constants import NEED_REVISION, ERROR

# Lock expires in 10 minutes
LOCK_EXPIRE = 60 * 10

# Get an instance of a logger
logger = get_task_logger(__name__)


class BaseTask(celery_app.Task):
    """Base class to celery tasks. Define logs for on_failure and debug_task"""

    description = None
    action = None

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

    def debug_task(self):
        # this does't throw an error when debugging a task called with run()
        if self.request_stack:
            logger.debug('Request: {0!r}'.format(self.request))


# https://stackoverflow.com/a/51429597
@celery_app.task(bind=True, base=BaseTask)
def clearsessions(self):
    """Cleanup expired sessions by using Django management command."""

    logger.info("Clearing session with celery...")

    # debugging instance
    self.debug_task()

    # calling management command
    management.call_command("clearsessions", verbosity=1)

    # debug
    logger.info("Sessions cleaned!")

    return "Session cleaned with success"


class BatchFailurelMixin():
    """Common mixin for batch task failure. Need to setup ``batch_type``
    (update/delete) and ``model_type`` (animal/sample)
    """

    batch_type = None
    model_type = None
    submission_cls = None

    # Ovverride default on failure method
    # This is not a failed validation for a wrong value, this is an
    # error in task that mean an error in coding
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        submission_id = args[0]

        logger.error(
            ("%s called with %s" % (self.name, args))
        )

        # get submission object
        submission_obj = self.submission_cls.objects.get(pk=submission_id)

        # mark submission with ERROR
        submission_obj.status = ERROR
        submission_obj.message = (
            "Error in %s batch %s: %s" % (
                self.model_type, self.batch_type, str(exc)))
        submission_obj.save()

        send_message(submission_obj)

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in %s batch %s for submission: %s" % (
                self.model_type, self.batch_type, submission_obj.id),
            ("Something goes wrong in batch %s for %ss. Please report "
             "this to InjectTool team\n\n %s" % (
                self.model_type, self.batch_type, str(einfo))),
        )

        # TODO: submit mail to admin


class BatchUpdateMixin:
    """Mixin to do batch update of fields to fix validation"""

    item_cls = None
    submission_cls = None

    def batch_update(self, submission_id, ids, attribute):
        for id_, value in ids.items():
            if value == '' or value == 'None':
                value = None

            item_object = self.item_cls.objects.get(pk=id_)

            if getattr(item_object, attribute) != value:
                setattr(item_object, attribute, value)
                item_object.save()

                # update name object
                item_object.name.last_changed = timezone.now()
                item_object.name.save()

        # Update submission
        submission_obj = self.submission_cls.objects.get(pk=submission_id)
        submission_obj.status = NEED_REVISION
        submission_obj.message = "Data updated, try to rerun validation"
        submission_obj.save()

        send_message(
            submission_obj, construct_validation_message(submission_obj)
        )


@contextmanager
def redis_lock(lock_id, blocking=False, expire=True):
    """
    This function get a lock relying on a lock name and other status. You
    can describe more process using the same lock name and give exclusive
    access to one of them.

    Args:
        lock_id (str): the name of the lock to take
        blocking (bool): if True, we wait until we have the block, if False
            we returns immediately False
        expire (bool): if True, lock will expire after LOCK_EXPIRE timeout,
            if False, it will persist until lock is released

    Returns:
        bool: True if lock acquired, False otherwise
    """

    # read parameters from settings
    REDIS_CLIENT = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB)

    # this will be the redis lock
    lock = None

    # timeout for the lock (if expire condition)
    timeout_at = monotonic() + LOCK_EXPIRE - 3

    if expire:
        lock = REDIS_CLIENT.lock(lock_id, timeout=LOCK_EXPIRE)

    else:
        lock = REDIS_CLIENT.lock(lock_id, timeout=None)

    status = lock.acquire(blocking=blocking)

    try:
        logger.debug("lock %s acquired is: %s" % (lock_id, status))
        yield status

    finally:
        # we take advantage of using add() for atomic locking
        # don't release the lock if we didn't acquire it
        if status and ((monotonic() < timeout_at and expire) or not expire):
            logger.debug("Releasing lock %s" % lock_id)
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # if no timeout and lock is taken, release it
            lock.release()
