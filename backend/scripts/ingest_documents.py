# """
# ingest_documents.py

# Main document ingestion pipeline for JanMitra.

# This script processes all PDF files stored inside:

#     backend/data/raw/

# Pipeline:

# PDF Files
#     ->
# PDF Extractor
#     ->
# Text Cleaner
#     ->
# Metadata Builder
#     ->
# Chunker
#     ->
# Embedding Service
#     ->
# ChromaDB

# Run from the backend directory:

#     python -m scripts.ingest_documents

# After successful ingestion, run:

#     python -m rag.rag_pipeline
# """

# from __future__ import annotations

# import hashlib
# import json
# import logging
# import sys
# import time
# from pathlib import Path
# from typing import Any, Dict, List, Optional


# # ============================================================
# # Project Root
# # ============================================================

# BACKEND_DIR = Path(__file__).resolve().parent.parent

# if str(BACKEND_DIR) not in sys.path:
#     sys.path.insert(
#         0,
#         str(BACKEND_DIR),
#     )


# # ============================================================
# # Project Imports
# # ============================================================

# try:
#     from preprocessing.pdf_extractor import PDFExtractor
# except ImportError:
#     PDFExtractor = None

# try:
#     from preprocessing.text_cleaner import TextCleaner
# except ImportError:
#     TextCleaner = None

# try:
#     from preprocessing.metadata_builder import MetadataBuilder
# except ImportError:
#     MetadataBuilder = None

# try:
#     from preprocessing.chunker import DocumentChunker
#     Chunker = DocumentChunker
# except ImportError:
#     Chunker = None

# try:
#     from embeddings.embedding_service import EmbeddingService
# except ImportError:
#     EmbeddingService = None

# try:
#     from vectorstore.chroma_store import ChromaStore
# except ImportError:
#     ChromaStore = None


# # ============================================================
# # Paths
# # ============================================================

# RAW_DATA_DIR = (
#     BACKEND_DIR
#     / "data"
#     / "raw"
# )

# PROCESSED_DATA_DIR = (
#     BACKEND_DIR
#     / "data"
#     / "processed"
# )

# INGESTION_STATE_FILE = (
#     PROCESSED_DATA_DIR
#     / "ingestion_state.json"
# )


# # ============================================================
# # Logging
# # ============================================================

# logging.basicConfig(
#     level=logging.INFO,
#     format=(
#         "%(asctime)s | "
#         "%(levelname)s | "
#         "%(message)s"
#     ),
# )

# logger = logging.getLogger(
#     "janmitra_ingestion"
# )


# # ============================================================
# # Custom Exception
# # ============================================================

# class IngestionError(Exception):
#     """
#     Raised when document ingestion fails.
#     """


# # ============================================================
# # Utility Functions
# # ============================================================

# def calculate_file_hash(
#     file_path: Path,
# ) -> str:
#     """
#     Calculate SHA-256 hash for a PDF.

#     This helps detect whether a document has already been
#     processed or has changed since the previous ingestion.
#     """

#     sha256 = hashlib.sha256()

#     with file_path.open(
#         "rb"
#     ) as file:

#         while True:

#             data = file.read(
#                 1024 * 1024
#             )

#             if not data:
#                 break

#             sha256.update(
#                 data
#             )

#     return sha256.hexdigest()


# def load_ingestion_state() -> Dict[str, Any]:
#     """
#     Load information about previously processed PDFs.
#     """

#     if not INGESTION_STATE_FILE.exists():

#         return {
#             "documents": {}
#         }

#     try:

#         with INGESTION_STATE_FILE.open(
#             "r",
#             encoding="utf-8",
#         ) as file:

#             state = json.load(
#                 file
#             )

#         if not isinstance(
#             state,
#             dict,
#         ):

#             return {
#                 "documents": {}
#             }

#         state.setdefault(
#             "documents",
#             {},
#         )

#         return state

#     except Exception as exc:

#         logger.warning(
#             "Could not load ingestion state: %s",
#             exc,
#         )

#         return {
#             "documents": {}
#         }


# def save_ingestion_state(
#     state: Dict[str, Any],
# ) -> None:
#     """
#     Save document ingestion state.
#     """

#     PROCESSED_DATA_DIR.mkdir(
#         parents=True,
#         exist_ok=True,
#     )

#     with INGESTION_STATE_FILE.open(
#         "w",
#         encoding="utf-8",
#     ) as file:

#         json.dump(
#             state,
#             file,
#             indent=2,
#             ensure_ascii=False,
#         )


# def get_pdf_files() -> List[Path]:
#     """
#     Find all PDFs inside backend/data/raw.

#     Uses recursive search so PDFs inside subdirectories are
#     also detected.
#     """

#     if not RAW_DATA_DIR.exists():

#         RAW_DATA_DIR.mkdir(
#             parents=True,
#             exist_ok=True,
#         )

#         return []

#     pdf_files = sorted(
#         [
#             path
#             for path in RAW_DATA_DIR.rglob("*")
#             if (
#                 path.is_file()
#                 and path.suffix.lower()
#                 == ".pdf"
#             )
#         ]
#     )

#     return pdf_files


# # ============================================================
# # Document Ingestion Pipeline
# # ============================================================

