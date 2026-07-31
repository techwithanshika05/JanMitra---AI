"""Focused contract tests for the canonical ``preprocessing`` package."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

from reportlab.pdfgen import canvas

from preprocessing.sarvam_system.pipeline import DocumentPipeline, PipelineConfig


class _FakeSarvamJob:
    job_id = "offline-contract-test"

    def __init__(self, response_zip: Path):
        self.response_zip = response_zip

    def upload_file(self, path: str) -> None:
        if not Path(path).is_file():
            raise FileNotFoundError(path)

    def start(self) -> None:
        return None

    def wait_until_complete(self, poll_interval: int, timeout: int):
        return SimpleNamespace(job_state="Completed")

    def download_output(self, path: str) -> None:
        Path(path).write_bytes(self.response_zip.read_bytes())

    def get_page_metrics(self) -> dict[str, int]:
        return {"pages": 1}


class _FakeDocumentIntelligence:
    def __init__(self, response_zip: Path):
        self.response_zip = response_zip

    def create_job(self, **_: object) -> _FakeSarvamJob:
        return _FakeSarvamJob(self.response_zip)


class _FakeSarvamClient:
    def __init__(self, response_zip: Path):
        self.document_intelligence = _FakeDocumentIntelligence(response_zip)


class MultimodalPreprocessingTest(unittest.TestCase):
    def test_pipeline_preserves_text_image_chart_and_graph(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pdf_path = root / "multimodal.pdf"
            response_zip = root / "sarvam-output.zip"
            artifact_root = root / "artifacts"

            pdf = canvas.Canvas(str(pdf_path), pagesize=(600, 800))
            pdf.drawString(40, 750, "JanMitra multimodal preprocessing test")
            pdf.setFillColorRGB(0.2, 0.5, 0.8)
            pdf.rect(40, 500, 140, 120, fill=1)
            pdf.setFillColorRGB(0.8, 0.4, 0.2)
            pdf.rect(220, 500, 140, 120, fill=1)
            pdf.setFillColorRGB(0.3, 0.7, 0.3)
            pdf.rect(400, 500, 140, 120, fill=1)
            pdf.save()

            page_payload = {
                "page_num": 1,
                "image_width": 600,
                "image_height": 800,
                "blocks": [
                    {
                        "layout_tag": "paragraph",
                        "coordinates": {"x1": 40, "y1": 40, "x2": 520, "y2": 100},
                        "text": "A searchable text paragraph.",
                        "confidence": 0.99,
                        "reading_order": 1,
                    },
                    {
                        "layout_tag": "image",
                        "coordinates": {"x1": 40, "y1": 180, "x2": 180, "y2": 300},
                        "text": "Citizen service illustration",
                        "confidence": 0.95,
                        "reading_order": 2,
                    },
                    {
                        "layout_tag": "chart",
                        "coordinates": {"x1": 220, "y1": 180, "x2": 360, "y2": 300},
                        "text": "Scheme applications by month: January 20, February 30",
                        "confidence": 0.92,
                        "reading_order": 3,
                    },
                    {
                        "layout_tag": "graph",
                        "coordinates": {"x1": 400, "y1": 180, "x2": 540, "y2": 300},
                        "text": "Benefit trend",
                        "data": {
                            "chart_type": "line",
                            "categories": ["2024", "2025"],
                            "series": [{"name": "beneficiaries", "data": [10, 15]}],
                        },
                        "confidence": 0.97,
                        "reading_order": 4,
                    },
                ],
            }
            with zipfile.ZipFile(response_zip, "w") as archive:
                archive.writestr("metadata/page_001.json", json.dumps(page_payload))

            pipeline = DocumentPipeline(
                PipelineConfig(
                    api_key="offline-test",
                    output_format="html",
                    artifact_output_dir=artifact_root,
                ),
                client=_FakeSarvamClient(response_zip),
            )
            document = pipeline.process(pdf_path)

            blocks = document.pages[0].blocks
            self.assertEqual(
                {"paragraph", "image", "chart", "graph"},
                {block.layout for block in blocks},
            )
            self.assertIn("A searchable text paragraph.", blocks[0].text)
            for block in blocks[1:]:
                self.assertIsNotNone(block.image_path)
                self.assertTrue(Path(str(block.image_path)).is_file())

            artifacts = document.metadata["artifacts"]
            chart = next(item for item in artifacts if item["element_type"] == "chart")
            graph = next(item for item in artifacts if item["element_type"] == "graph")
            self.assertEqual("visual_only", chart["metadata"]["verification_status"])
            self.assertEqual("verified", graph["metadata"]["verification_status"])


if __name__ == "__main__":
    unittest.main()
