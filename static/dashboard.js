// vip-recognition-web/static/dashboard.js

document.addEventListener('DOMContentLoaded', () => {
    // Lấy ngày hôm nay theo định dạng YYYY-MM-DD
    const todayStr = new Date().toISOString().split('T')[0];
    document.getElementById('dashboardDate').textContent = `(Ngày: ${todayStr})`;

    // Gọi hàm chính để tải dữ liệu và vẽ biểu đồ
    fetchAndRenderDashboard(todayStr);
});

/**
 * Hàm chính để lấy dữ liệu từ API và gọi các hàm vẽ biểu đồ con
 * @param {string} dateStr - Ngày cần lấy dữ liệu, định dạng 'YYYY-MM-DD'
 */
async function fetchAndRenderDashboard(dateStr) {
    try {
        const response = await fetch(`/api/analytics/${dateStr}`);
        if (!response.ok) {
            // Nếu API trả về lỗi 404 hoặc 500
            const errorText = await response.text();
            throw new Error(`Không thể tải dữ liệu: ${errorText}`);
        }
        const data = await response.json();

        // Gọi các hàm con để vẽ từng biểu đồ
        renderHourlyChart(data.hourlyDistribution || {});
        renderRatioChart(data.vipVisitCount || 0, data.totalVisits || 0);
        renderTopVipsTable(data.topVips || []);

    } catch (error) {
        console.error("Lỗi khi tải dữ liệu dashboard:", error);
        // Hiển thị lỗi cho người dùng một cách thân thiện
        document.querySelector('.dashboard-grid').innerHTML = 
            `<p style="color: red; text-align: center;">${error.message}</p>`;
    }
}

/**
 * Vẽ biểu đồ cột "Giờ Vàng"
 * @param {object} hourlyData - Dữ liệu số lượt ghé thăm theo giờ
 */
function renderHourlyChart(hourlyData) {
    const ctx = document.getElementById('hourlyVisitsChart').getContext('2d');
    
    // Chuẩn bị dữ liệu cho 24 giờ, điền 0 vào các giờ không có dữ liệu
    const chartLabels = Array.from({length: 24}, (_, i) => `${i}:00`);
    const chartData = Array.from({length: 24}, (_, i) => hourlyData[i] || 0);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartLabels,
            datasets: [{
                label: 'Số lượt nhận diện',
                data: chartData,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: { y: { beginAtZero: true } }
        }
    });
}

/**
 * Vẽ biểu đồ tròn "Tỷ Lệ VIP / Khách Lạ"
 * @param {number} vipCount - Số lượt ghé thăm của VIP
 * @param {number} totalCount - Tổng số lượt ghé thăm
 */
function renderRatioChart(vipCount, totalCount) {
    const ctx = document.getElementById('ratioChart').getContext('2d');
    const strangerCount = totalCount - vipCount;
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['VIP', 'Khách lạ'],
            datasets: [{
                data: [vipCount, strangerCount],
                backgroundColor: ['#28a745', '#ffc107'],
                hoverOffset: 4
            }]
        },
        options: { responsive: true }
    });
}

/**
 * Hiển thị bảng Top 5 VIP
 * @param {Array} topVips - Mảng các object VIP
 */
function renderTopVipsTable(topVips) {
    const tableBody = document.getElementById('topVipsTable').getElementsByTagName('tbody')[0];
    tableBody.innerHTML = ''; // Xóa dữ liệu cũ

    if (topVips.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="2" style="text-align: center;">Chưa có dữ liệu VIP.</td></tr>';
        return;
    }

    topVips.forEach(vip => {
        let row = tableBody.insertRow();
        row.insertCell(0).textContent = vip.name;
        row.insertCell(1).textContent = vip.visits;
    });
}