"""Testes unitários e de integração leve para o script de auditoria econômica longa."""

from __future__ import annotations

import pytest
from scripts.audit_simulate_seasons import (
    AuditAlert,
    SeasonAuditSnapshot,
    classify_audit_alerts,
    render_markdown_report,
    run_multi_season_simulation,
)


def test_classify_audit_alerts_detects_under_squad():
    snap = SeasonAuditSnapshot(
        season_year=2026,
        economic_index=1.0,
        teams_count=80,
        squad_under_18_count=2,
    )
    alerts = classify_audit_alerts([snap])

    assert len(alerts) >= 1
    assert any(a.severity == "CRÍTICO" and "18" in a.evidence for a in alerts)


def test_classify_audit_alerts_detects_over_squad():
    snap = SeasonAuditSnapshot(
        season_year=2026,
        economic_index=1.0,
        teams_count=80,
        squad_over_30_count=1,
    )
    alerts = classify_audit_alerts([snap])

    assert len(alerts) >= 1
    assert any(a.severity == "CRÍTICO" and "30" in a.evidence for a in alerts)


def test_render_markdown_report_generates_valid_content():
    snap = SeasonAuditSnapshot(
        season_year=2026,
        economic_index=1.0,
        teams_count=80,
        budget_avg_by_tier={"A": 10_000_000, "B": 5_000_000, "C": 2_000_000, "D": 800_000},
        squad_size_avg=22.5,
    )
    alert = AuditAlert(
        severity="BAIXO",
        system="Finanças",
        finding="Teste de alerta",
        evidence="Evidência",
        recommendation="Recomendação",
    )
    report = render_markdown_report([snap], [alert])

    assert "# Auditoria Econômica Longa — Garfoot" in report
    assert "Série A" in report
    assert "R$ 10,000,000" in report


def test_quick_single_season_audit_simulation_runs():
    """Valida a execução de 1 temporada de simulação econômica rápida."""
    snapshots, alerts = run_multi_season_simulation(num_seasons=1, seed=2026)

    assert len(snapshots) == 1
    assert snapshots[0].season_year == 2026
    assert snapshots[0].teams_count == 80
    assert snapshots[0].squad_size_avg > 0
