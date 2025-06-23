// vip-recognition-web/static/management.js

document.addEventListener('DOMContentLoaded', () => {
    // Lấy các element trên trang
    const addVipForm = document.getElementById('addVipForm');
    const vipListBody = document.getElementById('vipList');
    const statusMessageDiv = document.getElementById('statusMessage');

    /**
     * Hàm hiển thị thông báo trạng thái
     * @param {string} message - Nội dung thông báo
     * @param {boolean} isError - true nếu là lỗi, false nếu là thành công
     */
    function showStatus(message, isError = false) {
        statusMessageDiv.textContent = message;
        statusMessageDiv.className = 'statusMessage ' + (isError ? 'error' : 'success');
        statusMessageDiv.style.display = 'block';
        setTimeout(() => {
            statusMessageDiv.style.display = 'none';
        }, 5000); // Ẩn thông báo sau 5 giây
    }

    /**
     * Tải danh sách VIP từ server và hiển thị lên bảng
     */
    async function loadVips() {
        try {
            const response = await fetch('/api/vips');
            if (!response.ok) {
                throw new Error('Không thể tải danh sách VIP.');
            }
            const vips = await response.json();
            
            vipListBody.innerHTML = ''; // Xóa danh sách cũ
            vips.forEach(vip => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${vip.name}</td>
                    <td>${vip.category}</td>
                    <td>${vip.notes || 'N/A'}</td>
                    <td>
                        <button class="delete-btn" data-face-id="${vip.faceId}" data-vip-name="${vip.name}">Xóa</button>
                    </td>
                `;
                vipListBody.appendChild(row);
            });
        } catch (error) {
            console.error('Lỗi khi tải danh sách VIP:', error);
            showStatus(error.message, true);
        }
    }

    /**
     * Xử lý sự kiện submit form để thêm VIP mới
     */
    addVipForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData();
        formData.append('name', document.getElementById('vipName').value);
        formData.append('category', document.getElementById('vipCategory').value);
        formData.append('notes', document.getElementById('vipNotes').value);
        formData.append('dob', document.getElementById('vipDob').value);
        formData.append('image', document.getElementById('vipImage').files[0]);

        showStatus('Đang xử lý, vui lòng chờ...');

        try {
            const response = await fetch('/api/vips', {
                method: 'POST',
                body: formData, // Trình duyệt sẽ tự đặt Content-Type là multipart/form-data
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Có lỗi xảy ra khi thêm VIP.');
            }

            const newVip = await response.json();
            showStatus(`Đã thêm thành công VIP: ${newVip.name}`);
            addVipForm.reset(); // Xóa trắng form
            loadVips(); // Tải lại danh sách để hiển thị người mới

        } catch (error) {
            console.error('Lỗi khi thêm VIP:', error);
            showStatus(error.message, true);
        }
    });

    /**
     * Xử lý sự kiện click vào nút Xóa (sử dụng event delegation)
     */
    vipListBody.addEventListener('click', async (e) => {
        if (e.target && e.target.classList.contains('delete-btn')) {
            const faceId = e.target.dataset.faceId;
            const vipName = e.target.dataset.vipName;

            if (confirm(`Bạn có chắc chắn muốn xóa VIP "${vipName}" không? Hành động này không thể hoàn tác.`)) {
                try {
                    const response = await fetch(`/api/vips/${faceId}`, {
                        method: 'DELETE',
                    });

                    if (!response.ok) {
                        throw new Error('Không thể xóa VIP.');
                    }
                    
                    showStatus(`Đã xóa thành công VIP: ${vipName}`);
                    loadVips(); // Tải lại danh sách

                } catch (error) {
                    console.error('Lỗi khi xóa VIP:', error);
                    showStatus(error.message, true);
                }
            }
        }
    });

    // Tải danh sách VIP ngay khi trang được mở
    loadVips();
});