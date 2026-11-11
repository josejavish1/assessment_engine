"""Unit test suite for WorkforceSegmentationResolver (SR 11-7 / Bayesian Precedence)."""

from __future__ import annotations

from assessment_engine.domain.actuarial.workforce_segmentation import (
    SegmentationSourceType,
    WorkforceProfile,
    WorkforceSegmentationResolver,
)


def test_level_1_direct_interview_declarations() -> None:
    """Verifies that direct interview declarations take highest precedence."""
    telemetry = {
        "interview_workforce_declarations": {
            "corporate_seats": 1200,
            "shared_terminals": 800,
            "annual_refresh_units": 350,
            "hours_per_refresh": 3.5,
            "it_support_hourly_rate": 45.0,
        }
    }
    profile = WorkforceSegmentationResolver.resolve(
        total_headcount=3900,
        client_telemetry=telemetry,
    )

    assert isinstance(profile, WorkforceProfile)
    assert profile.source_type == SegmentationSourceType.EMPIRICAL_INTERVIEW_GROUND_TRUTH
    assert profile.total_headcount == 3900
    assert profile.corporate_seats == 1200
    assert profile.shared_operational_edge_terminals == 800
    assert profile.deskless_field_workers == 1900
    assert profile.annual_refresh_units == 350
    assert profile.annual_toil_hours == 1225.0
    assert profile.annual_toil_cost == 55125.0
    assert profile.confidence_score == 0.95
    assert (
        profile.corporate_seats
        + profile.shared_operational_edge_terminals
        + profile.deskless_field_workers
        == profile.total_headcount
    )


def test_level_1_interview_corpus_arithmetic_inference() -> None:
    """Verifies arithmetic inference from qualitative English interview notes (renewals × lifespan)."""
    telemetry = {
        "interview_notes": (
            "The annual refresh of approximately 350 laptops across a fleet total of 1,200 "
            "workstations requires 3.5 hours of manual technician effort per unit. "
            "Across the production facilities, there are more than 800 shared terminals."
        )
    }
    industry_profile = {
        "industry": "Heavy Manufacturing",
        "workforce_digital_profile": {
            "typical_it_support_hourly_rate": 45.0,
            "primary_disruption_driver": "PLANT_DISPATCH_AND_LOGISTICS",
        },
    }
    profile = WorkforceSegmentationResolver.resolve(
        total_headcount=3900,
        client_telemetry=telemetry,
        industry_profile=industry_profile,
    )

    assert profile.source_type == SegmentationSourceType.EMPIRICAL_INTERVIEW_GROUND_TRUTH
    assert profile.corporate_seats == 1200
    assert profile.shared_operational_edge_terminals == 800
    assert profile.deskless_field_workers == 1900
    assert profile.annual_refresh_units == 350
    assert profile.annual_toil_hours == 1225.0
    assert profile.annual_toil_cost == 55125.0
    assert profile.confidence_score == 0.92
    assert profile.primary_disruption_driver == "PLANT_DISPATCH_AND_LOGISTICS"


def test_level_2_verified_audited_regulatory_filing() -> None:
    """Verifies Level 2 extraction when no interview data is available."""
    telemetry = {
        "regulatory_filings": {
            "corporate_workforce": 600,
            "shared_terminals": 200,
            "citation": "Audited Non-Financial Information Statement (FY2024)",
        }
    }
    profile = WorkforceSegmentationResolver.resolve(
        total_headcount=2000,
        client_telemetry=telemetry,
    )

    assert profile.source_type == SegmentationSourceType.VERIFIED_AUDITED_FILING
    assert profile.corporate_seats == 600
    assert profile.shared_operational_edge_terminals == 200
    assert profile.deskless_field_workers == 1200
    assert profile.confidence_score == 0.90
    assert "Non-Financial Information Statement" in profile.provenance_citation