# class DocumentIngestionPipeline:
#     """
#     Orchestrates PDF ingestion into ChromaDB.
#     """

#     def __init__(
#         self,
#         force_reindex: bool = False,
#     ) -> None:

#         self.force_reindex = (
#             force_reindex
#         )

#         # ----------------------------------------------------
#         # Validate Required Classes
#         # ----------------------------------------------------

#         missing = []

#         if PDFExtractor is None:
#             missing.append(
#                 "PDFExtractor"
#             )

#         if Chunker is None:
#             missing.append(
#                 "Chunker"
#             )

#         if EmbeddingService is None:
#             missing.append(
#                 "EmbeddingService"
#             )

#         if ChromaStore is None:
#             missing.append(
#                 "ChromaStore"
#             )

#         if missing:

#             raise IngestionError(
#                 "Required project classes could not "
#                 "be imported: "
#                 + ", ".join(missing)
#                 + ". Check your class names and imports."
#             )

#         # ----------------------------------------------------
#         # Initialize Components
#         # ----------------------------------------------------

#         logger.info(
#             "Initializing ingestion components..."
#         )

#         self.pdf_extractor = (
#             PDFExtractor()
#         )

#         self.text_cleaner = (
#             TextCleaner()
#             if TextCleaner is not None
#             else None
#         )

#         self.metadata_builder = (
#             MetadataBuilder()
#             if MetadataBuilder is not None
#             else None
#         )

#         self.chunker = (
#             Chunker()
#         )

#         self.embedding_service = (
#             EmbeddingService()
#         )

#         self.chroma_store = (
#             ChromaStore()
#         )

#         self.state = (
#             load_ingestion_state()
#         )

#         logger.info(
#             "Ingestion components initialized."
#         )

#     # ========================================================
#     # Main Ingestion
#     # ========================================================

#     def run(
#         self,
#     ) -> None:
#         """
#         Process all PDFs in data/raw.
#         """

#         print(
#             "\n"
#             + "=" * 60
#         )

#         print(
#             "JANMITRA - DOCUMENT INGESTION"
#         )

#         print(
#             "=" * 60
#         )

#         pdf_files = (
#             get_pdf_files()
#         )

#         if not pdf_files:

#             print(
#                 "\nNo PDF files found in:"
#             )

#             print(
#                 RAW_DATA_DIR
#             )

#             return

#         logger.info(
#             "Found %d PDF file(s).",
#             len(pdf_files),
#         )

#         successful = 0
#         skipped = 0
#         failed = 0
#         total_chunks = 0

#         start_time = (
#             time.perf_counter()
#         )

#         for index, pdf_path in enumerate(
#             pdf_files,
#             start=1,
#         ):

#             print(
#                 "\n"
#                 + "-" * 60
#             )

#             print(
#                 f"[{index}/{len(pdf_files)}] "
#                 f"{pdf_path.name}"
#             )

#             print(
#                 "-" * 60
#             )

#             try:

#                 result = (
#                     self.process_document(
#                         pdf_path
#                     )
#                 )

#                 if result is None:

#                     skipped += 1

#                 else:

#                     successful += 1

#                     total_chunks += (
#                         result
#                     )

#             except Exception as exc:

#                 failed += 1

#                 logger.exception(
#                     "Failed to process %s",
#                     pdf_path.name,
#                 )

#                 print(
#                     f"FAILED: {exc}"
#                 )

#         elapsed = (
#             time.perf_counter()
#             - start_time
#         )

#         # ----------------------------------------------------
#         # Final Summary
#         # ----------------------------------------------------

#         print(
#             "\n"
#             + "=" * 60
#         )

#         print(
#             "INGESTION COMPLETE"
#         )

#         print(
#             "=" * 60
#         )

#         print(
#             f"PDFs found:       "
#             f"{len(pdf_files)}"
#         )

#         print(
#             f"Successfully processed: "
#             f"{successful}"
#         )

#         print(
#             f"Skipped:          "
#             f"{skipped}"
#         )

#         print(
#             f"Failed:           "
#             f"{failed}"
#         )

#         print(
#             f"Chunks processed: "
#             f"{total_chunks}"
#         )

#         print(
#             f"Time:             "
#             f"{elapsed:.2f}s"
#         )

#         print(
#             "\nChromaDB records: "
#             f"{self._get_collection_count()}"
#         )

#     # ========================================================
#     # Process Single PDF
#     # ========================================================

#     def process_document(
#         self,
#         pdf_path: Path,
#     ) -> Optional[int]:
#         """
#         Process one PDF from extraction through ChromaDB.

#         Returns:
#             Number of chunks indexed.

#             None when document is skipped.
#         """

#         file_hash = (
#             calculate_file_hash(
#                 pdf_path
#             )
#         )

#         relative_path = str(
#             pdf_path.relative_to(
#                 RAW_DATA_DIR
#             )
#         )

#         existing = (
#             self.state
#             .get(
#                 "documents",
#                 {},
#             )
#             .get(
#                 relative_path
#             )
#         )

#         # ----------------------------------------------------
#         # Skip Unchanged Documents
#         # ----------------------------------------------------

