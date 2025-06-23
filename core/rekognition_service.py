# vip-recognition-web/core/rekognition_service.py

import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, List
import os

class RekognitionService:
    """
    Service để đóng gói các tương tác với Amazon Rekognition.
    """
    def __init__(self):
        try:
            self.region = os.getenv("AWS_REGION")
            self.collection_id = os.getenv("REKOGNITION_COLLECTION_ID")
            if not self.collection_id or not self.region:
                raise ValueError("REKOGNITION_COLLECTION_ID và AWS_REGION phải được thiết lập trong file .env")

            self.client = boto3.client('rekognition', region_name=self.region)
            print(f"Rekognition Service đã sẵn sàng cho collection '{self.collection_id}'")
        except Exception as e:
            print(f"FATAL: Lỗi khi khởi tạo RekognitionService: {e}")
            raise

    def index_face(self, image_bytes: bytes, external_image_id: str) -> Optional[str]:
        """
        Thêm một khuôn mặt từ ảnh vào collection và trả về FaceId.
        Hữu ích cho việc thêm VIP mới.
        """
        try:
            response = self.client.index_faces(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                ExternalImageId=external_image_id,
                MaxFaces=1,
                QualityFilter="AUTO",
                DetectionAttributes=['DEFAULT']
            )
            if response['FaceRecords']:
                return response['FaceRecords'][0]['Face']['FaceId']
            return None
        except ClientError as e:
            print(f"Lỗi AWS khi index face: {e.response['Error']['Message']}")
            return None

    def search_face_in_collection(self, image_bytes: bytes, similarity_threshold: int = 98) -> Optional[Dict]:
        """
        Tìm kiếm khuôn mặt trong một ảnh với collection đã định sẵn.
        Trả về một dictionary chứa face_id và confidence nếu tìm thấy.
        """
        try:
            response = self.client.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                FaceMatchThreshold=similarity_threshold,
                MaxFaces=1
            )
            
            if response['FaceMatches']:
                match = response['FaceMatches'][0]
                return {
                    "face_id": match['Face']['FaceId'],
                    "confidence": match['Similarity']
                }
            return None
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidParameterException':
                pass # Bỏ qua nếu không có khuôn mặt trong ảnh
            else:
                print(f"Lỗi AWS Rekognition: {e.response['Error']['Message']}")
            return None
        except Exception as e:
            print(f"Lỗi không xác định trong Rekognition: {e}")
            return None
            
    # <<< PHƯƠNG THỨC MỚI >>>
    def delete_faces_from_collection(self, face_ids: List[str]) -> List[str]:
        """
        Xóa một hoặc nhiều khuôn mặt khỏi collection bằng danh sách Face ID.
        Trả về danh sách các Face ID đã được xóa thành công.
        """
        if not face_ids:
            return []
        try:
            response = self.client.delete_faces(
                CollectionId=self.collection_id,
                FaceIds=face_ids
            )
            deleted_ids = response.get('DeletedFaces', [])
            print(f"Đã xóa thành công các faceId: {deleted_ids}")
            return [d['FaceId'] for d in deleted_ids]
        except ClientError as e:
            print(f"Lỗi khi xóa face khỏi collection: {e.response['Error']['Message']}")
            return []