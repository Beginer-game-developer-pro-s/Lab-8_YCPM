#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simulate_booking.py
Lab 8 - Simulation of the MedBook core business logic
------------------------------------------------------------
This is a "sample software project" implementing DIRECTLY some of the
requirements specified in earlier labs, demonstrating that a
requirements document can be "traced all the way to running code":

  - FR-003 (Book appointment)      -> BookingSystem.book()
  - FR-004 (Cancel appointment, >=2h) -> BookingSystem.cancel()
  - FR-008 (Drug interaction warning) -> BookingSystem.prescribe()
  - NFR-007 (Booking conflict safety) -> uniqueness check inside book()

Run: python3 simulate_booking.py
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta


class BookingConflictError(Exception):
    """Raised when a booking conflict is detected - implements NFR-007."""


class CancellationPolicyError(Exception):
    """Raised when a cancellation violates the 2-hour policy - implements FR-004."""


@dataclass
class Appointment:
    patient: str
    doctor: str
    slot: datetime
    status: str = "pending_confirmation"


@dataclass
class Patient:
    name: str
    allergies: set = field(default_factory=set)


class BookingSystem:
    """Core booking logic - implements FR-003, FR-004, FR-008, NFR-007."""

    def __init__(self):
        self._appointments: list[Appointment] = []
        self._patients: dict[str, Patient] = {}

    def register_patient(self, name, allergies=None):
        self._patients[name] = Patient(name, set(allergies or []))

    # ---- FR-003 + NFR-007 --------------------------------------------
    def book(self, patient, doctor, slot: datetime) -> Appointment:
        """Book an appointment; reject if the doctor already has a
        conflicting slot (NFR-007)."""
        for appt in self._appointments:
            if appt.doctor == doctor and appt.slot == slot and appt.status != "cancelled":
                raise BookingConflictError(
                    f"Doctor {doctor} already has an appointment at {slot} "
                    f"(violates NFR-007)")
        appt = Appointment(patient=patient, doctor=doctor, slot=slot)
        self._appointments.append(appt)
        return appt

    # ---- FR-004 ---------------------------------------------------------
    def cancel(self, appt: Appointment, now: datetime):
        """Cancel an appointment; reject if less than 2 hours remain
        before the slot (FR-004)."""
        if appt.slot - now < timedelta(hours=2):
            raise CancellationPolicyError(
                "Cannot cancel within 2 hours of the appointment (FR-004 policy)")
        appt.status = "cancelled"

    # ---- FR-008 -----------------------------------------------------------
    def prescribe(self, patient_name: str, drug: str, known_interactions: dict):
        """
        Prescribe a drug; warns if it conflicts with the patient's known
        allergy history (FR-008 - related to HZ-001 in the safety case).
        `known_interactions`: dict {drug_name: [list of conflicting drugs/substances]}
        """
        patient = self._patients.get(patient_name)
        if not patient:
            raise ValueError(f"Patient {patient_name} not found")
        conflicts = known_interactions.get(drug, [])
        risky = patient.allergies.intersection(conflicts) | (
            {drug} if drug in patient.allergies else set())
        if risky:
            return {"warning": True, "details": f"Drug '{drug}' conflicts with: {risky}"}
        return {"warning": False, "details": "No conflict detected"}


def demo():
    sys_ = BookingSystem()
    sys_.register_patient("John Doe", allergies={"Penicillin"})

    slot = datetime(2026, 8, 1, 9, 0)
    appt1 = sys_.book("John Doe", "Dr. Robert Tran", slot)
    print(f"[OK] Booking successful: {appt1}")

    # Simulate TC-002: booking the same slot -> must be rejected
    try:
        sys_.book("Jane Roe", "Dr. Robert Tran", slot)
        print("[FAIL] Conflict was NOT detected - VIOLATES NFR-007!")
    except BookingConflictError as e:
        print(f"[OK] Conflict correctly blocked per NFR-007: {e}")

    # Simulate TC-004: cancel within 2h -> must be rejected
    try:
        sys_.cancel(appt1, now=slot - timedelta(minutes=30))
        print("[FAIL] Cancellation within 2h was allowed - VIOLATES FR-004!")
    except CancellationPolicyError as e:
        print(f"[OK] Late cancellation correctly blocked per FR-004: {e}")

    # Simulate TC-005: drug interaction warning
    interactions = {"Amoxicillin": ["Penicillin"]}
    result = sys_.prescribe("John Doe", "Amoxicillin", interactions)
    print(f"[OK] Prescription check result (FR-008): {result}")


if __name__ == "__main__":
    demo()
