"""Phase 5 entry point: session_report.json -> final_report.json."""
from pathlib import Path
from typing import Optional

from app.analysis.config import DEFAULT_CONFIG, AnalysisConfig
from app.analysis.feedback import llm as llm_module
from app.analysis.feedback.generator import generate_feedback
from app.analysis.feedback.llm import LLMClient
from app.analysis.fusion.pipeline import OUTPUT_FILE as REPORT_FILE
from app.analysis.fusion.pipeline import generate_report
from app.analysis.preprocess import load_run
from app.analysis.schemas import FinalReport, SessionReport

OUTPUT_FILE = "final_report.json"
_FROM_ENV = object()  # sentinel: "use the LLM configured in the environment, if any"


def generate_final(
    run_dir: str | Path,
    topic: Optional[str] = None,
    key_points: Optional[list[str]] = None,
    llm: Optional[LLMClient] | object = _FROM_ENV,
    cfg: AnalysisConfig = DEFAULT_CONFIG,
) -> FinalReport:
    """Build and save final_report.json for a run that has finished phases 2-4.

    llm: an LLMClient, None to force the offline template, or (default) whatever
    the SPEAKWISE_LLM_* environment variables configure (nothing = offline).
    """
    run = load_run(run_dir)
    report_path = run.run_dir / REPORT_FILE
    report = (SessionReport.model_validate_json(report_path.read_text(encoding="utf-8"))
              if report_path.is_file() else generate_report(run.run_dir, cfg))
    client = llm_module.from_env() if llm is _FROM_ENV else llm

    final = FinalReport(
        run_id=report.run_id, topic=topic, report=report,
        feedback=generate_feedback(report, topic=topic, key_points=key_points, llm=client),
    )
    (run.run_dir / OUTPUT_FILE).write_text(final.model_dump_json(indent=2), encoding="utf-8")
    return final
