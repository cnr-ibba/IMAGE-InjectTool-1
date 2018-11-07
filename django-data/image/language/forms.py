#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  7 14:38:51 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import forms

from image_app.models import DictCountry

from .models import SpecieSynonim


class SpecieSynonimForm(forms.ModelForm):
    word = forms.CharField(disabled=True)

    language = forms.ModelChoiceField(
        DictCountry.objects.all(), disabled=True)

    class Meta:
        model = SpecieSynonim
        fields = ('word', 'language', 'dictspecie')
