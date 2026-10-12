"""Write the report JSON Schema to configs/report.schema.json (for the future desktop app)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from speakwise.schemas import SCHEMA_VERSION, SessionReport  # noqa: E402

if __name__ == "__main__":
    schema = SessionReport.model_json_schema()
    schema["$comment"] = f"SpeakWise session report, schema version {SCHEMA_VERSION}"
    out = ROOT / "configs" / "report.schema.json"
    out.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print("wrote", out)
