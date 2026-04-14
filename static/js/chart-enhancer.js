/* ================================================
   大类资产配置指标监控面板 - 图表交互增强 V6.0
   ================================================ */

class ChartEnhancer {
    constructor(chartContainerId) {
        this.container = document.getElementById(chartContainerId);
        this.chart = null;
        this.currentHoverPoint = null;
        this.currentSelectedPoint = null;
        this.dataflowActive = false;

        // 绑定事件
        this.bindEvents();

        console.log('[ChartEnhancer] 初始化完成，容器:', chartContainerId);
    }

    /**
     * 绑定图表事件
     */
    bindEvents() {
        if (!this.container) return;

        // 监听Plotly图表更新事件
        this.container.addEventListener('plotly_afterplot', (event) => {
            this.chart = event.target;
            this.initDataflowEffects();
            this.initPointHighlighting();
        });

        // 监听悬停事件
        this.container.addEventListener('plotly_hover', (event) => {
            this.handleHover(event);
        });

        // 监听点击事件
        this.container.addEventListener('plotly_click', (event) => {
            this.handleClick(event);
        });

        // 监听鼠标离开
        this.container.addEventListener('mouseleave', () => {
            this.handleMouseLeave();
        });

        // 监听图表重绘
        this.container.addEventListener('plotly_relayout', (event) => {
            this.handleRelayout(event);
        });
    }

    /**
     * 初始化数据流动画效果
     */
    initDataflowEffects() {
        if (!this.chart || !this.container) return;

        // 检查数据流网格
        const dataflowGrid = this.container.querySelector('.dataflow-grid');
        if (dataflowGrid) {
            // 添加数据流脉冲效果
            this.startDataflowPulses();
        }

        // 添加图表扫描线
        this.addScanlines();
    }

    /**
     * 启动数据流脉冲效果
     */
    startDataflowPulses() {
        // 创建脉冲标记
        const pulseMarkers = document.createElement('div');
        pulseMarkers.className = 'pulse-markers';
        pulseMarkers.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 10;
        `;
        this.container.appendChild(pulseMarkers);

        // 定期添加脉冲
        this.pulseInterval = setInterval(() => {
            this.createPulseMarker(pulseMarkers);
        }, 3000);

        this.dataflowActive = true;
    }

    /**
     * 创建脉冲标记
     */
    createPulseMarker(pulseMarkers) {
        const marker = document.createElement('div');
        marker.className = 'pulse-marker animate-pulse';

        // 随机位置
        const xPercent = Math.random() * 80 + 10; // 10% - 90%
        const yPercent = Math.random() * 80 + 10;

        // 随机颜色（数据流主题）
        const colors = ['#00d4ff', '#7b61ff', '#00ff9d'];
        const color = colors[Math.floor(Math.random() * colors.length)];

        marker.style.cssText = `
            position: absolute;
            left: ${xPercent}%;
            top: ${yPercent}%;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: ${color};
            transform: translate(-50%, -50%);
            box-shadow: 0 0 15px ${color};
            pointer-events: none;
            z-index: 11;
        `;

        pulseMarkers.appendChild(marker);

        // 2秒后移除
        setTimeout(() => {
            if (marker.parentNode) {
                marker.remove();
            }
        }, 2000);
    }

    /**
     * 添加扫描线
     */
    addScanlines() {
        const scanlines = document.createElement('div');
        scanlines.className = 'chart-scanlines';
        scanlines.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 2;
            background: linear-gradient(
                to bottom,
                transparent 0%,
                transparent 98%,
                rgba(0, 212, 255, 0.1) 100%
            );
            background-size: 100% 4px;
            animation: scanline 15s linear infinite;
        `;
        this.container.appendChild(scanlines);
    }

