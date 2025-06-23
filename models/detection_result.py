# vip-recognition-web/models/detection_result.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .vip import VIP

class DetectionResult(BaseModel):
    """
    Định nghĩa cấu trúc dữ liệu được gửi từ server tới client qua WebSocket
    sau mỗi lần nhận diện.
    """
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    is_vip: bool
    confidence: Optional[float] = None
    
    # Chứa toàn bộ object VIP nếu nhận diện thành công
    vip_details: Optional[VIP] = None
    
    # Các trường dành riêng cho việc hiển thị cảnh báo thông minh
    alert_type: str = "stranger"  # Giá trị: stranger, normal-vip, returning-vip, birthday-vip
    display_note: Optional[str] = None