#         if (
#             not self.force_reindex
#             and existing
#             and existing.get(
#                 "sha256"
#             ) == file_hash
#             and existing.get(
#                 "status"
#             ) == "success"
#         ):

#             logger.info(
#                 "Skipping already processed PDF: %s",
#                 pdf_path.name,
#             )

#             print(
#                 "Already processed - skipping."
#             )

#             return None

#         logger.info(
#             "Processing PDF: %s",
#             pdf_path.name,
#         )

#         # ====================================================
#         # STEP 1: Extract PDF
#         # ====================================================

#         logger.info(
#             "Step 1/5 - Extracting PDF text..."
#         )

#         extracted = (
#             self._extract_pdf(
#                 pdf_path
#             )
#         )

#         if extracted is None:

#             raise IngestionError(
#                 "PDF extractor returned no data."
#             )

#         # ====================================================
#         # STEP 2: Normalize Extracted Pages
#         # ====================================================

#         pages = (
#             self._normalize_pages(
#                 extracted,
#                 pdf_path,
#             )
#         )

#         if not pages:

#             raise IngestionError(
#                 "No text could be extracted "
#                 "from the PDF."
#             )

#         logger.info(
#             "Extracted %d page(s) "
#             "containing text.",
#             len(pages),
#         )

#         # ====================================================
#         # STEP 3: Clean Text + Build Metadata + Chunk
#         # ====================================================

#         logger.info(
#             "Step 2/5 - Cleaning and chunking..."
#         )

#         all_chunks: List[
#             Dict[str, Any]
#         ] = []

#         for page in pages:

#             text = (
#                 page.get(
#                     "text",
#                     ""
#                 )
#             )

#             if not text.strip():

#                 continue

#             cleaned_text = (
#                 self._clean_text(
#                     text
#                 )
#             )

#             if not cleaned_text:

#                 continue

#             metadata = (
#                 self._build_metadata(
#                     pdf_path=pdf_path,
#                     page=page,
#                     file_hash=file_hash,
#                 )
#             )

#             page_chunks = (
#                 self._chunk_text(
#                     text=cleaned_text,
#                     metadata=metadata,
#                 )
#             )

#             all_chunks.extend(
#                 page_chunks
#             )

#         if not all_chunks:

#             raise IngestionError(
#                 "No chunks were generated."
#             )

#         logger.info(
#             "Generated %d chunk(s).",
#             len(all_chunks),
#         )

#         # ====================================================
#         # STEP 4: Generate Embeddings
#         # ====================================================

#         logger.info(
#             "Step 3/5 - Generating embeddings..."
#         )

#         texts = [
#             chunk["text"]
#             for chunk in all_chunks
#         ]

#         embeddings = (
#             self._generate_embeddings(
#                 texts
#             )
#         )

#         if len(
#             embeddings
#         ) != len(
#             all_chunks
#         ):

#             raise IngestionError(
#                 "Number of embeddings does not "
#                 "match number of chunks."
#             )

#         # ====================================================
#         # STEP 5: Prepare IDs
#         # ====================================================

#         logger.info(
#             "Step 4/5 - Preparing ChromaDB records..."
#         )

#         ids: List[str] = []
#         metadatas: List[
#             Dict[str, Any]
#         ] = []

#         for index, chunk in enumerate(
#             all_chunks
#         ):

#             chunk_id = (
#                 f"{file_hash[:16]}"
#                 f"_chunk_{index:06d}"
#             )

#             ids.append(
#                 chunk_id
#             )

#             metadata = dict(
#                 chunk.get(
#                     "metadata",
#                     {},
#                 )
#             )

#             metadata[
#                 "chunk_id"
#             ] = chunk_id

#             metadata[
#                 "chunk_index"
#             ] = index

#             # Chroma metadata should contain simple values.

#             metadata = (
#                 self._sanitize_metadata(
#                     metadata
#                 )
#             )

#             metadatas.append(
#                 metadata
#             )

#         # ====================================================
#         # STEP 6: Store in ChromaDB
#         # ====================================================

#         logger.info(
#             "Step 5/5 - Storing in ChromaDB..."
#         )

#         self._store_in_chroma(
#             ids=ids,
#             texts=texts,
#             embeddings=embeddings,
#             metadatas=metadatas,
#         )

#         # ====================================================
#         # Save State
#         # ====================================================

#         self.state.setdefault(
#             "documents",
#             {},
#         )

#         self.state[
#             "documents"
#         ][
#             relative_path
#         ] = {
#             "sha256": (
#                 file_hash
#             ),
#             "status": (
#                 "success"
#             ),
#             "chunks": (
#                 len(all_chunks)
#             ),
#             "file_name": (
#                 pdf_path.name
#             ),
#         }

#         save_ingestion_state(
#             self.state
#         )

#         logger.info(
#             "Successfully indexed %s | chunks=%d",
#             pdf_path.name,
#             len(all_chunks),
#         )

#         print(
#             f"SUCCESS - "
#             f"{len(all_chunks)} chunks indexed."
#         )

#         return len(
#             all_chunks
#         )

#     # ========================================================
#     # PDF Extraction Adapter
#     # ========================================================

#     def _extract_pdf(
#         self,
#         pdf_path: Path,
#     ) -> Any:
#         """
#         Support common PDFExtractor interfaces.
#         """