    /**
     * 初始化数据点高亮
     */
    initPointHighlighting() {
        if (!this.chart || !this.chart.data) return;

        // 为每个数据点添加高亮层
        const plotlyRoot = this.container.querySelector('.main-svg');
        if (!plotlyRoot) return;

        // 创建高亮点容器
        const highlightLayer = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        highlightLayer.setAttribute('class', 'point-highlight-layer');
        highlightLayer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 20;
        `;

        plotlyRoot.appendChild(highlightLayer);
    }

    /**
     * 处理悬停事件
     */
    handleHover(event) {
        if (!event || !event.points || !event.points.length) return;

        const point = event.points[0];
        this.currentHoverPoint = point;

        // 显示悬停详情
        this.showHoverDetails(point);

        // 高亮数据点
        this.highlightPoint(point);
    }

    /**
     * 显示悬停详情
     */
    showHoverDetails(point) {
        const detailsPanel = document.getElementById('chartDetails');
        if (!detailsPanel) return;

        // 更新数据详情tab
        const dataDetails = detailsPanel.querySelector('[data-tab="data"]');
        if (dataDetails) {
            const date = new Date(point.x).toLocaleDateString('zh-CN');
            const value = point.y.toFixed(4);
            const traceName = point.data.name || '数据';

            dataDetails.innerHTML = `
                <div class="hover-details">
                    <div class="detail-row">
                        <span class="detail-label">指标：</span>
                        <span class="detail-value">${traceName}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">日期：</span>
                        <span class="detail-value">${date}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">数值：</span>
                        <span class="detail-value" style="color: ${point.fullData.line.color || '#00d4ff'}">${value}</span>
                    </div>
                    ${point.pointNumber !== undefined ? `
                    <div class="detail-row">
                        <span class="detail-label">位置：</span>
                        <span class="detail-value">第 ${point.pointNumber + 1} 个数据点</span>
                    </div>` : ''}
                </div>
            `;
        }

        // 显示详情面板（如果隐藏）
        detailsPanel.style.display = 'block';
    }

    /**
     * 高亮数据点
     */
    highlightPoint(point) {
        // 清除之前的高亮
        this.clearPointHighlight();

        // 创建高亮点
        const highlightLayer = this.container.querySelector('.point-highlight-layer');
        if (!highlightLayer || !point.x || !point.y) return;

        // 获取图表坐标系统
        const xAxis = this.chart.layout.xaxis;
        const yAxis = this.chart.layout.yaxis;

        // 这里简化处理，实际需要计算坐标转换
        // 在实际项目中，需要根据Plotly的坐标系统进行转换
        // 由于时间限制，这里使用简化版本

        // 添加脉冲动画标记
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        marker.setAttribute('class', 'point-highlight');
        marker.setAttribute('cx', '50%'); // 简化位置
        marker.setAttribute('cy', '50%');
        marker.setAttribute('r', '15');
        marker.setAttribute('fill', 'none');
        marker.setAttribute('stroke', point.fullData.line.color || '#00d4ff');
        marker.setAttribute('stroke-width', '2');
        marker.setAttribute('stroke-dasharray', '5,5');
        marker.style.cssText = `
            animation: pulse 1.5s ease-in-out infinite;
        `;

        highlightLayer.appendChild(marker);

        this.currentSelectedPoint = marker;
    }

    /**
     * 清除点高亮
     */
    clearPointHighlight() {
        if (this.currentSelectedPoint && this.currentSelectedPoint.parentNode) {
            this.currentSelectedPoint.remove();
        }
        this.currentSelectedPoint = null;
    }

    /**
     * 处理点击事件
     */
    handleClick(event) {
        if (!event || !event.points || !event.points.length) return;

        const point = event.points[0];

        // 创建数据点详情弹窗
        this.createPointPopup(point);

        // 记录选择点
        this.currentSelectedPoint = point;
    }

    /**
     * 创建数据点详情弹窗
     */
    createPointPopup(point) {
        // 移除现有弹窗
        this.removePointPopup();

        const popup = document.createElement('div');
        popup.className = 'point-popup animate-fade-in';
        popup.style.cssText = `
            position: absolute;
            background: rgba(10, 12, 16, 0.95);
            border: 1px solid #3a4052;
            border-radius: 8px;
            padding: 16px;
            min-width: 200px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(10px);
            z-index: 1000;
            pointer-events: auto;
        `;

        const date = new Date(point.x).toLocaleDateString('zh-CN');
        const value = point.y.toFixed(4);
        const traceName = point.data.name || '数据';

        popup.innerHTML = `
            <div class="popup-header">
                <h3 style="margin: 0 0 8px 0; color: #e3e7f1; font-size: 14px;">${traceName}</h3>
                <button class="close-popup" style="
                    position: absolute;
                    top: 8px;
                    right: 8px;
                    background: none;
                    border: none;
                    color: #8b93a7;
                    cursor: pointer;
                    font-size: 18px;
                ">×</button>
            </div>
            <div class="popup-content">
                <div style="margin-bottom: 8px;">
                    <div style="color: #8b93a7; font-size: 12px;">日期</div>
                    <div style="color: #e3e7f1; font-size: 14px; font-family: 'JetBrains Mono', monospace;">${date}</div>
                </div>
                <div style="margin-bottom: 8px;">
                    <div style="color: #8b93a7; font-size: 12px;">数值</div>
                    <div style="color: ${point.fullData.line.color || '#00d4ff'}; font-size: 16px; font-family: 'JetBrains Mono', monospace; font-weight: bold;">${value}</div>
                </div>
                ${point.pointNumber !== undefined ? `
                <div style="margin-bottom: 8px;">
                    <div style="color: #8b93a7; font-size: 12px;">序列位置</div>
                    <div style="color: #e3e7f1; font-size: 14px; font-family: 'JetBrains Mono', monospace;">第 ${point.pointNumber + 1} 个数据点</div>
                </div>` : ''}
            </div>
            <div class="popup-actions" style="margin-top: 12px; display: flex; gap: 8px;">
                <button class="popup-action-btn" data-action="compare" style="
                    flex: 1;
                    background: rgba(0, 212, 255, 0.1);
                    border: 1px solid #00d4ff;
                    color: #00d4ff;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    cursor: pointer;
                ">对比</button>
                <button class="popup-action-btn" data-action="bookmark" style="
                    flex: 1;
                    background: rgba(123, 97, 255, 0.1);
                    border: 1px solid #7b61ff;
                    color: #7b61ff;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    cursor: pointer;
                ">标记</button>
            </div>
        `;

        // 添加到图表容器
        this.container.appendChild(popup);

        // 定位弹窗
        const rect = this.container.getBoundingClientRect();
        popup.style.left = `${rect.width / 2 - 100}px`;
        popup.style.top = '20px';

        // 绑定事件
        popup.querySelector('.close-popup').addEventListener('click', () => {
            this.removePointPopup();
        });

        popup.querySelectorAll('.popup-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                this.handlePopupAction(action, point);
            });
        });

        this.currentPopup = popup;
    }

    /**
     * 移除数据点弹窗
     */
    removePointPopup() {
        if (this.currentPopup && this.currentPopup.parentNode) {
            this.currentPopup.remove();
            this.currentPopup = null;
        }
    }

    /**
     * 处理弹窗操作
     */
    handlePopupAction(action, point) {
        switch(action) {
            case 'compare':
                console.log('对比数据点:', point);
                alert(`对比功能开发中\n数据点: ${point.y.toFixed(4)}`);
                break;
            case 'bookmark':
                console.log('标记数据点:', point);
                this.bookmarkPoint(point);
                break;
        }
    }

    /**
     * 标记数据点
     */
    bookmarkPoint(point) {
        // 保存标记到本地存储
        const bookmarks = JSON.parse(localStorage.getItem('chartBookmarks') || '[]');

        const bookmark = {
            id: Date.now(),
            date: point.x,
            value: point.y,
            trace: point.data.name || '未知',
            color: point.fullData.line.color || '#00d4ff',
            timestamp: new Date().toISOString(),
        };

        bookmarks.push(bookmark);
        localStorage.setItem('chartBookmarks', JSON.stringify(bookmarks));

        // 显示确认消息
        const toast = document.createElement('div');
        toast.textContent = '数据点已标记';
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 212, 255, 0.9);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 10000;
            animation: fade-in 0.3s ease-out, fade-out 0.3s ease-out 2s forwards;
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            if (toast.parentNode) toast.remove();
        }, 2300);
    }

    /**
     * 处理鼠标离开
     */
    handleMouseLeave() {
        this.currentHoverPoint = null;

        // 清除悬停详情
        const detailsPanel = document.getElementById('chartDetails');
        if (detailsPanel) {
            const dataDetails = detailsPanel.querySelector('[data-tab="data"]');
            if (dataDetails) {
                dataDetails.innerHTML = '<p>请将鼠标悬停在图表上查看数据详情</p>';
            }
        }

        // 清除高亮
        this.clearPointHighlight();
    }

    /**
     * 处理图表重绘
     */
    handleRelayout(event) {
        // 图表重绘时重新初始化效果
        setTimeout(() => {
            this.initDataflowEffects();
            this.initPointHighlighting();
        }, 100);
    }

    /**
     * 清理资源
     */
    destroy() {
        if (this.pulseInterval) {
            clearInterval(this.pulseInterval);
            this.pulseInterval = null;
        }

        this.removePointPopup();
        this.clearPointHighlight();

        if (this.currentPopup) {
            this.removePointPopup();
        }

        this.dataflowActive = false;
        console.log('[ChartEnhancer] 已销毁');
    }
}

// 全局导出
if (typeof window !== 'undefined') {
    window.ChartEnhancer = ChartEnhancer;
}

console.log('[ChartEnhancer] 模块加载完成');