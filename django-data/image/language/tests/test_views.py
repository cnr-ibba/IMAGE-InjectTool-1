#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 10:27:48 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import Client, TestCase
from django.urls import reverse, resolve

from common.tests import (
    GeneralMixinTestCase, FormMixinTestCase, InvalidFormMixinTestCase)
from uid.models import DictCountry, DictSpecie

from ..views import ListSpeciesView, UpdateSpeciesView
from ..forms import SpecieSynonymForm
from ..models import SpecieSynonym


class BaseTest(TestCase):
    fixtures = [
        "uid/user",
        "uid/dictcountry",
        "language/dictspecie",
        "language/speciesynonym",
    ]

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

    def create_synonym(self):
        """Create a synonym for testing"""

        # get a language from db
        self.language = DictCountry.objects.get(label="Italy")

        # get a specie from db
        self.specie = DictSpecie.objects.get(label="Bos taurus")

        # add a new speciesynonym obj
        synonym = SpecieSynonym(word="Mucca", language=self.language)
        synonym.save()
        synonym.refresh_from_db()

        return synonym


# GeneralTestCase contains test against a non logged user, and the default
# status
class ListSpeciesViewTest(GeneralMixinTestCase, BaseTest):
    """Test ListSpeciesView"""

    def setUp(self):
        # call base method
        super().setUp()

        self.url = reverse("language:species")
        self.response = self.client.get(self.url)

        # some attribs
        self.bos_url = reverse('language:species-update', kwargs={'pk': 1})
        self.ovis_url = reverse('language:species-update', kwargs={'pk': 2})

    def test_url_resolves_view(self):
        view = resolve('/language/species/')
        self.assertIsInstance(view.func.view_class(), ListSpeciesView)

    def test_content(self):
        """Assert species in list"""

        self.assertContains(self.response, "Bos taurus")
        self.assertContains(self.response, "Ovis aries")

    def test_contains_navigation_links(self):
        """Contain links to UpdateSpeciesView"""

        self.assertContains(self.response, 'href="{0}"'.format(self.bos_url))
        self.assertContains(self.response, 'href="{0}"'.format(self.ovis_url))

    def test_filter_by_language(self):
        """Testing views filtering by language"""

        country = "Italy"
        url = self.url + "?country={}".format(country)

        # get a response filtering by language
        response = self.client.get(url)

        # assert no data for Italy
        self.assertNotContains(response, 'href="{0}"'.format(self.bos_url))
        self.assertNotContains(response, 'href="{0}"'.format(self.ovis_url))

    def test_contains_navigation_links_with_parameters(self):
        """Contain links to UpdateSpeciesView with get parameters"""

        country = "United Kingdom"

        url = self.url + "?country={}".format(country)
        bos_url = self.bos_url + "?country={}".format(country)
        ovis_url = self.ovis_url + "?country={}".format(country)

        # get a response filtering by language
        response = self.client.get(url)

        self.assertContains(response, 'href="{0}"'.format(bos_url))
        self.assertContains(response, 'href="{0}"'.format(ovis_url))


class UpdateSpeciesViewTest(FormMixinTestCase, BaseTest):
    """A class to test language update species"""

    form_class = SpecieSynonymForm

    def setUp(self):
        """call base method"""
        super().setUp()

        self.url = reverse("language:species-update", kwargs={'pk': 1})
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/language/species/1/update/')
        self.assertIsInstance(view.func.view_class(), UpdateSpeciesView)

    def test_form_inputs(self):

        # total input is n of form fields + (CSRF) + 2 select
        self.assertContains(self.response, '<input', 2)
        self.assertContains(self.response, 'type="text"', 1)
        self.assertContains(self.response, '<select', 2)
        self.assertContains(self.response, "required disabled", 2)
        self.assertContains(self.response, 'name="word" value="Cattle"')

    # TODO: test not found species

    # TODO: test navigation links


# Here, I'm already tested the urls, csfr. So BaseTest
class SuccessfulUpdateSpeciesViewTest(BaseTest):
    def setUp(self):
        """call base method"""
        super().setUp()

        # create a synonym
        synonym = self.create_synonym()

        self.url = reverse(
            "language:species-update",
            kwargs={'pk': synonym.id}) + "?country=Italy"

        self.response = self.client.post(
            self.url,
            {'dictspecie': self.specie.id},
            follow=True)

    def test_redirect(self):
        url = reverse("language:species") + "?country=Italy"
        self.assertRedirects(self.response, url)

    def test_specie_updated(self):
        # get a speciesynonym object
        synonym = SpecieSynonym.objects.get(
            word="Mucca", language=self.language)

        self.assertEqual(synonym.dictspecie, self.specie)


class InvalidUpdateSpeciesViewTest(InvalidFormMixinTestCase, BaseTest):

    def setUp(self):
        """call base method"""
        super().setUp()

        # create a synonym
        synonym = self.create_synonym()

        self.url = reverse(
            "language:species-update",
            kwargs={'pk': synonym.id})

        self.response = self.client.post(self.url, {})

    def test_no_update(self):
        # get a speciesynonym object
        synonym = SpecieSynonym.objects.get(
            word="Mucca", language=self.language)

        self.assertIsNone(synonym.dictspecie)
