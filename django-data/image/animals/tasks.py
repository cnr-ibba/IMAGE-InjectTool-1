#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 16:38:37 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger
import asyncio

from common.constants import ERROR, LOADED, STATUSES
from common.helpers import send_message_to_websocket
from image.celery import app as celery_app, MyTask
from image_app.models import Animal, Submission
from submissions.helpers import send_message
from validation.helpers import construct_validation_message

# Get an instance of a logger
logger = get_task_logger(__name__)


class BatchUpdateAnimals(MyTask):
    name = "Batch update animals"
    description = """Batch update of field in animals"""

    # Ovverride default on failure method
    # This is not a failed validation for a wrong value, this is an
    # error in task that mean an error in coding
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        # get submission object
        submission_obj = Submission.objects.get(pk=args[0])

        # mark submission with ERROR
        submission_obj.status = ERROR
        submission_obj.message = ("Error in batch update for animals: %s"
                                  % (str(exc)))
        submission_obj.save()

        asyncio.get_event_loop().run_until_complete(
            send_message_to_websocket(
                {
                    'message': STATUSES.get_value_display(ERROR),
                    'notification_message': submission_obj.message
                },
                args[0]
            )
        )

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in batch update for animals: %s" % (args[0]),
            ("Something goes wrong  in batch update for animals. Please report "
             "this to InjectTool team\n\n %s" % str(einfo)),
        )

        # TODO: submit mail to admin

    def run(self, submission_id, animal_ids, attribute):
        """a function to upload data into UID"""

        logger.info(submission_id)
        logger.info(animal_ids)
        logger.info(attribute)
        logger.info("Start batch update for animals")

        for animal_id, value in animal_ids.items():
            animal = Animal.objects.get(pk=animal_id)
            setattr(animal, attribute, value)
            animal.save()

        # Update submission
        submission_obj = Submission.objects.get(pk=submission_id)
        submission_obj.status = LOADED
        submission_obj.message = "Data updated, try to rerun validation"
        submission_obj.save()

        send_message(
            submission_obj, construct_validation_message(submission_obj)
        )
        return 'success'


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(BatchUpdateAnimals)