#         if hasattr(
#             self.pdf_extractor,
#             "extract",
#         ):

#             return (
#                 self.pdf_extractor.extract(
#                     str(pdf_path)
#                 )
#             )

#         if hasattr(
#             self.pdf_extractor,
#             "extract_pdf",
#         ):

#             return (
#                 self.pdf_extractor.extract_pdf(
#                     str(pdf_path)
#                 )
#             )

#         if hasattr(
#             self.pdf_extractor,
#             "process",
#         ):

#             return (
#                 self.pdf_extractor.process(
#                     str(pdf_path)
#                 )
#             )

#         raise IngestionError(
#             "PDFExtractor must implement "
#             "extract(), extract_pdf(), or process()."
#         )

#     # ========================================================
#     # Normalize PDF Pages
#     # ========================================================

#     @staticmethod
#     def _normalize_pages(
#         extracted: Any,
#         pdf_path: Path,
#     ) -> List[Dict[str, Any]]:
#         """
#         Convert extractor output into:

#             [
#                 {
#                     "text": "...",
#                     "page_number": 1
#                 }
#             ]
#         """

#         pages: List[
#             Dict[str, Any]
#         ] = []

#         # ----------------------------------------------------
#         # Plain String
#         # ----------------------------------------------------

#         if isinstance(
#             extracted,
#             str,
#         ):

#             if extracted.strip():

#                 pages.append(
#                     {
#                         "text":
#                             extracted,

#                         "page_number":
#                             1,
#                     }
#                 )

#             return pages

#         # ----------------------------------------------------
#         # Dictionary
#         # ----------------------------------------------------

#         if isinstance(
#             extracted,
#             dict,
#         ):

#             possible_pages = (
#                 extracted.get(
#                     "pages"
#                 )
#             )

#             if isinstance(
#                 possible_pages,
#                 list,
#             ):

#                 extracted = (
#                     possible_pages
#                 )

#             else:

#                 text = (
#                     extracted.get(
#                         "text"
#                     )
#                     or extracted.get(
#                         "content"
#                     )
#                     or ""
#                 )

#                 if text:

#                     pages.append(
#                         {
#                             "text":
#                                 str(text),

#                             "page_number":
#                                 extracted.get(
#                                     "page_number",
#                                     1,
#                                 ),
#                         }
#                     )

#                 return pages

#         # ----------------------------------------------------
#         # List
#         # ----------------------------------------------------

#         if isinstance(
#             extracted,
#             list,
#         ):

#             for index, item in enumerate(
#                 extracted,
#                 start=1,
#             ):

#                 if isinstance(
#                     item,
#                     str,
#                 ):

#                     text = item

#                     page_number = (
#                         index
#                     )

#                 elif isinstance(
#                     item,
#                     dict,
#                 ):

#                     text = (
#                         item.get(
#                             "text"
#                         )
#                         or item.get(
#                             "content"
#                         )
#                         or item.get(
#                             "page_text"
#                         )
#                         or ""
#                     )

#                     page_number = (
#                         item.get(
#                             "page_number"
#                         )
#                         or item.get(
#                             "page"
#                         )
#                         or index
#                     )

#                 else:

#                     text = getattr(
#                         item,
#                         "text",
#                         "",
#                     )

#                     page_number = getattr(
#                         item,
#                         "page_number",
#                         index,
#                     )

#                 if str(
#                     text
#                 ).strip():

#                     pages.append(
#                         {
#                             "text":
#                                 str(text),

#                             "page_number":
#                                 page_number,
#                         }
#                     )

#         return pages

#     # ========================================================
#     # Text Cleaning Adapter
#     # ========================================================

#     def _clean_text(
#         self,
#         text: str,
#     ) -> str:

#         if self.text_cleaner is None:

#             return (
#                 " ".join(
#                     text.split()
#                 )
#             )

#         if hasattr(
#             self.text_cleaner,
#             "clean",
#         ):

#             return (
#                 self.text_cleaner.clean(
#                     text
#                 )
#             )

#         if hasattr(
#             self.text_cleaner,
#             "clean_text",
#         ):

#             return (
#                 self.text_cleaner.clean_text(
#                     text
#                 )
#             )

#         if hasattr(
#             self.text_cleaner,
#             "process",
#         ):

#             return (
#                 self.text_cleaner.process(
#                     text
#                 )
#             )

#         return (
#             " ".join(
#                 text.split()
#             )
#         )

#     # ========================================================
#     # Metadata Builder Adapter
#     # ========================================================

#     def _build_metadata(
#         self,
#         pdf_path: Path,
#         page: Dict[str, Any],
#         file_hash: str,
#     ) -> Dict[str, Any]:

#         base_metadata = {
#             "file_name":
#                 pdf_path.name,

#             "source":
#                 str(pdf_path),

#             "page_number":
#                 page.get(
#                     "page_number",
#                     1,
#                 ),

#             "document_id":
#                 file_hash[:16],
#         }

#         if self.metadata_builder is None:

#             return (
#                 base_metadata
#             )

#         try:

#             if hasattr(
#                 self.metadata_builder,
#                 "build",
#             ):

