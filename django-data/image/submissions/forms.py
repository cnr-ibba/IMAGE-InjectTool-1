#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 15:51:05 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import forms

from image_app.models import Submission


class SubmissionForm(forms.ModelForm):
    # the request is now available, add it to the instance data
    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')

        super(SubmissionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Submission
        fields = (
            'title',
            'description',
            'gene_bank_name',
            'gene_bank_country',
            'datasource_type',
            'datasource_version',
            'uploaded_file'
        )