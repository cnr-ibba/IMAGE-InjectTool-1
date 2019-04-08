#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 14:35:36 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase
from django.utils.dateparse import parse_date

from .. import constants
from ..helpers import image_timedelta


class TestImageTimedelta(TestCase):
    """A class to test common.helpers.image_timedelta functions"""

    def test_years(self):
        t1 = parse_date("2019-03-27")
        t2 = parse_date("2018-03-27")

        years, units = image_timedelta(t1, t2)

        self.assertEqual(years, 1)
        self.assertEqual(units, constants.YEARS)

        with self.assertLogs('common.helpers', level="WARNING") as cm:
            # assert date inversion (returns None)
            years, units = image_timedelta(t2, t1)

        self.assertEqual(years, None)
        self.assertEqual(units, constants.YEARS)
        self.assertEqual(len(cm.output), 1)
        self.assertIn("t2>t1", cm.output[0])

    def test_months(self):
        t1 = parse_date("2019-03-27")
        t2 = parse_date("2019-01-27")

        months, units = image_timedelta(t1, t2)

        self.assertEqual(months, 2)
        self.assertEqual(units, constants.MONTHS)

    def test_days(self):
        t1 = parse_date("2019-03-27")
        t2 = parse_date("2019-03-20")

        days, units = image_timedelta(t1, t2)

        self.assertEqual(days, 7)
        self.assertEqual(units, constants.DAYS)

    def test_unknown_date(self):
        t1 = parse_date("2019-03-20")
        t2 = parse_date("1900-01-01")

        with self.assertLogs('common.helpers', level="WARNING") as cm:
            years, units = image_timedelta(t1, t2)

        self.assertIsNone(years)
        self.assertEqual(units, constants.YEARS)
        self.assertEqual(len(cm.output), 1)
        self.assertIn("Ignoring one date", cm.output[0])

    def test_null_date(self):
        t1 = None
        t2 = parse_date("1900-01-01")

        with self.assertLogs('common.helpers', level="WARNING") as cm:
            years, units = image_timedelta(t1, t2)

        self.assertIsNone(years)
        self.assertEqual(units, constants.YEARS)
        self.assertEqual(len(cm.output), 1)
        self.assertIn("One date is NULL", cm.output[0])