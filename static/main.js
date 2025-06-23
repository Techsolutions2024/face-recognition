// vip-recognition-web/static/main.js

document.addEventListener('DOMContentLoaded', () => {
    // Lấy các element trên trang
    const videoElement = document.getElementById('video');
    const canvasElement = document.getElementById('canvas');
    const statusDiv = document.getElementById('status');
    const resultsDiv = document.getElementById('results');

    const FPS = 5; // Gửi 5 frame/giây tới server để phân tích
    let websocket;

    /**
     * Khởi tạo và truy cập webcam của người dùng
     */
    async function setupCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: { ideal: 640 }, height: { ideal: 480 } } 
            });
            videoElement.srcObject = stream;
            videoElement.addEventListener('loadeddata', () => {
                statusDiv.textContent = 'Camera đã sẵn sàng. Đang kết nối tới server...';
                connectWebSocket();
            });
        } catch (err) {
            console.error("Lỗi truy cập camera: ", err);
            statusDiv.textContent = "Lỗi: Không thể truy cập camera.";
            statusDiv.className = "status disconnected";
        }
    }

    /**
     * Kết nối tới WebSocket server và xử lý các sự kiện
     */
    function connectWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        websocket = new WebSocket(`${wsProtocol}//${window.location.host}/ws/live-detection`);

        websocket.onopen = () => {
            console.log("Đã kết nối WebSocket.");
            statusDiv.textContent = "Đã kết nối. Đang phân tích luồng video...";
            statusDiv.className = "status connected";
            setInterval(sendFrame, 1000 / FPS);
        };

        websocket.onmessage = (event) => {
            const result = JSON.parse(event.data);
            addDetectionCard(result);
        };

        websocket.onclose = () => {
            console.log("Đã ngắt kết nối WebSocket. Thử lại sau 3 giây...");
            statusDiv.textContent = "Đã ngắt kết nối. Đang thử lại...";
            statusDiv.className = "status disconnected";
            setTimeout(connectWebSocket, 3000);
        };

        websocket.onerror = (error) => {
            console.error("Lỗi WebSocket:", error);
        };
    }

    /**
     * Chụp một frame từ video, vẽ lên canvas và gửi qua WebSocket
     */
    function sendFrame() {
        if (!websocket || websocket.readyState !== WebSocket.OPEN) return;

        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;
        const context = canvasElement.getContext('2d');
        context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
        
        const data = canvasElement.toDataURL('image/jpeg', 0.8);
        websocket.send(data);
    }

    /**
     * <<< HÀM ĐƯỢC NÂNG CẤP >>>
     * Tạo và thêm một thẻ kết quả vào giao diện với các loại cảnh báo khác nhau
     * @param {object} result Dữ liệu kết quả từ server
     */
    function addDetectionCard(result) {
        const card = document.createElement('div');
        // Dùng alert_type từ server để quyết định class CSS (màu sắc)
        card.className = 'result-card ' + result.alert_type;
        
        let content = `<p class="name">${result.is_vip ? result.vip_details.name : 'Người lạ'}</p>`;
        
        if (result.is_vip) {
            content += `<p>Phân loại: ${result.vip_details.category}</p>`;
            content += `<p>Độ tin cậy: ${result.confidence.toFixed(2)}%</p>`;

            // Hiển thị ghi chú quan trọng nếu có
            if (result.display_note) {
                content += `<p class="note">${result.display_note}</p>`;
            }
        }
        
        content += `<p>Thời gian: ${result.timestamp}</p>`;
        
        card.innerHTML = content;
        resultsDiv.prepend(card);

        // Giới hạn số lượng thẻ hiển thị để tránh lag trình duyệt
        while (resultsDiv.childElementCount > 50) {
            resultsDiv.removeChild(resultsDiv.lastChild);
        }
    }

    // Bắt đầu toàn bộ quy trình khi trang được tải
    window.addEventListener('load', setupCamera);
});