#                 metadata = (
#                     self.metadata_builder.build(
#                         file_path=str(
#                             pdf_path
#                         ),
#                         page_number=page.get(
#                             "page_number",
#                             1,
#                         ),
#                     )
#                 )

#                 if isinstance(
#                     metadata,
#                     dict,
#                 ):

#                     base_metadata.update(
#                         metadata
#                     )

#         except TypeError:

#             # Different MetadataBuilder interface.
#             # Fall back to safe base metadata.

#             pass

#         return base_metadata

#     # ========================================================
#     # Chunking Adapter
#     # ========================================================

#     def _chunk_text(
#         self,
#         text: str,
#         metadata: Dict[str, Any],
#     ) -> List[Dict[str, Any]]:
#         """
#         Chunk one already-extracted PDF page using the existing
#         DocumentChunker.chunk_page(document, page) interface.

#         The project's DocumentChunker expects two dictionaries:
#             - document
#             - page

#         This adapter converts the ingestion pipeline's page text
#         and metadata into those structures and normalizes the
#         returned chunks for embedding and ChromaDB storage.
#         """

#         page_number = metadata.get(
#             "page_number",
#             1,
#         )

#         source_file = (
#             metadata.get("source_file")
#             or metadata.get("file_name")
#             or "unknown.pdf"
#         )

#         document_id = metadata.get(
#             "document_id",
#             "unknown_document",
#         )

#         # ----------------------------------------------------
#         # Build document structure expected by DocumentChunker
#         # ----------------------------------------------------

#         document = {
#             "document_id": document_id,
#             "source_file": source_file,
#             "document_metadata": {
#                 "document_id": document_id,
#                 "source_file": source_file,
#                 "file_name": source_file,
#                 "title": metadata.get(
#                     "title",
#                     "",
#                 ),
#                 "category": metadata.get(
#                     "category",
#                     "GENERAL",
#                 ),
#                 "subcategory": metadata.get(
#                     "subcategory",
#                     "general",
#                 ),
#                 "service": metadata.get(
#                     "service",
#                     "general_information",
#                 ),
#                 "document_type": metadata.get(
#                     "document_type",
#                     "GENERAL_DOCUMENT",
#                 ),
#                 "state": metadata.get(
#                     "state",
#                     "unknown",
#                 ),
#                 "jurisdiction": metadata.get(
#                     "jurisdiction",
#                     "unknown",
#                 ),
#                 "language": metadata.get(
#                     "language",
#                     "unknown",
#                 ),
#             },
#         }

#         # ----------------------------------------------------
#         # Build page structure expected by DocumentChunker
#         # ----------------------------------------------------

#         page = {
#             "page_number": page_number,
#             "cleaned_text": text,
#             "text": text,
#             "page_text": text,
#             "metadata": {
#                 **metadata,
#                 "page_number": page_number,
#             },
#         }

#         # ----------------------------------------------------
#         # Call the actual JanMitra DocumentChunker interface
#         # ----------------------------------------------------

#         if not hasattr(
#             self.chunker,
#             "chunk_page",
#         ):
#             raise IngestionError(
#                 "DocumentChunker does not implement chunk_page()."
#             )

#         result = self.chunker.chunk_page(
#             document,
#             page,
#         )

#         if not result:
#             return []

#         # Some implementations may wrap chunks in a dictionary.
#         if isinstance(
#             result,
#             dict,
#         ):
#             nested = (
#                 result.get("chunks")
#                 or result.get("data")
#                 or result.get("results")
#             )

#             if isinstance(
#                 nested,
#                 list,
#             ):
#                 result = nested
#             else:
#                 result = [
#                     result
#                 ]

#         if not isinstance(
#             result,
#             (list, tuple),
#         ):
#             try:
#                 result = list(
#                     result
#                 )
#             except TypeError:
#                 result = [
#                     result
#                 ]

#         # ----------------------------------------------------
#         # Normalize returned chunks
#         # ----------------------------------------------------

#         normalized: List[
#             Dict[str, Any]
#         ] = []

#         for item in result:

#             if isinstance(
#                 item,
#                 str,
#             ):
#                 chunk_text = item
#                 chunk_metadata = dict(
#                     metadata
#                 )

#             elif isinstance(
#                 item,
#                 dict,
#             ):
#                 chunk_text = (
#                     item.get("text")
#                     or item.get("content")
#                     or item.get("chunk_text")
#                     or item.get("page_text")
#                     or ""
#                 )

#                 chunk_metadata = dict(
#                     metadata
#                 )

#                 item_metadata = item.get(
#                     "metadata",
#                     {},
#                 )

#                 if isinstance(
#                     item_metadata,
#                     dict,
#                 ):
#                     chunk_metadata.update(
#                         item_metadata
#                     )

#                 # Preserve useful fields produced by DocumentChunker.
#                 field_map = {
#                     "chunk_id": "original_chunk_id",
#                     "word_count": "word_count",
#                     "character_count": "character_count",
#                     "chunk_index": "chunk_index",
#                     "chunk_index_on_page": "chunk_index_on_page",
#                     "total_chunks_on_page": "total_chunks_on_page",
#                     "page_number": "page_number",
#                 }

#                 for source_key, target_key in field_map.items():
#                     value = item.get(
#                         source_key
#                     )

