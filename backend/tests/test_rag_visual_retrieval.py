from __future__ import annotations

import json
import tempfile
from pathlib import Path

import fitz
from reportlab.pdfgen import canvas

from rag.rag_pipeline import RAGPipeline


QUERY = (
    "TOTAL FOODGRAIN ALLOCATIONS REACHED A RECORD HIGH "
    "OF 1,002 LAKH TONS IN 2021-22"
)


def _make_chart_pdf(path: Path) -> None:
    pdf = canvas.Canvas(str(path), pagesize=(600, 800))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(45, 735, QUERY)
    pdf.setFillColorRGB(0.8, 0.1, 0.1)
    pdf.rect(80, 520, 90, 140, fill=1)
    pdf.setFillColorRGB(0.5, 0.5, 0.5)
    pdf.rect(210, 520, 90, 100, fill=1)
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(45, 480, "Source: official foodgrain allocation bulletin")
    pdf.save()


def test_query_crops_one_visual_from_top_retrieved_source_page() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        data_dir = root / "data"
        raw_dir = data_dir / "raw"
        output_dir = data_dir / "retrieved_visuals"
        raw_dir.mkdir(parents=True)
        pdf_path = raw_dir / "foodgrain.pdf"
        _make_chart_pdf(pdf_path)

        results = [{
            "chunk_id": "foodgrain_p1",
            "distance": 0.20,
            "metadata": {
                "source_file": pdf_path.name,
                "page_number": 1,
            },
        }]
        visuals = RAGPipeline._prepare_retrieved_images(
            QUERY,
            results,
            data_dir=data_dir,
            output_dir=output_dir,
        )

        assert len(visuals) == 1
        visual = visuals[0]
        assert visual["layout"] == "chart"
        assert visual["page_number"] == 1
        assert visual["selection_method"] == "retrieved_source_page_crop"
        image_path = Path(visual["image_path"])
        assert image_path.is_file()

        with fitz.open(pdf_path) as source:
            full_width = source[0].rect.width
            full_height = source[0].rect.height
        crop = fitz.Pixmap(str(image_path))
        assert crop.width < full_width * 2
        assert crop.height < full_height * 2


def test_captioned_visual_metadata_is_preferred_over_page_fallback() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        data_dir = root / "data"
        corpus_dir = data_dir / "sarvam_test"
        image_dir = data_dir / "images"
        corpus_dir.mkdir(parents=True)
        image_dir.mkdir(parents=True)

        image_path = image_dir / "record-foodgrain-chart.png"
        pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 80), False)
        pixmap.clear_with(255)
        pixmap.save(image_path)

        record = {
            "chunk_id": "visual-1",
            "source_file": "foodgrain.pdf",
            "page_number": 1,
            "layout": "chart",
            "text": QUERY,
            "image_path": str(image_path),
        }
        (corpus_dir / "corpus.jsonl").write_text(
            json.dumps(record) + "\n",
            encoding="utf-8",
        )

        visuals = RAGPipeline._prepare_retrieved_images(
            QUERY,
            [{
                "metadata": {
                    "source_file": "foodgrain.pdf",
                    "page_number": 1,
                },
            }],
            data_dir=data_dir,
            output_dir=data_dir / "retrieved_visuals",
        )

        assert len(visuals) == 1
        assert visuals[0]["image_path"] == str(image_path.resolve())
        assert visuals[0]["selection_method"] == "indexed_visual_metadata"
