#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 16:25:39 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from common.constants import (
    WAITING, LOADED, ERROR, READY, NEED_REVISION, SUBMITTED, COMPLETED)


class SubmissionStatusMixin():
    """Test response with different submission statuses"""

    def test_waiting(self):
        """Test waiting statuses return to submission detail"""

        # update statuses
        self.submission.status = WAITING
        self.submission.save()

        # test redirect
        response = self.client.get(self.url)
        self.assertRedirects(response, self.redirect_url)

    def test_loaded(self):
        """Test loaded status"""

        # force submission status
        self.submission.status = LOADED
        self.submission.save()

        # test no redirect
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_submitted(self):
        """Test submitted status"""

        # force submission status
        self.submission.status = SUBMITTED
        self.submission.save()

        # test redirect
        response = self.client.get(self.url)
        self.assertRedirects(response, self.redirect_url)

    def test_error(self):
        """Test error status"""

        # force submission status
        self.submission.status = ERROR
        self.submission.save()

        # test no redirect
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_need_revision(self):
        """Test need_revision status"""

        # force submission status
        self.submission.status = NEED_REVISION
        self.submission.save()

        # test no redirect
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_ready(self):
        """Test ready status"""

        # force submission status
        self.submission.status = READY
        self.submission.save()

        # test no redirect
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_completed(self):
        """Test completed status"""

        # force submission status
        self.submission.status = COMPLETED
        self.submission.save()

        # test no redirect
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)