from collections.abc import Callable
import hashlib
import json
import re
from typing import Any

from app.checklists.enums import ChecklistItemType
from app.checklists.schemas import (
    ChecklistCreate,
    ChecklistKnowledgeRequest,
    ChecklistRefresh,
    ChecklistSourceItem,
)


class ChecklistKnowledgeUnavailableError(RuntimeError):
    pass


class InsufficientChecklistEvidenceError(ValueError):
    pass


_GENERATED_SOURCE_MARKERS = (
    "setuai_checklist",
    "ai-generated-checklist",
    "generated_checklist",
)
_DOCUMENT_HEADING = re.compile(
    r"\b(required\s+documents?|documents?\s+required|document\s+checklist)\b",
    re.IGNORECASE,
)
_STEP_HEADING = re.compile(
    r"\b(application\s+steps?|procedure\s+for\s+apply|application\s+procedure|process\s+steps?)\b",
    re.IGNORECASE,
)
_TIMELINE = re.compile(
    r"\b(?:sla|estimated|processing\s+time|number\s+of\s+days|\d+\s*(?:working\s+)?"
    r"(?:days?|weeks?|months?))\b",
    re.IGNORECASE,
)
_WARNING = re.compile(r"\b(?:warning|important|note|caution)\b", re.IGNORECASE)
_NUMBER_PREFIX = re.compile(
    r"^\s*(?:step\s*[-–—]?\s*\d+\s*[:.)-]?|\d+\s*[.)-]|[a-z]\s*[.)])\s*",
    re.IGNORECASE,
)
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_INLINE_BULLET = re.compile(
    r"\s*(?:\u2022|\u25cf|\u25e6|\u25aa|\u2713|\u00b7|\u00e2\u20ac\u00a2)\s*"
)


def _source_title(result: dict[str, Any]) -> str:
    metadata = result.get("metadata") or {}
    return str(
        metadata.get("title")
        or metadata.get("source_file")
        or metadata.get("file_name")
        or "Government document"
    ).strip()


def _clean_line(line: str) -> str:
    line = _CONTROL_CHARS.sub(" ", line)
    line = line.replace("•", " ").replace("✓", " ")
    line = re.sub(r"\s+", " ", line).strip(" \t|")
    return line


def _line_segments(line: str) -> list[str]:
    """Split inline PDF bullets before normalization destroys their structure."""
    parts = [
        cleaned
        for part in _INLINE_BULLET.split(line)
        if (cleaned := _clean_line(part))
    ]
    # Text before the first inline bullet is normally a document/service
    # heading, not a checkable requirement.
    if _INLINE_BULLET.search(line) and len(parts) > 1:
        prefix_is_heading = bool(
            _DOCUMENT_HEADING.search(parts[0]) or _STEP_HEADING.search(parts[0])
        )
        return parts if prefix_is_heading else parts[1:]
    return parts