#                     if value is not None:
#                         chunk_metadata[
#                             target_key
#                         ] = value

#             else:
#                 chunk_text = (
#                     getattr(
#                         item,
#                         "text",
#                         None,
#                     )
#                     or getattr(
#                         item,
#                         "content",
#                         None,
#                     )
#                     or getattr(
#                         item,
#                         "chunk_text",
#                         None,
#                     )
#                     or ""
#                 )

#                 chunk_metadata = dict(
#                     metadata
#                 )

#                 item_metadata = getattr(
#                     item,
#                     "metadata",
#                     None,
#                 )

#                 if isinstance(
#                     item_metadata,
#                     dict,
#                 ):
#                     chunk_metadata.update(
#                         item_metadata
#                     )

#             chunk_text = str(
#                 chunk_text
#             ).strip()

#             if not chunk_text:
#                 continue

#             normalized.append(
#                 {
#                     "text": chunk_text,
#                     "metadata": chunk_metadata,
#                 }
#             )

#         if not normalized:
#             raise IngestionError(
#                 "DocumentChunker returned data, but no valid "
#                 "text chunks could be normalized."
#             )

#         return normalized

#     # ========================================================
#     # Embedding Adapter
#     # ========================================================

#     def _generate_embeddings(
#         self,
#         texts: List[str],
#     ) -> List[List[float]]:

#         result = None

#         if hasattr(
#             self.embedding_service,
#             "embed_documents",
#         ):

#             result = (
#                 self.embedding_service
#                 .embed_documents(
#                     texts
#                 )
#             )

#         elif hasattr(
#             self.embedding_service,
#             "embed_texts",
#         ):

#             result = (
#                 self.embedding_service
#                 .embed_texts(
#                     texts
#                 )
#             )

#         elif hasattr(
#             self.embedding_service,
#             "encode",
#         ):

#             result = (
#                 self.embedding_service
#                 .encode(
#                     texts
#                 )
#             )

#         elif hasattr(
#             self.embedding_service,
#             "embed",
#         ):

#             try:

#                 result = (
#                     self.embedding_service
#                     .embed(
#                         texts
#                     )
#                 )

#             except Exception:

#                 result = [
#                     self.embedding_service
#                     .embed(
#                         text
#                     )
#                     for text in texts
#                 ]

#         else:

#             raise IngestionError(
#                 "EmbeddingService must implement "
#                 "embed_documents(), embed_texts(), "
#                 "encode(), or embed()."
#             )

#         # NumPy array support.

#         if hasattr(
#             result,
#             "tolist",
#         ):

#             result = (
#                 result.tolist()
#             )

#         return list(
#             result
#         )

#     # ========================================================
#     # ChromaDB Adapter
#     # ========================================================

#     def _store_in_chroma(
#         self,
#         ids: List[str],
#         texts: List[str],
#         embeddings: List[List[float]],
#         metadatas: List[Dict[str, Any]],
#     ) -> None:
#         """
#         Store generated records in ChromaDB.

#         Supports common ChromaStore interfaces.
#         """

#         # ----------------------------------------------------
#         # Custom upsert method
#         # ----------------------------------------------------

#         if hasattr(
#             self.chroma_store,
#             "upsert",
#         ):

#             try:

#                 self.chroma_store.upsert(
#                     ids=ids,
#                     documents=texts,
#                     embeddings=embeddings,
#                     metadatas=metadatas,
#                 )

#                 return

#             except TypeError:

#                 pass

#         # ----------------------------------------------------
#         # Custom add method
#         # ----------------------------------------------------

#         if hasattr(
#             self.chroma_store,
#             "add",
#         ):

#             try:

#                 self.chroma_store.add(
#                     ids=ids,
#                     documents=texts,
#                     embeddings=embeddings,
#                     metadatas=metadatas,
#                 )

#                 return

#             except TypeError:

#                 pass

#         # ----------------------------------------------------
#         # add_documents method
#         # ----------------------------------------------------

#         if hasattr(
#             self.chroma_store,
#             "add_documents",
#         ):

#             try:

#                 self.chroma_store.add_documents(
#                     ids=ids,
#                     documents=texts,
#                     embeddings=embeddings,
#                     metadatas=metadatas,
#                 )

#                 return

#             except TypeError:

#                 pass

#         # ----------------------------------------------------
#         # Direct Chroma collection
#         # ----------------------------------------------------

#         collection = getattr(
#             self.chroma_store,
#             "collection",
#             None,
#         )

#         if collection is not None:

#             collection.upsert(
#                 ids=ids,
#                 documents=texts,
#                 embeddings=embeddings,
#                 metadatas=metadatas,
#             )

#             return

#         raise IngestionError(
#             "Could not find a supported method "
#             "for storing records in ChromaDB."
#         )

#     # ========================================================
#     # Metadata Sanitizer
#     # ========================================================

#     @staticmethod
#     def _sanitize_metadata(
#         metadata: Dict[str, Any],
#     ) -> Dict[str, Any]:

#         sanitized = {}

#         for key, value in (
#             metadata.items()
#         ):

#             if value is None:

#                 continue

#             if isinstance(
#                 value,
#                 (
#                     str,
#                     int,
#                     float,
#                     bool,
#                 ),
#             ):