def test_level_3_pre_flight_web_intelligence_osint() -> None:
    """Verifies Level 3 extraction from client_intelligence web discovery."""
    intel = {
        "profile": {
            "workforce_intelligence": {
                "corporate_workforce": 400,
                "shared_edge_terminals": 100,
                "evidence_citation": "LinkedIn Workforce Insights & Public Register",
            }
        }
    }
    profile = WorkforceSegmentationResolver.resolve(
        total_headcount=1000,
        client_intelligence=intel,
    )

    assert profile.source_type == SegmentationSourceType.DISCOVERED_PUBLIC_OSINT
    assert profile.corporate_seats == 400
    assert profile.shared_operational_edge_terminals == 100
    assert profile.deskless_field_workers == 500
    assert profile.confidence_score == 0.80


def test_level_4_bayesian_sector_prior_heavy_manufacturing() -> None:
    """Verifies Level 4 fallback for heavy manufacturing industry profile."""
    industry_profile = {
        "industry": "Heavy Manufacturing",
        "workforce_digital_profile": {
            "corporate_seat_ratio": 0.25,
            "shared_operational_edge_ratio": 0.15,
            "deskless_field_ratio": 0.60,
            "work_make_up_elasticity": 0.30,
            "annual_endpoint_refresh_rate": 0.285,
            "hours_per_manual_refresh": 3.5,
            "typical_it_support_hourly_rate": 45.0,
            "primary_disruption_driver": "PLANT_DISPATCH_AND_LOGISTICS",
        },
    }
    profile = WorkforceSegmentationResolver.resolve(
        total_headcount=4000,
        industry_profile=industry_profile,
    )

    assert profile.source_type == SegmentationSourceType.ESTIMATED_SECTOR_BASELINE
    assert profile.corporate_seats == 1000  # 25% of 4000
    assert profile.shared_operational_edge_terminals == 600  # 15% of 4000
    assert profile.deskless_field_workers == 2400  # 60% of 4000
    assert profile.confidence_score == 0.65
    assert profile.primary_disruption_driver == "PLANT_DISPATCH_AND_LOGISTICS"
    assert (
        profile.corporate_seats
        + profile.shared_operational_edge_terminals
        + profile.deskless_field_workers
        == profile.total_headcount
    )


def test_level_4_bayesian_sector_prior_banking() -> None:
    """Verifies Level 4 fallback for banking (0% deskless workers)."""
    banking_profile = {
        "industry": "Banking",
        "workforce_digital_profile": {
            "corporate_seat_ratio": 0.95,
            "shared_operational_edge_ratio": 0.05,
            "deskless_field_ratio": 0.00,
            "work_make_up_elasticity": 0.15,
            "annual_endpoint_refresh_rate": 0.333,
            "hours_per_manual_refresh": 2.0,
            "typical_it_support_hourly_rate": 65.0,
            "primary_disruption_driver": "TRANSACTION_CLEARING_AND_TRADING",
        },
    }
    profile = WorkforceSegmentationResolver.resolve(
        total_headcount=3000,
        industry_profile=banking_profile,
    )

    assert profile.source_type == SegmentationSourceType.ESTIMATED_SECTOR_BASELINE
    assert profile.corporate_seats == 2850  # 95% of 3000
    assert profile.shared_operational_edge_terminals == 150  # 5% of 3000
    assert profile.deskless_field_workers == 0  # 0% deskless in fintech
    assert profile.primary_disruption_driver == "TRANSACTION_CLEARING_AND_TRADING"


def test_euler_headcount_conservation_under_overflow() -> None:
    """Verifies that declared seats + shared terminals never exceed total_headcount."""
    telemetry = {
        "interview_workforce_declarations": {
            "corporate_seats": 800,
            "shared_terminals": 500,
        }
    }
    profile = WorkforceSegmentationResolver.resolve(
        total_headcount=1000,
        client_telemetry=telemetry,
    )
    assert profile.corporate_seats == 800
    assert profile.shared_operational_edge_terminals == 200
    assert profile.deskless_field_workers == 0
    assert (
        profile.corporate_seats
        + profile.shared_operational_edge_terminals
        + profile.deskless_field_workers
        == profile.total_headcount
    )
