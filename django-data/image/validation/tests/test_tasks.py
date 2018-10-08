#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:39:21 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase

from image_app.models import Submission

from ..tasks import validate_submission

# get available statuses
READY = Submission.STATUSES.get_value('ready')


class ValidateSubmissionTest(TestCase):
    fixtures = [
        "submissions/user",
        "submissions/dictcountry",
        "submissions/dictrole",
        "submissions/organization",
        "submissions/submission"
    ]

    # TODO: remove unuseful stuff and test a real case
    @patch("validation.tasks.sleep")
    def test_validate_submission(self, my_sleep):
        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = validate_submission(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # TODO: check submission status and message
        submission = Submission.objects.get(pk=1)

        # check submission.state changed
        self.assertEqual(submission.status, READY)
        self.assertEqual(
            submission.message,
            "Submission validated with success")