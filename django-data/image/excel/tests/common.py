#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 10:57:13 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from uid.models import Submission


class BaseExcelMixin():
    # import this file and populate database once
    fixtures = [
        'excel/dictspecie',
        'excel/speciesynonym',
        'excel/submission',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/organization',
        'uid/user',

    ]

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # track submission
        self.submission = Submission.objects.get(pk=1)
        self.submission_id = 1
