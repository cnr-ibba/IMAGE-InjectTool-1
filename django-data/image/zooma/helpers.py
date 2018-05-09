#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 15:49:04 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

Functions adapted from Jun Fan misc.py and use_zooma.py python scripts
"""

import re
import logging

import requests

from .constants import ZOOMA_URL, ONTOLOGIES


# Get an instance of a logger
logger = logging.getLogger(__name__)


def to_camel_case(input_str):
    """
    Convert a string using CamelCase convention
    """

    input_str = input_str.replace("_", " ")
    components = input_str.split(' ')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0].lower() + ''.join(x.title() for x in components[1:])


def from_camel_case(lower_camel):
    """
    Split a lower camel case string in words
    https://stackoverflow.com/a/1176023
    """

    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', lower_camel)
    return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1).lower()


def useZooma(term, category):
    # replacing spaces with +
    newTerm = term.replace(" ", "+")

    # defining params
    # TODO: can we focus the request to a specific endpoint (eg, why I need to
    # search into EPO for countries?)
    params = {
        'propertyValue': newTerm,
        'filter': "required:[ena],ontologies:[%s]" % (",".join(ONTOLOGIES))
    }

    category = from_camel_case(category)

    if category == "species":  # necessary if
        category = "organism"

    highResult = {}
    goodResult = {}
    result = {}

    # debug
    logger.debug("Calling zooma with %s" % (params))

    request = requests.get(ZOOMA_URL, params=params)

    # print (json.dumps(request.json(), indent=4, sort_keys=True))
    logger.debug(request)

    # read results
    results = request.json()

    # a warn
    if len(results) > 1:
        logger.warn("Got %s results for %s" % (len(results), params))

        for elem in results:
            logger.warn(elem['annotatedProperty'])

    for elem in results:
        detectedType = elem['annotatedProperty']['propertyType']

        # the type must match the given one or be null
        if (detectedType is None or detectedType == category):
            confidence = elem['confidence'].lower()
            propertyValue = elem['annotatedProperty']['propertyValue']
            semanticTag = elem['_links']['olslinks'][0]['semanticTag']

            # potential useful data: ['_links']['olslinks'][0]['href']:
            # https://www.ebi.ac.uk/ols/api/terms?iri=http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FUBERON_0002106
            if (confidence == "high"):
                highResult[propertyValue] = semanticTag
                logger.debug(
                    "got '%s' for '%s' with 'high' confidence" % (
                            semanticTag, newTerm))

            elif (confidence == "good"):
                goodResult[propertyValue] = semanticTag
                logger.debug(
                    "got '%s' for '%s' with 'good' confidence" % (
                            semanticTag, newTerm))

            else:
                logger.debug(
                    "Ignoring '%s' for '%s' since confidence is '%s'" % (
                            semanticTag, newTerm, confidence))

            # if we have a low confidence, don't take the results
            # else: #  medium/low

    # HINT: is useful?
    result['type'] = category

    # TODO: check if the annotation is useful (eg throw away GAZ for a specie)

    # TODO: is not clear if I have more than one result. For what I understand
    # or I have a result or not
    if len(highResult) > 0:
        result['confidence'] = 'High'
        for value in highResult:
            result['text'] = value
            result['ontologyTerms'] = highResult[value]
            return result

    if len(goodResult) > 0:
        result['confidence'] = 'Good'
        for value in goodResult:
            result['text'] = value
            result['ontologyTerms'] = goodResult[value]
            return result

    # no results is returned with low or medium confidence
    logger.warn("No result returned for %s" % (newTerm))
