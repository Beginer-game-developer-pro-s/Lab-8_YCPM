#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_safety_scenarios.py
Lab 8 - Automated tests mapped to test_cases.csv
--------------------------------------------------------
Each test method below implements one row from
datasets/test_cases.csv, demonstrating the complete chain:
    requirement (FR/NFR) -> test case (TC) -> automated test code

Run:  python3 -m unittest test_safety_scenarios.py -v
"""
import unittest
from datetime import datetime, timedelta

from simulate_booking import (
    BookingSystem, BookingConflictError, CancellationPolicyError,
)

SLOT = datetime(2026, 8, 1, 9, 0)


class TestSafetyScenarios(unittest.TestCase):

    def setUp(self):
        self.sys = BookingSystem()
        self.sys.register_patient("John Doe", allergies={"Penicillin"})

    def test_TC001_booking_succeeds(self):
        """TC-001: booking succeeds with an available time slot -> FR-003."""
        appt = self.sys.book("John Doe", "Dr. B", SLOT)
        self.assertEqual(appt.status, "pending_confirmation")

    def test_TC002_booking_fails_on_conflicting_slot(self):
        """TC-002: reject booking on an already-taken slot -> FR-003 / NFR-007."""
        self.sys.book("John Doe", "Dr. B", SLOT)
        with self.assertRaises(BookingConflictError):
            self.sys.book("Someone Else", "Dr. B", SLOT)

    def test_TC003_cancel_more_than_2h_before_succeeds(self):
        """TC-003: valid cancellation with more than 2h remaining -> FR-004."""
        appt = self.sys.book("John Doe", "Dr. B", SLOT)
        self.sys.cancel(appt, now=SLOT - timedelta(hours=3))
        self.assertEqual(appt.status, "cancelled")

    def test_TC004_cancel_within_2h_rejected(self):
        """TC-004: reject cancellation within 2h of the appointment -> FR-004."""
        appt = self.sys.book("John Doe", "Dr. B", SLOT)
        with self.assertRaises(CancellationPolicyError):
            self.sys.cancel(appt, now=SLOT - timedelta(minutes=30))

    def test_TC005_drug_interaction_warning(self):
        """TC-005: warning shown for a drug conflicting with allergy history -> FR-008 / HZ-001."""
        result = self.sys.prescribe(
            "John Doe", "Amoxicillin", {"Amoxicillin": ["Penicillin"]})
        self.assertTrue(result["warning"])

    def test_TC005b_no_false_positive_when_safe(self):
        """False-positive check: a safe drug must not trigger a warning."""
        result = self.sys.prescribe(
            "John Doe", "Paracetamol", {"Amoxicillin": ["Penicillin"]})
        self.assertFalse(result["warning"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
