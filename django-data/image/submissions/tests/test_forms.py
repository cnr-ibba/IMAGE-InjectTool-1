#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 16:55:56 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from ..forms import SubmissionForm, ReloadForm, UpdateSubmissionForm


class SubmissionFormTest(TestCase):
    def test_form_has_fields(self):
        form = SubmissionForm()
        expected = [
            'title',
            'description',
            'gene_bank_name',
            'gene_bank_country',
            'organization',
            'datasource_type',
            'datasource_version',
            'uploaded_file'
        ]
        actual = list(form.fields)
        self.assertSequenceEqual(expected, actual)


class ReloadFormTest(TestCase):
    def test_form_has_fields(self):
        form = ReloadForm()
        expected = [
            'datasource_type',
            'datasource_version',
            'uploaded_file',
            'agree_reload',
        ]
        actual = list(form.fields)
        self.assertSequenceEqual(expected, actual)


class UpdateSubmissionFormTest(TestCase):
    def test_form_has_fields(self):
        form = UpdateSubmissionForm()
        expected = [
            'title',
            'description',
            'gene_bank_name',
            'gene_bank_country',
            'organization',
            "datasource_type",
            "datasource_version",
        ]
        actual = list(form.fields)
        self.assertSequenceEqual(expected, actual)
