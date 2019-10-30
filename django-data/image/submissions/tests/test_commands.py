#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 11:17:12 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.core.management import call_command
from django.test import TestCase

from common.constants import LOADED
from uid.models import Submission, Name


class CommandsTestCase(TestCase):
    fixtures = [
        'uid/animal',
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/dictstage',
        'uid/dictuberon',
        'uid/organization',
        'uid/publication',
        'uid/sample',
        'uid/submission',
        'uid/user'
    ]

    def test_reset_submission(self):
        "Test biosample_submission command command."

        # mocking objects
        args = ["--submission", 1]
        opts = {}
        call_command('reset_submission', *args, **opts)

        # get submission
        submission_obj = Submission.objects.get(pk=1)

        # check submission.state changed
        self.assertEqual(submission_obj.status, LOADED)

        # check name status changed
        qs = Name.objects.filter(submission=submission_obj)

        for name in qs:
            self.assertEqual(name.status, LOADED)
