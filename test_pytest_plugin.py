# Copyright 2021 Jonathan Holloway <loadtheaccumulator@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software. If not, see <http://www.gnu.org/licenses/>.
#
"""Test glusto basic functionality"""
import time
import unittest
import pytest


class TestPyTestKafkavent(unittest.TestCase):
    """Glusto basics test class"""
    @classmethod
    def setUpClass(cls):
        """unittest standard setUpClass method
        Runs before all test_ methods in the class
        """
        # print("Setting Up Class: %s" % cls.__name__)

        pass

    def setUp(self):
        """unittest standard setUp method
        Runs before each test_ method
        """
        # print("Setting Up: %s" % self.id())

        pass

    def test_pass(self):
        time.sleep(2)
        self.assertEqual(True, True, 'this should have passed')

    def test_fail(self):
        self.assertEqual(True, False, "this should have failed")

    def test_fail2(self):
        self.assertEqual(True, False, "this should have also failed")

    @pytest.mark.skip(reason="skipping intentionally")
    def test_skip(self):
        self.assertEqual(True, False, "this should have failed")

    @pytest.mark.xfail(reason="always xfail")
    def test_xfail(self):
        self.assertEqual(True, False, "this should have xfailed")

    def tearDown(self):
        """Unittest tearDown override"""
        # print("Tearing Down: %s" % self.id())

        pass

    @classmethod
    def tearDownClass(cls):
        """unittest tearDownClass override"""
        # print("Tearing Down Class: %s" % cls.__name__)

        pass