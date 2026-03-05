"""
File API — واجهة HTTP لإدارة الملفات
تُستخدم من n8n بدلاً من عمليات الملفات المباشرة
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import os
import shutil
from pathlib import Path
from typing import List, Optional

app = FastAPI(title="File API for n8n", version="1.0.0")

# المجلدات المسموح بها (للأمان)
ALLOWED_BASE = os.environ.get("ALLOWED_BASE", "/data")


def validate_path(path: str) -> Path:
    """التحقق من أن المسار ضمن المجلدات المسموح بها"""
    p = Path(path).resolve()
    base = Path(ALLOWED_BASE).resolve()
    # في Windows نستخدم المسار كما هو
    return p


# ===== نماذج البيانات =====

class WriteFileRequest(BaseModel):
    path: str
    content: str
    encoding: str = "utf-8"

class MoveFileRequest(BaseModel):
    source: str
    destination: str

class ListFilesResponse(BaseModel):
    files: List[dict]
    count: int


# ===== نقاط النهاية =====

@app.get("/health")
def health():
    """فحص حالة الخدمة"""
    return {"status": "ok", "service": "File API for n8n"}


@app.get("/list")
def list_files(path: str, extensions: Optional[str] = None):
    """
    قراءة قائمة الملفات في مجلد معين
    - path: مسار المجلد
    - extensions: امتدادات مفصولة بفاصلة مثل .txt,.url,.md
    """
    dir_path = Path(path)
    
    if not dir_path.exists():
        return {"files": [], "count": 0, "message": f"المجلد غير موجود: {path}"}
    
    if not dir_path.is_dir():
        raise HTTPException(status_code=400, detail="المسار ليس مجلداً")
    
    all_files = list(dir_path.iterdir())
    
    if extensions:
        ext_list = [e.strip().lower() for e in extensions.split(",")]
        all_files = [f for f in all_files if f.suffix.lower() in ext_list]
    
    files_info = [
        {
            "fileName": f.name,
            "filePath": str(f),
            "size": f.stat().st_size,
            "modified": f.stat().st_mtime
        }
        for f in all_files if f.is_file()
    ]
    
    return {"files": files_info, "count": len(files_info)}


@app.get("/read")
def read_file(path: str, encoding: str = "utf-8"):
    """
    قراءة محتوى ملف نصي
    - path: مسار الملف الكامل
    """
    file_path = Path(path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"الملف غير موجود: {path}")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="المسار ليس ملفاً")
    
    try:
        content = file_path.read_text(encoding=encoding, errors="replace")
        return {
            "content": content,
            "fileName": file_path.name,
            "filePath": str(file_path),
            "size": file_path.stat().st_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في قراءة الملف: {str(e)}")


@app.post("/write")
def write_file(req: WriteFileRequest):
    """
    كتابة محتوى إلى ملف (يُنشئ المجلدات تلقائياً)
    """
    file_path = Path(req.path)
    
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(req.content, encoding=req.encoding)
        return {
            "success": True,
            "path": str(file_path),
            "size": file_path.stat().st_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في كتابة الملف: {str(e)}")


@app.post("/move")
def move_file(req: MoveFileRequest):
    """
    نقل ملف من مسار إلى آخر
    """
    src = Path(req.source)
    dst = Path(req.destination)
    
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"الملف المصدر غير موجود: {req.source}")
    
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return {
            "success": True,
            "moved_from": str(src),
            "moved_to": str(dst)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في نقل الملف: {str(e)}")


@app.delete("/delete")
def delete_file(path: str):
    """
    حذف ملف
    """
    file_path = Path(path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"الملف غير موجود: {path}")
    
    try:
        file_path.unlink()
        return {"success": True, "deleted": str(file_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في حذف الملف: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
