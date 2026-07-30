
"""
metadata_builder.py

Purpose:
--------
Build structured metadata for cleaned PDS and social welfare documents.

Input:
------
data/processed/cleaned/
    document1.json
    document2.json

Output:
-------
data/processed/metadata/
    document1.json
    document2.json

Pipeline:
---------
data/raw/*.pdf
        ↓
pdf_extractor.py
        ↓
data/extracted/*.json
        ↓
text_cleaner.py
        ↓
data/processed/cleaned/*.json
        ↓
metadata_builder.py
        ↓
data/processed/metadata/*.json

Metadata generated:
-------------------
- document_id
- source_file
- title
- category
- subcategory
- service
- document_type
- state
- jurisdiction
- language
- source_type
- page-level metadata

Notes:
------
This implementation uses deterministic keyword/rule-based classification.
It does NOT require an LLM.

This is intentional because metadata should be predictable and reproducible.

Run:
----
python backend/preprocessing/metadata_builder.py
"""

import json
import logging
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

PROCESSED_DIR = DATA_DIR / "processed"

CLEANED_DIR = PROCESSED_DIR / "cleaned"

METADATA_DIR = PROCESSED_DIR / "metadata"


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# Metadata Builder
# ============================================================

class MetadataBuilder:
    """
    Build metadata for PDS and social welfare documents.

    Classification is primarily performed at document level.

    The resulting document-level metadata is then propagated
    to individual pages.

    Later, the chunker can propagate the same metadata to
    individual chunks stored in ChromaDB.
    """

    # ========================================================
    # Category Rules
    # ========================================================

    CATEGORY_RULES = {
        "PDS": [
            "ration card",
            "ration",
            "public distribution system",
            "pds",
            "fair price shop",
            "fps",
            "food security",
            "national food security act",
            "nfsa",
            "food and civil supplies",
            "food grains",
            "foodgrain",
            "essential commodities",
        ],

        "WELFARE": [
            "welfare scheme",
            "social welfare",
            "government scheme",
            "beneficiary",
            "pension scheme",
            "scholarship",
            "housing scheme",
            "financial assistance",
            "social security",
            "employment scheme",
            "education scheme",
        ],

        "GRIEVANCE": [
            "grievance",
            "complaint",
            "complain",
            "escalation",
            "grievance redressal",
            "helpline",
            "lodge complaint",
            "register complaint",
        ],

        "FAQ": [
            "frequently asked questions",
            "faq",
            "questions and answers",
            "common questions",
        ],
    }

    # ========================================================
    # Service Rules
    # ========================================================

    SERVICE_RULES = {
        "ration_card_application": [
            "new ration card",
            "apply for ration card",
            "ration card application",
            "application for ration card",
            "issue of ration card",
        ],

        "ration_card_update": [
            "update ration card",
            "ration card update",
            "modify ration card",
            "modification of ration card",
            "correction in ration card",
        ],

        "address_update": [
            "change of address",
            "address change",
            "update address",
            "address update",
            "change address",
        ],

        "add_family_member": [
            "add family member",
            "addition of member",
            "add member",
            "inclusion of member",
            "include family member",
        ],

        "remove_family_member": [
            "remove family member",
            "deletion of member",
            "delete member",
            "remove member",
            "exclusion of member",
        ],

        "ration_entitlement": [
            "ration entitlement",
            "foodgrain entitlement",
            "food grain entitlement",
            "entitled quantity",
            "monthly entitlement",
        ],

        "fair_price_shop": [
            "fair price shop",
            "fps dealer",
            "ration dealer",
            "ration shop",
        ],

        "pds_grievance": [
            "pds grievance",
            "ration complaint",
            "ration grievance",
            "fair price shop complaint",
            "grievance redressal",
        ],

        "pension": [
            "pension scheme",
            "old age pension",
            "widow pension",
            "disability pension",
            "social security pension",
        ],

        "scholarship": [
            "scholarship",
            "student assistance",
            "education assistance",
        ],

        "housing": [
            "housing scheme",
            "housing assistance",
            "awas yojana",
            "housing benefit",
        ],

        "employment": [
            "employment scheme",
            "employment guarantee",
            "job scheme",
            "livelihood scheme",
        ],

        "general_welfare": [
            "social welfare",
            "welfare scheme",
            "government scheme",
        ],
    }

    # ========================================================
    # Document Type Rules
    # ========================================================

    DOCUMENT_TYPE_RULES = {
        "FAQ": [
            "frequently asked questions",
            "faq",
            "questions and answers",
        ],

        "GUIDELINE": [
            "guidelines",
            "guideline",
            "instructions",
            "operational guidelines",
        ],

        "POLICY": [
            "policy",
            "act",
            "rules",
            "regulation",
            "regulations",
        ],

        "SERVICE_GUIDE": [
            "how to apply",
            "application process",
            "procedure",
            "process for",
            "steps to",
        ],

        "GRIEVANCE_GUIDE": [
            "grievance redressal",
            "complaint procedure",
            "lodge complaint",
            "register grievance",
        ],

        "SCHEME_DOCUMENT": [
            "scheme",
            "yojana",
            "programme",
            "program",
        ],
    }

    # ========================================================
    # State Detection Rules
    # ========================================================

    STATE_RULES = {
        "andhra_pradesh": [
            "andhra pradesh",
        ],
        "arunachal_pradesh": [
            "arunachal pradesh",
        ],
        "assam": [
            "assam",
        ],
        "bihar": [
            "bihar",
        ],
        "chhattisgarh": [
            "chhattisgarh",
        ],
        "goa": [
            "goa",
        ],
        "gujarat": [
            "gujarat",
        ],
        "haryana": [
            "haryana",
        ],
        "himachal_pradesh": [
            "himachal pradesh",
        ],
        "jharkhand": [
            "jharkhand",
        ],
        "karnataka": [
            "karnataka",
        ],
        "kerala": [
            "kerala",
        ],
        "madhya_pradesh": [
            "madhya pradesh",
        ],
        "maharashtra": [
            "maharashtra",
        ],
        "manipur": [
            "manipur",
        ],
        "meghalaya": [
            "meghalaya",
        ],
        "mizoram": [
            "mizoram",
        ],
        "nagaland": [
            "nagaland",
        ],
        "odisha": [
            "odisha",
            "orissa",
        ],
        "punjab": [
            "punjab",
        ],
        "rajasthan": [
            "rajasthan",
        ],
        "sikkim": [
            "sikkim",
        ],
        "tamil_nadu": [
            "tamil nadu",
        ],
        "telangana": [
            "telangana",
        ],
        "tripura": [
            "tripura",
        ],
        "uttar_pradesh": [
            "uttar pradesh",
        ],
        "uttarakhand": [
            "uttarakhand",
            "uttaranchal",
        ],
        "west_bengal": [
            "west bengal",
        ],
    }

    # ========================================================
    # Central / National Indicators
    # ========================================================

    CENTRAL_INDICATORS = [
        "government of india",
        "ministry of",
        "national food security act",
        "nfsa",
        "central government",
        "national scheme",
    ]

    # ========================================================
    # Hindi Character Detection
    # ========================================================

    DEVANAGARI_PATTERN = re.compile(
        r"[\u0900-\u097F]"
    )

    # ========================================================
    # Constructor
    # ========================================================

    def __init__(
        self,
        input_dir: Path = CLEANED_DIR,
        output_dir: Path = METADATA_DIR,
    ) -> None:

        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

        self.input_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info("MetadataBuilder initialized")
        logger.info(
            "Input directory: %s",
            self.input_dir,
        )
        logger.info(
            "Output directory: %s",
            self.output_dir,
        )

    # ========================================================
    # File Discovery
    # ========================================================

    def find_json_files(
        self,
    ) -> List[Path]:

        json_files = sorted(
            [
                file
                for file in self.input_dir.iterdir()
                if file.is_file()
                and file.suffix.lower() == ".json"
            ],
            key=lambda path: path.name.lower(),
        )

        logger.info(
            "Found %d cleaned document(s)",
            len(json_files),
        )

        return json_files

    # ========================================================
    # Load Document
    # ========================================================

    @staticmethod
    def load_document(
        path: Path,
    ) -> Dict[str, Any]:

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    # ========================================================
    # Get Document Text
    # ========================================================

    @staticmethod
    def get_document_text(
        document: Dict[str, Any],
        max_pages: Optional[int] = None,
    ) -> str:
        """
        Combine cleaned page text.

        max_pages can be used to inspect only the beginning
        of very large documents.
        """

        pages = document.get(
            "pages",
            [],
        )

        if max_pages is not None:
            pages = pages[:max_pages]

        texts = []

        for page in pages:

            text = (
                page.get("cleaned_text")
                or page.get("text")
                or ""
            )

            if text:
                texts.append(text)

        return "\n".join(texts)

    # ========================================================
    # Keyword Scoring
    # ========================================================

    @staticmethod
    def score_rules(
        text: str,
        rules: Dict[str, List[str]],
    ) -> Dict[str, int]:
        """
        Score each classification label based on keyword
        occurrences.
        """

        text_lower = text.lower()

        scores = {}

        for label, keywords in rules.items():

            score = 0

            for keyword in keywords:

                occurrences = text_lower.count(
                    keyword.lower()
                )

                score += occurrences

            scores[label] = score

        return scores

    @staticmethod
    def best_match(
        scores: Dict[str, int],
        default: str = "GENERAL",
    ) -> Tuple[str, int]:
        """
        Return highest scoring label.
        """

        if not scores:
            return default, 0

        label = max(
            scores,
            key=scores.get,
        )

        score = scores[label]

        if score <= 0:
            return default, 0

        return label, score

    # ========================================================
    # Category Detection
    # ========================================================

    def detect_category(
        self,
        text: str,
    ) -> Tuple[str, int]:

        scores = self.score_rules(
            text,
            self.CATEGORY_RULES,
        )

        return self.best_match(
            scores,
            default="GENERAL",
        )

    # ========================================================
    # Service Detection
    # ========================================================

    def detect_service(
        self,
        text: str,
    ) -> Tuple[str, int]:

        scores = self.score_rules(
            text,
            self.SERVICE_RULES,
        )

        return self.best_match(
            scores,
            default="general_information",
        )

    # ========================================================
    # Document Type Detection
    # ========================================================

    def detect_document_type(
        self,
        text: str,
    ) -> Tuple[str, int]:

        scores = self.score_rules(
            text,
            self.DOCUMENT_TYPE_RULES,
        )

        return self.best_match(
            scores,
            default="GENERAL_DOCUMENT",
        )

    # ========================================================
    # State Detection
    # ========================================================

    def detect_state(
        self,
        text: str,
        filename: str,
    ) -> Tuple[str, int]:

        combined_text = (
            filename.replace("_", " ")
            + "\n"
            + text
        ).lower()

        scores = self.score_rules(
            combined_text,
            self.STATE_RULES,
        )

        state, score = self.best_match(
            scores,
            default="unknown",
        )

        return state, score

    # ========================================================
    # Jurisdiction Detection
    # ========================================================

    def detect_jurisdiction(
        self,
        text: str,
        state: str,
    ) -> str:

        if state != "unknown":
            return "state"

        text_lower = text.lower()

        for indicator in self.CENTRAL_INDICATORS:

            if indicator in text_lower:
                return "central"

        return "unknown"

    # ========================================================
    # Language Detection
    # ========================================================

    def detect_language(
        self,
        text: str,
    ) -> str:
        """
        Basic Hindi/English/mixed language detection.

        This is intentionally lightweight and requires no
        external language-detection package.
        """

        if not text.strip():
            return "unknown"

        devanagari_chars = len(
            self.DEVANAGARI_PATTERN.findall(
                text
            )
        )

        latin_chars = len(
            re.findall(
                r"[A-Za-z]",
                text,
            )
        )

        total_language_chars = (
            devanagari_chars
            + latin_chars
        )

        if total_language_chars == 0:
            return "unknown"

        hindi_ratio = (
            devanagari_chars
            / total_language_chars
        )

        english_ratio = (
            latin_chars
            / total_language_chars
        )

        if hindi_ratio >= 0.70:
            return "hindi"

        if english_ratio >= 0.70:
            return "english"

        if (
            devanagari_chars > 0
            and latin_chars > 0
        ):
            return "mixed"

        return "unknown"

    # ========================================================
    # Title Extraction
    # ========================================================

    @staticmethod
    def extract_title(
        document: Dict[str, Any],
    ) -> str:
        """
        Attempt to determine a human-readable document title.

        Priority:
        1. PDF metadata title
        2. First useful text line
        3. Source filename
        """

        pdf_metadata = document.get(
            "pdf_metadata",
            {},
        )

        metadata_title = (
            pdf_metadata.get("title")
            or ""
        ).strip()

        if metadata_title:

            return metadata_title

        pages = document.get(
            "pages",
            [],
        )

        for page in pages[:3]:

            text = (
                page.get("cleaned_text")
                or page.get("text")
                or ""
            )

            for line in text.split("\n"):

                line = line.strip()

                if (
                    len(line) >= 5
                    and len(line) <= 200
                ):
                    return line

        source_file = document.get(
            "source_file",
            "Unknown Document",
        )

        return Path(
            source_file
        ).stem.replace(
            "_",
            " ",
        ).replace(
            "-",
            " ",
        ).strip()

    # ========================================================
    # Subcategory Detection
    # ========================================================

    @staticmethod
    def determine_subcategory(
        category: str,
        service: str,
    ) -> str:

        if category == "PDS":

            if service in {
                "ration_card_application",
                "ration_card_update",
                "address_update",
                "add_family_member",
                "remove_family_member",
            }:
                return "ration_card_services"

            if service == "ration_entitlement":
                return "entitlement"

            if service == "fair_price_shop":
                return "fair_price_shop"

            if service == "pds_grievance":
                return "grievance"

            return "general_pds"

        if category == "WELFARE":

            if service in {
                "pension",
                "scholarship",
                "housing",
                "employment",
            }:
                return service

            return "general_welfare"

        if category == "GRIEVANCE":
            return "grievance"

        if category == "FAQ":
            return "faq"

        return "general"

    # ========================================================
    # Build Document Metadata
    # ========================================================

    def build_document_metadata(
        self,
        document: Dict[str, Any],
    ) -> Dict[str, Any]:

        source_file = document.get(
            "source_file",
            "unknown.pdf",
        )

        document_id = document.get(
            "document_id",
            Path(source_file).stem,
        )

        # Use complete text for classification.
        document_text = self.get_document_text(
            document
        )

        # Use first pages for title/context-sensitive detection.
        initial_text = self.get_document_text(
            document,
            max_pages=10,
        )

        category, category_score = (
            self.detect_category(
                document_text
            )
        )

        service, service_score = (
            self.detect_service(
                document_text
            )
        )

        document_type, type_score = (
            self.detect_document_type(
                document_text
            )
        )

        state, state_score = (
            self.detect_state(
                initial_text,
                source_file,
            )
        )

        jurisdiction = (
            self.detect_jurisdiction(
                initial_text,
                state,
            )
        )

        language = (
            self.detect_language(
                document_text
            )
        )

        title = self.extract_title(
            document
        )

        subcategory = (
            self.determine_subcategory(
                category,
                service,
            )
        )

        metadata = {
            "document_id": document_id,
            "title": title,
            "source_file": source_file,

            "category": category,
            "subcategory": subcategory,
            "service": service,

            "document_type": (
                document_type
            ),

            "state": state,
            "jurisdiction": jurisdiction,

            "language": language,

            "source_type": "document",

            "classification_scores": {
                "category_score": (
                    category_score
                ),
                "service_score": (
                    service_score
                ),
                "document_type_score": (
                    type_score
                ),
                "state_score": (
                    state_score
                ),
            },

            "metadata_version": "1.0",

            "metadata_generated_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
        }

        return metadata

    # ========================================================
    # Add Metadata to Pages
    # ========================================================

    @staticmethod
    def enrich_pages(
        pages: List[Dict[str, Any]],
        document_metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Propagate relevant document metadata to every page.

        This is useful because the chunker will later inherit
        page metadata.
        """

        enriched_pages = []

        for page in pages:

            enriched_page = page.copy()

            page_number = page.get(
                "page_number"
            )

            page_metadata = {
                "document_id": (
                    document_metadata[
                        "document_id"
                    ]
                ),

                "source_file": (
                    document_metadata[
                        "source_file"
                    ]
                ),

                "title": (
                    document_metadata[
                        "title"
                    ]
                ),

                "page_number": (
                    page_number
                ),

                "category": (
                    document_metadata[
                        "category"
                    ]
                ),

                "subcategory": (
                    document_metadata[
                        "subcategory"
                    ]
                ),

                "service": (
                    document_metadata[
                        "service"
                    ]
                ),

                "document_type": (
                    document_metadata[
                        "document_type"
                    ]
                ),

                "state": (
                    document_metadata[
                        "state"
                    ]
                ),

                "jurisdiction": (
                    document_metadata[
                        "jurisdiction"
                    ]
                ),

                "language": (
                    document_metadata[
                        "language"
                    ]
                ),
            }

            enriched_page[
                "metadata"
            ] = page_metadata

            enriched_pages.append(
                enriched_page
            )

        return enriched_pages

    # ========================================================
    # Process Document
    # ========================================================

    def process_document(
        self,
        document: Dict[str, Any],
    ) -> Dict[str, Any]:

        source_file = document.get(
            "source_file",
            "unknown.pdf",
        )

        logger.info(
            "Building metadata for: %s",
            source_file,
        )

        document_metadata = (
            self.build_document_metadata(
                document
            )
        )

        enriched_document = (
            document.copy()
        )

        enriched_document[
            "document_metadata"
        ] = document_metadata

        enriched_document[
            "pages"
        ] = self.enrich_pages(
            document.get(
                "pages",
                [],
            ),
            document_metadata,
        )

        logger.info(
            "Metadata: %s | "
            "Category=%s | "
            "Service=%s | "
            "State=%s | "
            "Language=%s",
            source_file,
            document_metadata[
                "category"
            ],
            document_metadata[
                "service"
            ],
            document_metadata[
                "state"
            ],
            document_metadata[
                "language"
            ],
        )

        return enriched_document

    # ========================================================
    # Save Document
    # ========================================================

    def save_document(
        self,
        document: Dict[str, Any],
    ) -> Path:

        document_id = document.get(
            "document_id"
        )

        if not document_id:

            raise ValueError(
                "Document missing document_id."
            )

        output_path = (
            self.output_dir
            / f"{document_id}.json"
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                document,
                file,
                ensure_ascii=False,
                indent=2,
            )

        logger.info(
            "Saved metadata document: %s",
            output_path,
        )

        return output_path

    # ========================================================
    # Process Single File
    # ========================================================

    def process_single_file(
        self,
        json_path: Path,
    ) -> Dict[str, Any]:

        document = self.load_document(
            json_path
        )

        enriched_document = (
            self.process_document(
                document
            )
        )

        output_path = (
            self.save_document(
                enriched_document
            )
        )

        metadata = enriched_document[
            "document_metadata"
        ]

        return {
            "source_file": metadata[
                "source_file"
            ],
            "status": "success",
            "output_file": str(
                output_path
            ),
            "category": metadata[
                "category"
            ],
            "service": metadata[
                "service"
            ],
            "state": metadata[
                "state"
            ],
            "language": metadata[
                "language"
            ],
        }

    # ========================================================
    # Process All Documents
    # ========================================================

    def process_all_documents(
        self,
    ) -> Dict[str, Any]:

        json_files = (
            self.find_json_files()
        )

        if not json_files:

            logger.warning(
                "No cleaned JSON documents found."
            )

            return {
                "total_files": 0,
                "successful_files": 0,
                "failed_files": 0,
                "results": [],
            }

        results = []

        successful_files = 0
        failed_files = 0

        category_counter = Counter()

        for json_path in json_files:

            try:

                result = (
                    self.process_single_file(
                        json_path
                    )
                )

                results.append(result)

                successful_files += 1

                category_counter[
                    result["category"]
                ] += 1

            except Exception as error:

                failed_files += 1

                logger.exception(
                    "Failed metadata generation "
                    "for %s: %s",
                    json_path.name,
                    error,
                )

                results.append(
                    {
                        "source_file": (
                            json_path.name
                        ),
                        "status": "failed",
                        "error": str(error),
                    }
                )

        summary = {
            "total_files": len(
                json_files
            ),

            "successful_files": (
                successful_files
            ),

            "failed_files": (
                failed_files
            ),

            "category_distribution": dict(
                category_counter
            ),

            "results": results,
        }

        logger.info("=" * 60)
        logger.info(
            "METADATA GENERATION COMPLETED"
        )
        logger.info("=" * 60)

        logger.info(
            "Total documents: %d",
            len(json_files),
        )

        logger.info(
            "Successful: %d",
            successful_files,
        )

        logger.info(
            "Failed: %d",
            failed_files,
        )

        logger.info(
            "Categories: %s",
            dict(category_counter),
        )

        logger.info("=" * 60)

        return summary


# ============================================================
# Main
# ============================================================

def main() -> None:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "PDS & SOCIAL WELFARE AI - METADATA BUILDER"
    )

    print(
        "=" * 60
    )

    builder = MetadataBuilder()

    summary = (
        builder.process_all_documents()
    )

    print(
        "\nMetadata Summary"
    )

    print(
        "-" * 60
    )

    print(
        f"Total documents : "
        f"{summary['total_files']}"
    )

    print(
        f"Successful      : "
        f"{summary['successful_files']}"
    )

    print(
        f"Failed          : "
        f"{summary['failed_files']}"
    )

    if summary.get(
        "category_distribution"
    ):

        print(
            "\nCategory Distribution"
        )

        print(
            "-" * 60
        )

        for (
            category,
            count,
        ) in summary[
            "category_distribution"
        ].items():

            print(
                f"{category}: {count}"
            )

    if summary["results"]:

        print(
            "\nProcessed Documents"
        )

        print(
            "-" * 60
        )

        for result in summary[
            "results"
        ]:

            if (
                result["status"]
                == "success"
            ):

                print(
                    f"[OK] "
                    f"{result['source_file']} "
                    f"| Category: "
                    f"{result['category']} "
                    f"| Service: "
                    f"{result['service']} "
                    f"| State: "
                    f"{result['state']} "
                    f"| Language: "
                    f"{result['language']}"
                )

            else:

                print(
                    f"[FAILED] "
                    f"{result['source_file']} "
                    f"| Error: "
                    f"{result['error']}"
                )

    print(
        "\nMetadata directory:"
    )

    print(
        METADATA_DIR
    )

    print(
        "\n"
        + "=" * 60
    )


if __name__ == "__main__":
    main()

