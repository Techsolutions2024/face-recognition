# vip-recognition-web/models/vip.py

from pydantic import BaseModel
from typing import Optional, List

class VIP(BaseModel):
    """
    Định nghĩa cấu trúc dữ liệu cho một VIP trong hệ thống.
    Đã được cập nhật để bao gồm các thông tin quản lý mở rộng.
    """
    faceId: str
    name: str
    category: str
    
    # Các trường cho tính năng thông báo thông minh
    notes: Optional[str] = None
    dateOfBirth: Optional[str] = None # Định dạng "MM-DD"
    lastVisit: Optional[str] = None   # Định dạng ISO 8601
    
    # --- TRƯỜNG MỚI CHO TÍNH NĂNG TAGGING ---
    tags: Optional[List[str]] = None  # Ví dụ: ["sanh-ruou", "di-cung-gia-dinh"]