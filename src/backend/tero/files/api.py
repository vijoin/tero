from io import BytesIO
from typing import Optional
from urllib.parse import quote

from fastapi.responses import StreamingResponse
from fastapi import HTTPException, status

from .domain import File


def build_file_download_response(f: Optional[File]) -> StreamingResponse:
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    # quote filename to properly handle non-ASCII characters
    return StreamingResponse(BytesIO(f.content), media_type=f.content_type,
                             headers={"Content-Disposition": f'attachment; filename="{quote(f.name)}"'})
