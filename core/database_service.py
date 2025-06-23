# vip-recognition-web/core/database_service.py

import boto3
from botocore.exceptions import ClientError
from typing import Optional, List, Dict, Any
from collections import Counter
from models.vip import VIP
import os

class DatabaseService:
    def __init__(self):
        try:
            self.region = os.getenv("AWS_REGION")
            # <<< THAY ĐỔI CHÍNH: Đọc một tên gốc duy nhất >>>
            base_table_name = os.getenv("DYNAMODB_TABLE_NAME")

            if not base_table_name or not self.region:
                raise ValueError("DYNAMODB_TABLE_NAME và AWS_REGION phải được thiết lập trong .env")
            
            # <<< THAY ĐỔI CHÍNH: Tự động tạo tên đầy đủ cho các bảng >>>
            self.vips_table_name = f"{base_table_name}-VIPs"
            self.logs_table_name = f"{base_table_name}-Logs"

            self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
            self.vips_table = self.dynamodb.Table(self.vips_table_name)
            self.logs_table = self.dynamodb.Table(self.logs_table_name)
            
            print(f"Đã kết nối tới các bảng DynamoDB: '{self.vips_table_name}', '{self.logs_table_name}'")

        except Exception as e:
            print(f"FATAL: Lỗi khi khởi tạo DatabaseService: {e}")
            raise

    # ... (Toàn bộ các hàm còn lại như get_vip_by_face_id, add_vip, log_detection_event... giữ nguyên không thay đổi) ...

    def get_vip_by_face_id(self, face_id: str) -> Optional[VIP]:
        try:
            response = self.vips_table.get_item(Key={'faceId': face_id})
            return VIP(**response['Item']) if 'Item' in response else None
        except ClientError as e:
            print(f"Lỗi khi lấy VIP: {e.response['Error']['Message']}")
            return None

    def get_all_vips(self) -> List[VIP]:
        try:
            response = self.vips_table.scan()
            items = response.get('Items', [])
            return [VIP(**item) for item in sorted(items, key=lambda x: x.get('name', ''))]
        except ClientError as e:
            print(f"Lỗi khi quét bảng VIPs: {e.response['Error']['Message']}")
            return []

    def add_or_update_vip(self, vip: VIP) -> bool:
        try:
            self.vips_table.put_item(Item=vip.model_dump(exclude_none=True))
            return True
        except ClientError as e:
            print(f"Lỗi khi ghi VIP: {e.response['Error']['Message']}")
            return False

    def delete_vip(self, face_id: str) -> bool:
        try:
            self.vips_table.delete_item(Key={'faceId': face_id})
            return True
        except ClientError as e:
            print(f"Lỗi khi xóa VIP: {e.response['Error']['Message']}")
            return False
            
    def update_last_visit(self, face_id: str, visit_date: str) -> bool:
        try:
            self.vips_table.update_item(
                Key={'faceId': face_id},
                UpdateExpression="set lastVisit = :d",
                ExpressionAttributeValues={':d': visit_date}
            )
            return True
        except ClientError as e:
            print(f"Lỗi khi cập nhật lastVisit: {e.response['Error']['Message']}")
            return False

    def log_detection_event(self, log_data: Dict[str, Any]):
        try:
            self.logs_table.put_item(Item=log_data)
        except ClientError as e:
            print(f"Lỗi khi ghi log nhận diện: {e.response['Error']['Message']}")

    def get_analytics_summary_for_date(self, date_str: str) -> Dict[str, Any]:
        print(f"Đang tổng hợp analytics cho ngày: {date_str}...")
        try:
            # Giả định GSI có tên 'DateIndex' trên bảng logs
            response = self.logs_table.query(
                IndexName='DateIndex',
                KeyConditionExpression='detectionDate = :d',
                ExpressionAttributeValues={':d': date_str}
            )
            logs = response.get('Items', [])
            
            total_visits = len(logs)
            vip_logs = [log for log in logs if log.get('isVip')]
            vip_visit_count = len(vip_logs)
            
            hourly_distribution = Counter(int(log['detectionHour']) for log in logs)
            hourly_data = {str(h): hourly_distribution.get(h, 0) for h in range(24)}
            
            top_vips_counter = Counter(log['vipName'] for log in vip_logs if 'vipName' in log)
            top_vips = [{"name": name, "visits": count} for name, count in top_vips_counter.most_common(5)]

            return {
                "summaryDate": date_str,
                "totalVisits": total_visits,
                "vipVisitCount": vip_visit_count,
                "strangerVisitCount": total_visits - vip_visit_count,
                "hourlyDistribution": hourly_data,
                "topVips": top_vips
            }
        except ClientError as e:
            print(f"Lỗi khi truy vấn analytics: {e.response['Error']['Message']}")
            # Trả về lỗi nếu GSI chưa được tạo
            if e.response['Error']['Code'] == 'ValidationException':
                return {"error": "Bảng Logs chưa có Index 'DateIndex'. Vui lòng tạo GSI để sử dụng tính năng này."}
            return {"error": "Không thể lấy dữ liệu analytics."}