#                 sanitized[
#                     str(key)
#                 ] = value

#             else:

#                 sanitized[
#                     str(key)
#                 ] = str(
#                     value
#                 )

#         return sanitized

#     # ========================================================
#     # Collection Count
#     # ========================================================

#     def _get_collection_count(
#         self,
#     ) -> Any:

#         try:

#             collection = getattr(
#                 self.chroma_store,
#                 "collection",
#                 None,
#             )

#             if collection is not None:

#                 return (
#                     collection.count()
#                 )

#             if hasattr(
#                 self.chroma_store,
#                 "count",
#             ):

#                 return (
#                     self.chroma_store.count()
#                 )

#         except Exception:

#             pass

#         return "Unknown"


# # ============================================================
# # Main
# # ============================================================

# def main() -> None:
#     """
#     Main entry point.
#     """

#     try:

#         pipeline = (
#             DocumentIngestionPipeline(
#                 force_reindex=False
#             )
#         )

#         pipeline.run()

#     except KeyboardInterrupt:

#         print(
#             "\nIngestion cancelled."
#         )

#     except Exception as exc:

#         logger.exception(
#             "Document ingestion failed."
#         )

#         print(
#             "\nINGESTION FAILED"
#         )

#         print(
#             exc
#         )

#         sys.exit(
#             1
#         )


# # ============================================================
# # Entry Point
# # ============================================================

# if __name__ == "__main__":
#     main()














