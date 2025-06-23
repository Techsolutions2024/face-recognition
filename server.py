# vip-recognition-web/server.py

import uvicorn
import base64
import uuid
import random # Dùng để giả lập dữ liệu analytics ban đầu
from fastapi import FastAPI, WebSocket, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.websockets import WebSocketDisconnect
from dotenv import load_dotenv
from typing import List, Optional
from datetime import datetime, timedelta

# Tải biến môi trường trước tiên
load_dotenv()

from core.rekognition_service import RekognitionService
from core.database_service import DatabaseService
from models.detection_result import DetectionResult
from models.vip import VIP

# --- Khởi tạo ứng dụng và các services ---
app = FastAPI(title="VIP Vision - API & Realtime Service")

try:
    rekognition_serv = RekognitionService()
    db_serv = DatabaseService()
except ValueError as e:
    print(f"FATAL: Lỗi cấu hình môi trường - {e}")
    exit(1)

# Phục vụ các file tĩnh trong thư mục 'static'
app.mount("/static", StaticFiles(directory="static"), name="static")


# === CÁC ENDPOINT ĐỂ PHỤC VỤ GIAO DIỆN NGƯỜI DÙNG ===

@app.get("/", response_class=FileResponse, summary="Trang nhận diện thời gian thực")
async def get_realtime_view():
    return "static/index.html"

@app.get("/management", response_class=FileResponse, summary="Cổng quản lý VIP")
async def get_management_portal():
    return "static/management.html"

# <<< ENDPOINT MỚI CHO DASHBOARD >>>
@app.get("/dashboard", response_class=FileResponse, summary="Dashboard Analytics")
async def get_dashboard():
    return "static/dashboard.html"


# === API CHO CỔNG QUẢN LÝ VIP (Giữ nguyên) ===

@app.get("/api/vips", response_model=List[VIP], summary="Lấy danh sách tất cả VIP")
async def list_vips():
    return db_serv.get_all_vips()

@app.post("/api/vips", response_model=VIP, status_code=201, summary="Thêm một VIP mới")
async def create_vip(
    name: str = Form(...), category: str = Form(...),
    notes: Optional[str] = Form(None), dob: Optional[str] = Form(None),
    tags: Optional[str] = Form(None), image: UploadFile = File(...)
):
    image_bytes = await image.read()
    face_id = rekognition_serv.index_face(image_bytes, external_image_id=name)
    if not face_id:
        raise HTTPException(status_code=400, detail="Không tìm thấy khuôn mặt trong ảnh hoặc ảnh không đạt chất lượng.")
    
    vip_tags = [tag.strip() for tag in tags.split(',')] if tags else []
    new_vip = VIP(faceId=face_id, name=name, category=category, notes=notes, dateOfBirth=dob, tags=vip_tags, lastVisit='2000-01-01')
    
    if not db_serv.add_or_update_vip(new_vip):
        rekognition_serv.delete_faces_from_collection([face_id])
        raise HTTPException(status_code=500, detail="Không thể lưu thông tin VIP vào database.")
    return new_vip

@app.delete("/api/vips/{face_id}", status_code=204, summary="Xóa một VIP")
async def delete_vip(face_id: str):
    rekognition_serv.delete_faces_from_collection([face_id])
    db_serv.delete_vip(face_id)
    return

# <<< API MỚI CHO DASHBOARD >>>
@app.get("/api/analytics/{date_str}", summary="Lấy dữ liệu analytics cho một ngày")
async def get_analytics_for_date(date_str: str):
    """
    Cung cấp dữ liệu đã tổng hợp cho Dashboard.
    """
    try:
        # Gọi service để thực hiện truy vấn và tổng hợp dữ liệu
        analytics_data = db_serv.get_analytics_summary_for_date(date_str)
        if analytics_data.get("error"):
             raise HTTPException(status_code=500, detail=analytics_data["error"])
        if analytics_data.get("totalVisits") == 0:
            raise HTTPException(status_code=404, detail=f"Không có dữ liệu cho ngày {date_str}.")
        return analytics_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === WEBSOCKET CHO NHẬN DIỆN REAL-TIME (Cập nhật logic ghi log) ===

@app.websocket("/ws/live-detection")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Một client đã kết nối qua WebSocket.")
    try:
        while True:
            base64_data = await websocket.receive_text()
            image_data = base64.b64decode(base64_data.split(',')[1])
            detection_result = await process_detection(image_data)
            await websocket.send_json(detection_result.model_dump())
    except WebSocketDisconnect:
        print("Client đã ngắt kết nối.")
    except Exception as e:
        print(f"Lỗi xảy ra trong WebSocket: {e}")
        await websocket.close(code=1011)

async def process_detection(image_bytes: bytes) -> DetectionResult:
    """Hàm tách riêng logic nhận diện và ghi log."""
    match_result = rekognition_serv.search_face_in_collection(image_bytes)
    detection: DetectionResult

    if match_result:
        vip_info = db_serv.get_vip_by_face_id(match_result["face_id"])
        if vip_info:
            alert_type = "normal-vip" # (Logic phân loại cảnh báo thông minh ở đây)
            # ...
            db_serv.update_last_visit(vip_info.faceId, datetime.now().isoformat())
            detection = DetectionResult(is_vip=True, confidence=match_result["confidence"], vip_details=vip_info, alert_type=alert_type, display_note=vip_info.notes)
        else:
            detection = DetectionResult(is_vip=False, alert_type="stranger")
    else:
        detection = DetectionResult(is_vip=False, alert_type="stranger")

    # <<< LOGIC GHI NHẬN LỊCH SỬ >>>
    now = datetime.now()
    log_item = {
        "logId": str(uuid.uuid4()), "timestamp": now.isoformat(),
        "detectionDate": now.strftime("%Y-%m-%d"), "detectionHour": now.hour,
        "isVip": detection.is_vip
    }
    if detection.is_vip:
        log_item.update({
            "faceId": detection.vip_details.faceId,
            "vipName": detection.vip_details.name,
            "vipCategory": detection.vip_details.category
        })
    db_serv.log_detection_event(log_item)
    
    return detection

if __name__ == "__main__":
    print("Khởi động server tại http://localhost:8000")
    print("-> Trang nhận diện: http://localhost:8000")
    print("-> Trang quản lý: http://localhost:8000/management")
    print("-> Trang dashboard: http://localhost:8000/dashboard")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)