#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 16:11:23 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from django.test import Client, TestCase
from django.urls import reverse

from image_app.models import User


class SiteTestCase(TestCase):
    def setUp(self):
        # create a testuser
        User.objects.create_user(
            username='test',
            password='test',
            email="test@test.com")

        self.client = Client()
        self.client.login(username='test', password='test')

    def tearDown(self):
        # remove user
        u = User.objects.get(username='test')
        u.delete()

    def test_homepage(self):
        """Testing home"""

        response = self.client.get(reverse('index'))

        # Check that the response is 200
        self.assertEqual(response.status_code, 200)