def _timeline_excerpt(line: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", line)
    for sentence in sentences:
        if _TIMELINE.search(sentence):
            return sentence[:600]
    return line[:600]


def _content_after_prefix(line: str) -> str:
    return _NUMBER_PREFIX.sub("", line).strip(" :-–—")


def _source_key(item_type: ChecklistItemType, title: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    digest = hashlib.sha256(
        f"{item_type.value}:{normalized}".encode("utf-8")
    ).hexdigest()[:12]
    return f"{item_type.value}:{digest}"


class ChecklistKnowledgeService:
    def __init__(
        self,
        retrieve: Callable[[str], list[dict[str, Any]]] | None = None,
        *,
        minimum_similarity: float = 0.35,
    ):
        self._retrieve = retrieve
        self.minimum_similarity = minimum_similarity

    def _retrieve_results(self, query: str) -> list[dict[str, Any]]:
        try:
            if self._retrieve is not None:
                return self._retrieve(query)
            from integration.rag_adapter import rag_adapter

            return rag_adapter.retrieve(query)
        except Exception as exc:
            raise ChecklistKnowledgeUnavailableError(
                "Official checklist retrieval is temporarily unavailable"
            ) from exc

    def _verified_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        verified = []
        for result in results:
            title = _source_title(result)
            lowered_title = title.lower().replace(" ", "_")
            if any(marker in lowered_title for marker in _GENERATED_SOURCE_MARKERS):
                continue
            text = str(result.get("text") or "").strip()
            try:
                similarity = float(result.get("similarity") or 0.0)
            except (TypeError, ValueError):
                similarity = 0.0
            if text and similarity >= self.minimum_similarity:
                verified.append({**result, "_title": title, "_similarity": similarity})
        return verified

    @staticmethod
    def _extract_items(results: list[dict[str, Any]]) -> list[ChecklistSourceItem]:
        extracted: list[tuple[ChecklistItemType, str, str | None, bool]] = []

        for result in results:
            mode: ChecklistItemType | None = None
            lines = [
                segment
                for raw_line in str(result["text"]).splitlines()
                for segment in _line_segments(raw_line)
            ]
            for line in (line for line in lines if line):
                lowered = line.lower()
                if _DOCUMENT_HEADING.search(line):
                    mode = ChecklistItemType.DOCUMENT
                    trailing = _DOCUMENT_HEADING.sub("", line).strip(" :-–—")
                    if trailing and not re.match(
                        r"^(?:for|of|to)\b", trailing, re.IGNORECASE
                    ):
                        extracted.append((mode, trailing, None, True))
                    continue
                if _STEP_HEADING.search(line):
                    mode = ChecklistItemType.PROCESS_STEP
                    trailing = _STEP_HEADING.sub("", line).strip(" :-–—&")
                    if trailing:
                        extracted.append((mode, trailing, None, True))
                    continue
                if _TIMELINE.search(line) and (
                    "day" in lowered
                    or "week" in lowered
                    or "month" in lowered
                    or "sla" in lowered
                ):
                    extracted.append(
                        (
                            ChecklistItemType.TIMELINE,
                            "Estimated service timeline",
                            _timeline_excerpt(line),
                            False,
                        )
                    )
                    continue
                if _WARNING.search(line) and len(line) >= 20:
                    extracted.append(
                        (ChecklistItemType.IMPORTANT_NOTE, line, None, False)
                    )
                    continue

                if mode is None:
                    continue
                if lowered in {
                    "document",
                    "required",
                    "notes",
                    "required documents",
                    "application steps",
                }:
                    continue
                if lowered.startswith(
                    (
                        "form submission",
                        "name of department",
                        "applicability criteria",
                        "responsible ai disclaimer",
                    )
                ):
                    mode = None
                    continue
                candidate = _content_after_prefix(line)
                if len(candidate) < 4 or candidate.isdigit():
                    continue
                extracted.append((mode, candidate, None, True))

        items: list[ChecklistSourceItem] = []
        seen: set[str] = set()
        for item_type, title, description, required in extracted:
            normalized_title = re.sub(r"\s+", " ", title).strip(" .;:")
            key = _source_key(item_type, normalized_title)
            if key in seen:
                continue
            seen.add(key)
            items.append(
                ChecklistSourceItem(
                    item_type=item_type,
                    title=normalized_title[:300],
                    description=description[:4000] if description else None,
                    sequence_number=len(items) + 1,
                    is_required=required,
                    source_item_key=key,
                )
            )
        return items

    @staticmethod
    def _citations(results: list[dict[str, Any]]) -> list[dict]:
        return [
            {
                "title": result["_title"],
                "snippet": re.sub(r"\s+", " ", str(result["text"]))[:240],
                "score": round(
                    max(0.0, min(1.0, float(result["_similarity"]))), 3
                ),
            }
            for result in results
        ]

    @staticmethod
    def _version(results: list[dict[str, Any]]) -> str:
        evidence = [
            {
                "title": result["_title"],
                "text": str(result["text"]),
                "metadata": result.get("metadata") or {},
            }
            for result in results
        ]
        encoded = json.dumps(
            evidence, sort_keys=True, ensure_ascii=False, default=str
        ).encode("utf-8")
        return f"rag-{hashlib.sha256(encoded).hexdigest()[:24]}"

    @staticmethod
    def _deterministic_service_payload(
        request: ChecklistKnowledgeRequest,
    ) -> ChecklistCreate | None:
        """Use the checklist already shown to the citizen for known services."""
        from app.routers.checklist import CHECKLIST_LIBRARY

        entry = CHECKLIST_LIBRARY.get(request.service_id)
        if entry is None:
            return None

        rows: list[tuple[ChecklistItemType, str, str | None, bool]] = [
            (ChecklistItemType.DOCUMENT, title, None, True)
            for title in entry["documents"]
        ]
        rows.extend(
            (ChecklistItemType.PROCESS_STEP, title, None, True)
            for title in entry["steps"]
        )
        if entry.get("estimated_time"):
            rows.append(
                (
                    ChecklistItemType.TIMELINE,
                    "Estimated service timeline",
                    entry["estimated_time"],
                    False,
                )
            )

        items = [
            ChecklistSourceItem(
                item_type=item_type,
                title=title,
                description=description,
                sequence_number=index,
                is_required=required,
                source_item_key=_source_key(item_type, title),
            )
            for index, (item_type, title, description, required) in enumerate(
                rows, start=1
            )
        ]
        encoded = json.dumps(entry, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return ChecklistCreate(
            service_id=request.service_id,
            service_name=request.service_name,
            language=request.language,
            source_version=(
                f"library-{hashlib.sha256(encoded).hexdigest()[:24]}"
            ),
            source_citations=[{
                "title": "JanMitra service checklist",
                "snippet": (
                    "The same structured requirements shown by the checklist generator."
                ),
                "score": 1.0,
            }],
            knowledge_context={
                "state": request.state,
                "category": request.category,
            },
            items=items,
        )

    def build(self, request: ChecklistKnowledgeRequest) -> ChecklistCreate:
        deterministic = self._deterministic_service_payload(request)
        if deterministic is not None:
            return deterministic

        query_parts = [
            request.service_name,
            "required documents application steps warnings important notes estimated timeline",
        ]
        if request.state:
            query_parts.append(request.state)
        if request.category:
            query_parts.append(request.category)
        verified = self._verified_results(
            self._retrieve_results(" ".join(query_parts))
        )
        if not verified:
            raise InsufficientChecklistEvidenceError(
                "No sufficiently reliable official checklist evidence was retrieved"
            )
        items = self._extract_items(verified)
        if not any(
            item.item_type
            in {ChecklistItemType.DOCUMENT, ChecklistItemType.PROCESS_STEP}
            for item in items
        ):
            raise InsufficientChecklistEvidenceError(
                "Retrieved sources did not contain a structured document or process checklist"
            )
        return ChecklistCreate(
            service_id=request.service_id,
            service_name=request.service_name,
            language=request.language,
            source_version=self._version(verified),
            source_citations=self._citations(verified),
            knowledge_context={
                "state": request.state,
                "category": request.category,
            },
            items=items,
        )

    def refresh_payload(
        self, request: ChecklistKnowledgeRequest
    ) -> ChecklistRefresh:
        created = self.build(request)
        return ChecklistRefresh(
            source_version=created.source_version,
            source_citations=created.source_citations,
            items=created.items,
        )