"""
ingest_documents.py

===============================================================================
JanMitra AI -- Document Ingestion Entry Point
-------------------------------------------------------------------------------

Wires everything together:

    document_analyzer.py   -> decides pymupdf vs sarvam per PDF
    sarvam_processor.py    -> OCR/layout pipeline for scanned/complex PDFs
    document_normalizer.py -> shared schema + local text/image/table
                               extraction
    router.py               -> runs the above per file, batches a folder

...and adds the last mile: reading every PDF out of data/raw/, writing
one normalized JSON (+ extracted images) per PDF into data/processed/,
and flattening all of it into a single corpus.jsonl ready to hand to
an embedding / RAG ingestion step.

Usage
-----
    python ingest_documents.py
    python ingest_documents.py --input-dir data/raw --output-dir data/processed
    python ingest_documents.py --force-processor sarvam --output-format html
    python ingest_documents.py --no-fallback

This file expects document_analyzer.py, sarvam_processor.py,
document_normalizer.py, and router.py to live alongside it.
===============================================================================
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
import sys

from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from preprocessing.document_analyzer import DocumentAnalyzer
from preprocessing.sarvam_processor import SarvamProcessor, SarvamConfig
from preprocessing.document_normalizer import document_from_dict
from preprocessing.router import DocumentRouter, RouteResult


logger = logging.getLogger("ingest_documents")

if not logger.handlers:

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(message)s"
    )

    stream = logging.StreamHandler()

    stream.setFormatter(formatter)

    logger.addHandler(stream)


DEFAULT_INPUT_DIR = "data/raw"

DEFAULT_OUTPUT_DIR = "data/processed"


# =============================================================================
# Setup
# =============================================================================

def build_router(
    language: str = "en-IN",
    output_format: str = "md",
    force_processor: Optional[str] = None,
    fallback_to_pymupdf: bool = True,
) -> DocumentRouter:
    """
    Wires up DocumentAnalyzer + (optional) SarvamProcessor into a
    DocumentRouter, reading SARVAM_API_KEY from the environment.
    Missing the key is not fatal: the router falls back to local
    pymupdf extraction for everything unless fallback_to_pymupdf=False.
    """

    load_dotenv()

    api_key = os.getenv("SARVAM_API_KEY")

    sarvam_processor: Optional[SarvamProcessor] = None

    if api_key:

        sarvam_processor = SarvamProcessor(
            SarvamConfig(
                api_key=api_key,
                language=language,
                output_format=output_format,
            )
        )

        logger.info("Sarvam processor configured (language=%s, format=%s).",
                    language, output_format)

    else:

        logger.warning(
            "SARVAM_API_KEY not set; documents that need Sarvam will %s.",
            "fall back to local pymupdf extraction"
            if fallback_to_pymupdf else "fail",
        )

    return DocumentRouter(
        analyzer=DocumentAnalyzer(),
        sarvam_processor=sarvam_processor,
        force_processor=force_processor,
        fallback_to_pymupdf=fallback_to_pymupdf,
    )


# =============================================================================
# Corpus Building
# =============================================================================

def build_corpus(
    output_dir: Path,
    results: List[RouteResult],
) -> Path:
    """
    Reads every successfully-processed <document_id>.json back off disk
    and flattens all blocks (text, table, image) from every document
    into a single JSONL file -- one line per block -- ready to feed an
    embedding / RAG ingestion step. Each line carries enough metadata
    (source file, page, layout, confidence, image_path) to trace a
    chunk back to its origin.
    """

    corpus_path = output_dir / "corpus.jsonl"

    chunk_count = 0

    with open(corpus_path, "w", encoding="utf-8") as out:

        for result in results:

            if result.status != "success" or not result.output_path:

                continue

            doc_json_path = Path(result.output_path)

            if not doc_json_path.exists():

                logger.warning(
                    "Expected output missing for %s: %s",
                    result.document_id, doc_json_path,
                )

                continue

            with open(doc_json_path, "r", encoding="utf-8") as f:

                document = document_from_dict(json.load(f))

            for page in document.pages:

                for block in page.blocks:

                    chunk = {
                        "chunk_id": (
                            f"{result.document_id}_p{page.page_number}"
                            f"_b{block.reading_order}"
                        ),
                        "document_id": result.document_id,
                        "source_file": document.source_file,
                        "processor_used": result.processor_used,
                        "page_number": page.page_number,
                        "layout": block.layout,
                        "text": block.text,
                        "confidence": block.confidence,
                        "reading_order": block.reading_order,
                        "coordinates": block.coordinates,
                        "image_path": block.image_path,
                    }

                    out.write(json.dumps(chunk, ensure_ascii=False) + "\n")

                    chunk_count += 1

    logger.info(
        "Corpus written: %d chunks from %d document(s) -> %s",
        chunk_count,
        sum(1 for r in results if r.status == "success"),
        corpus_path,
    )

    return corpus_path


# =============================================================================
# Summary
# =============================================================================

def print_summary(
    results: List[RouteResult],
    elapsed_seconds: float,
) -> None:

    total = len(results)

    succeeded = [r for r in results if r.status == "success"]

    failed = [r for r in results if r.status == "failed"]

    by_processor: Dict[str, int] = {}

    for r in succeeded:

        by_processor[r.processor_used] = by_processor.get(
            r.processor_used, 0
        ) + 1

    print("=" * 60)
    print("INGESTION SUMMARY")
    print("=" * 60)
    print(f"Total PDFs   : {total}")
    print(f"Succeeded    : {len(succeeded)}")
    print(f"Failed       : {len(failed)}")

    for processor, count in sorted(by_processor.items()):

        print(f"  via {processor:<8}: {count}")

    print(f"Elapsed      : {elapsed_seconds:.1f}s")

    if failed:

        print("-" * 60)
        print("Failed documents:")

        for r in failed:

            print(f"  - {r.document_id}: {r.error}")

    print("=" * 60)


# =============================================================================
# Main Ingestion Flow
# =============================================================================

def ingest(
    input_dir: Path,
    output_dir: Path,
    pattern: str = "*.pdf",
    language: str = "en-IN",
    output_format: str = "md",
    force_processor: Optional[str] = None,
    fallback_to_pymupdf: bool = True,
) -> List[RouteResult]:

    input_dir = Path(input_dir)

    output_dir = Path(output_dir)

    if not input_dir.exists():

        input_dir.mkdir(parents=True, exist_ok=True)

        logger.warning(
            "%s did not exist; created it. Drop PDFs there and re-run.",
            input_dir,
        )

        return []

    pdf_count = len(list(input_dir.glob(pattern)))

    if pdf_count == 0:

        logger.warning(
            "No files matching %s in %s -- nothing to do.",
            pattern, input_dir,
        )

        return []

    logger.info(
        "Found %d file(s) matching %s in %s", pdf_count, pattern, input_dir
    )

    router = build_router(
        language=language,
        output_format=output_format,
        force_processor=force_processor,
        fallback_to_pymupdf=fallback_to_pymupdf,
    )

    start = time.perf_counter()

    results = router.process_directory(
        input_dir, output_dir, pattern=pattern
    )

    build_corpus(output_dir, results)

    print_summary(results, time.perf_counter() - start)

    return results


# =============================================================================
# CLI Entry Point
# =============================================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Ingest every PDF in a folder: analyze, route between "
            "local extraction and Sarvam Document Intelligence, "
            "normalize, and build a consolidated RAG-ready corpus."
        )
    )

    parser.add_argument(
        "--input-dir", default=DEFAULT_INPUT_DIR,
        help=f"Folder of source PDFs (default: {DEFAULT_INPUT_DIR})",
    )

    parser.add_argument(
        "--output-dir", default=DEFAULT_OUTPUT_DIR,
        help=f"Folder to write normalized output (default: {DEFAULT_OUTPUT_DIR})",
    )

    parser.add_argument(
        "--pattern", default="*.pdf",
        help="Glob pattern for source files",
    )

    parser.add_argument(
        "--language", default="en-IN",
        help="Sarvam target language code (BCP-47), e.g. en-IN, hi-IN",
    )

    parser.add_argument(
        "--output-format", default="md", choices=["md", "html"],
        help=(
            "Sarvam output format. Use 'html' to preserve table "
            "structure; 'md' is more compact for plain text."
        ),
    )

    parser.add_argument(
        "--force-processor",
        choices=["pymupdf", "sarvam", "hybrid"],
        default=None,
        help="Skip analysis and force a specific processor for every file",
    )

    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help=(
            "Fail a document instead of falling back to pymupdf when "
            "Sarvam is needed but unavailable"
        ),
    )

    args = parser.parse_args()

    ingest(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        pattern=args.pattern,
        language=args.language,
        output_format=args.output_format,
        force_processor=args.force_processor,
        fallback_to_pymupdf=not args.no_fallback,
    )


if __name__ == "__main__":

    main()