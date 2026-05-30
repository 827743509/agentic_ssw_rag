from __future__ import annotations

import json
import mimetypes
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.core.config import BASE_DIR
from app.db.object_storage import (
    delete_file_object,
    file_object_exists,
    stream_file_object,
    upload_file_object,
)
from app.db.vector_store import build_vector_store
from app.utils.ingest import DEFAULT_EXTS, ingest_file
from app.utils.rag import build_index


DATA_DIR = BASE_DIR / "data"
TEMP_DIR = DATA_DIR / "tmp"
MANIFEST_PATH = DATA_DIR / "documents.json"


class DocumentRecord(BaseModel):
    id: str
    file_name: str
    stored_name: str
    size: int
    node_count: int
    uploaded_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentRecord]


class DocumentUploadResponse(BaseModel):
    document: DocumentRecord


class DocumentDeleteResponse(BaseModel):
    deleted: bool
    vector_deleted: bool
    document: DocumentRecord


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


def _ensure_storage() -> None:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    if not MANIFEST_PATH.exists():
        MANIFEST_PATH.write_text("[]", encoding="utf-8")


def _read_manifest() -> list[DocumentRecord]:
    _ensure_storage()
    try:
        raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raw = []
    return [DocumentRecord.model_validate(item) for item in raw]


def _write_manifest(records: list[DocumentRecord]) -> None:
    _ensure_storage()
    payload = [record.model_dump() for record in records]
    tmp_path = MANIFEST_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp_path.replace(MANIFEST_PATH)


def _safe_file_name(filename: str | None) -> str:
    name = Path(filename or "").name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    return re.sub(r"[\x00-\x1f<>:\"/\\|?*]+", "_", name)


def _save_upload_file(upload_file: UploadFile, target_path: Path) -> None:
    upload_file.file.seek(0)
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)


def _delete_document_vectors(document_id: str) -> bool:
    vector_store = build_vector_store(overwrite=False)
    try:
        vector_store.delete(ref_doc_id=document_id)
    except TypeError:
        vector_store.delete(document_id)
    build_index.cache_clear()
    return True


def _find_document(document_id: str) -> DocumentRecord:
    records = _read_manifest()
    target = next((record for record in records if record.id == document_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    return target


def _object_name(document_id: str, filename: str) -> str:
    return f"{document_id}/{filename}"


def _content_type(upload_file: UploadFile, filename: str) -> str:
    guessed_type, _ = mimetypes.guess_type(filename)
    return upload_file.content_type or guessed_type or "application/octet-stream"


def _create_document(upload_file: UploadFile) -> DocumentRecord:
    _ensure_storage()
    original_name = _safe_file_name(upload_file.filename)
    suffix = Path(original_name).suffix.lower()
    if suffix not in DEFAULT_EXTS:
        allowed = ", ".join(DEFAULT_EXTS)
        raise HTTPException(status_code=400, detail=f"仅支持这些文件类型：{allowed}")

    document_id = uuid4().hex
    stored_name = _object_name(document_id, original_name)
    temp_path = TEMP_DIR / f"{document_id}{suffix}"

    try:
        _save_upload_file(upload_file, temp_path)
        file_size = temp_path.stat().st_size
        upload_file_object(
            file_path=temp_path,
            object_name=stored_name,
            content_type=_content_type(upload_file, original_name),
        )
        node_count = ingest_file(
            file_path=str(temp_path),
            document_id=document_id,
            original_filename=original_name,
        )
    except Exception:
        try:
            delete_file_object(stored_name)
        except Exception:
            pass
        raise
    finally:
        temp_path.unlink(missing_ok=True)

    record = DocumentRecord(
        id=document_id,
        file_name=original_name,
        stored_name=stored_name,
        size=file_size,
        node_count=node_count,
        uploaded_at=datetime.now(timezone.utc).isoformat(),
    )

    records = _read_manifest()
    records.insert(0, record)
    _write_manifest(records)
    build_index.cache_clear()
    return record


def _delete_document(document_id: str) -> DocumentDeleteResponse:
    records = _read_manifest()
    target = next((record for record in records if record.id == document_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    vector_deleted = _delete_document_vectors(document_id)
    delete_file_object(target.stored_name)
    _write_manifest([record for record in records if record.id != document_id])

    return DocumentDeleteResponse(
        deleted=True,
        vector_deleted=vector_deleted,
        document=target,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    return DocumentListResponse(documents=_read_manifest())


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    record = await run_in_threadpool(_create_document, file)
    return DocumentUploadResponse(document=record)


@router.get("/{document_id}/download")
async def download_document(document_id: str):
    record = _find_document(document_id)
    if not file_object_exists(record.stored_name):
        raise HTTPException(status_code=404, detail="文件不存在")

    return StreamingResponse(
        stream_file_object(record.stored_name),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(record.file_name)}",
        },
    )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: str):
    return await run_in_threadpool(_delete_document, document_id)
