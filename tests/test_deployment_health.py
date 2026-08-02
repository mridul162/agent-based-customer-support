from app.api.routes.support import build_health_report


def test_build_health_report_includes_core_checks() -> None:
    report = build_health_report()

    assert report["status"] in {"ok", "degraded"}
    assert set(report["checks"].keys()) >= {"database", "openai", "vector_index"}
