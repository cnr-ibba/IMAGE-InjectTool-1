#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 16:05:18 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from enum import Enum

# a constant for this module
OBO_URL = "http://purl.obolibrary.org/obo"


class EnumMixin():
    """Common methods for my Enum classes"""

    @classmethod
    def get_value(cls, member):
        """Get numerical representation of an Enum object"""

        return cls[member].value[0]

    @classmethod
    def get_value_display(cls, value):
        for el in cls:
            if el.value[0] == value:
                return el.value[1]
        return Exception("value %s not in %s" % (value, cls))


class ACCURACIES(EnumMixin, Enum):
    missing = (0, 'missing geographic information')
    country = (1, 'country level')
    region = (2, 'region level')
    precise = (3, 'precise coordinates')
    unknown = (4, 'unknown accuracy level')


# 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
class CONFIDENCES(EnumMixin, Enum):
    high = (0, 'High')
    good = (1, 'Good')
    medium = (2, 'Medium')
    low = (3, 'Low')
    curated = (4, 'Manually Curated')


# 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
# waiting: waiting to upload data (or process them!)
# loaded: data loaded into UID, can validate
# error: error in uploading data into UID or in submission
# ready: validated data ready for submission
# need_revision: validated data need checks before submission
# submitted: submitted to biosample
# completed: finalized submission with biosample id
class STATUSES(EnumMixin, Enum):
    waiting = (0, 'Waiting')
    loaded = (1, 'Loaded')
    submitted = (2, 'Submitted')
    error = (3, 'Error')
    need_revision = (4, 'Need Revision')
    ready = (5, "Ready")
    completed = (6, "Completed")


# 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
class DATA_TYPES(EnumMixin, Enum):
    cryoweb = (0, 'CryoWeb')
    template = (1, 'Template')
    crb_anim = (2, 'CRB-Anim')


# to deal with time units
class TIME_UNITS(EnumMixin, Enum):
    minutes = (0, "minutes")
    hours = (1, "hours")
    days = (2, "days")
    weeks = (3, "weeks")
    months = (4, "months")
    years = (5, "years")


# a list of a valid statuse for names
NAME_STATUSES = [
    'loaded',
    'ready',
    'need_revision',
    'submitted',
    'completed'
]


# get statuses
WAITING = STATUSES.get_value('waiting')
LOADED = STATUSES.get_value('loaded')
ERROR = STATUSES.get_value('error')
READY = STATUSES.get_value('ready')
NEED_REVISION = STATUSES.get_value('need_revision')
SUBMITTED = STATUSES.get_value('submitted')
COMPLETED = STATUSES.get_value('completed')

# get accuracy levels
MISSING = ACCURACIES.get_value('missing')
UNKNOWN = ACCURACIES.get_value('unknown')
PRECISE = ACCURACIES.get_value('precise')

# get different data sources types
CRYOWEB_TYPE = DATA_TYPES.get_value('cryoweb')
TEMPLATE_TYPE = DATA_TYPES.get_value('template')
CRB_ANIM_TYPE = DATA_TYPES.get_value('crb_anim')

# get different confidence statuses
GOOD = CONFIDENCES.get_value('good')
CURATED = CONFIDENCES.get_value('curated')

# get time units
YEARS = TIME_UNITS.get_value('years')
MONTHS = TIME_UNITS.get_value('months')
DAYS = TIME_UNITS.get_value('days')

# define sample storage types
SAMPLE_STORAGE_TYPES = [
    "ambient temperature",
    "cut slide",
    "frozen, -80 degrees Celsius freezer",
    "frozen, -20 degrees Celsius freezer",
    "frozen, liquid nitrogen",
    "frozen, vapor phase",
    "paraffin block",
    "RNAlater, frozen -20 degrees Celsius",
    "TRIzol, frozen",
    "paraffin block at ambient temperatures (+15 to +30 degrees Celsius)",
    "freeze dried"
]
