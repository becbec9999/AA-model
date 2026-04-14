/* ================================================
   大类资产配置指标监控面板 - 数据流可视化 V6.0
   ================================================ */

class DataFlowVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.effects = {
            grid: null,
            scanlines: null,
            pulses: null,
            nodes: null,
            connections: null
        };
        this.active = false;
        this.animationFrame = null;

        console.log('[DataFlowVisualizer] 初始化完成，容器:', containerId);
    }

    /**
     * 启动数据流可视化
     */
    start() {
        if (this.active || !this.container) return;

        console.log('[DataFlowVisualizer] 启动数据流可视化');

        // 创建数据流网格
        this.createDataFlowGrid();

        // 创建扫描线
        this.createScanlines();

        // 创建数据节点
        this.createDataNodes();

        // 创建数据连接线
        this.createConnections();

        // 启动动画循环
        this.startAnimationLoop();

        this.active = true;

        // 添加工业实用主义状态指示器
        this.createStatusIndicator();
    }

    /**
     * 创建数据流网格（工业网格背景）
     */
    createDataFlowGrid() {
        const grid = document.createElement('div');
        grid.className = 'dataflow-grid-enhanced';
        grid.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 1;
            background-image:
                linear-gradient(90deg, rgba(0, 212, 255, 0.08) 1px, transparent 1px),
                linear-gradient(rgba(0, 212, 255, 0.08) 1px, transparent 1px),
                linear-gradient(45deg, rgba(123, 97, 255, 0.03) 1px, transparent 1px),
                linear-gradient(-45deg, rgba(123, 97, 255, 0.03) 1px, transparent 1px);
            background-size:
                40px 40px,
                40px 40px,
                80px 80px,
                80px 80px;
            animation: grid-scan 60s linear infinite;
            opacity: 0.6;
        `;

        this.container.appendChild(grid);
        this.effects.grid = grid;
    }

    /**
     * 创建扫描线（工业监控效果）
     */
    createScanlines() {
        const scanlines = document.createElement('div');
        scanlines.className = 'scanlines-enhanced';
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
                rgba(0, 212, 255, 0.12) 100%
            );
            background-size: 100% 8px;
            animation: scanline 12s linear infinite;
        `;

        this.container.appendChild(scanlines);
        this.effects.scanlines = scanlines;
    }

    /**
     * 创建数据节点（动态数据点）
     */
    createDataNodes() {
        const nodesContainer = document.createElement('div');
        nodesContainer.className = 'data-nodes-container';
        nodesContainer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 3;
        `;

        this.container.appendChild(nodesContainer);
        this.effects.nodes = nodesContainer;

        // 创建初始数据节点
        for (let i = 0; i < 15; i++) {
            this.createDataNode(nodesContainer);
        }

        // 定期添加新节点
        this.nodeInterval = setInterval(() => {
            if (this.effects.nodes) {
                this.createDataNode(this.effects.nodes);
                // 保持节点数量不超过20个
                const nodes = this.effects.nodes.querySelectorAll('.data-node');
                if (nodes.length > 20) {
                    nodes[0].remove();
                }
            }
        }, 2000);
    }

    /**
     * 创建单个数据节点
     */
    createDataNode(container) {
        const node = document.createElement('div');
        node.className = 'data-node animate-pulse';

        // 随机位置
        const x = Math.random() * 95 + 2.5; // 2.5% - 97.5%
        const y = Math.random() * 95 + 2.5;

        // 随机大小和颜色
        const size = Math.random() * 6 + 3; // 3px - 9px
        const colors = [
            'rgba(0, 212, 255, 0.8)',    // 青色
            'rgba(123, 97, 255, 0.8)',   // 紫色
            'rgba(0, 255, 157, 0.8)'     // 绿色
        ];
        const color = colors[Math.floor(Math.random() * colors.length)];

        // 随机移动方向
        const dx = (Math.random() - 0.5) * 0.3;
        const dy = (Math.random() - 0.5) * 0.3;

        node.style.cssText = `
            position: absolute;
            left: ${x}%;
            top: ${y}%;
            width: ${size}px;
            height: ${size}px;
            border-radius: 50%;
            background: ${color};
            transform: translate(-50%, -50%);
            box-shadow: 0 0 ${size * 2}px ${color};
            pointer-events: none;
            z-index: 4;
            transition: transform 0.5s ease-out;
        `;

        container.appendChild(node);

        // 动画移动
        const animate = () => {
            if (!node.parentNode) return;

            const rect = node.getBoundingClientRect();
            const containerRect = container.getBoundingClientRect();

            let newX = parseFloat(node.style.left) + dx;
            let newY = parseFloat(node.style.top) + dy;

            // 边界检查
            if (newX < 2.5 || newX > 97.5) dx = -dx;
            if (newY < 2.5 || newY > 97.5) dy = -dy;

            node.style.left = `${newX}%`;
            node.style.top = `${newY}%`;

            this.animationFrame = requestAnimationFrame(animate);
        };

        // 延迟启动动画
        setTimeout(() => {
            this.animationFrame = requestAnimationFrame(animate);
        }, Math.random() * 1000);
    }

    /**
     * 创建数据连接线（节点间的流动）
     */
    createConnections() {
        const connectionsContainer = document.createElement('div');
        connectionsContainer.className = 'connections-container';
        connectionsContainer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 3.5;
        `;

        this.container.appendChild(connectionsContainer);
        this.effects.connections = connectionsContainer;

        // 定期更新连接线
        this.connectionInterval = setInterval(() => {
            this.updateConnections();
        }, 1000);
    }

    /**
     * 更新连接线
     */
    updateConnections() {
        if (!this.effects.connections || !this.effects.nodes) return;

        // 清除旧连接线
        this.effects.connections.innerHTML = '';

        const nodes = this.effects.nodes.querySelectorAll('.data-node');
        if (nodes.length < 2) return;

        // 在相近节点间创建连接线
        const nodePositions = Array.from(nodes).map(node => ({
            element: node,
            x: parseFloat(node.style.left),
            y: parseFloat(node.style.top),
            color: node.style.backgroundColor
        }));

        for (let i = 0; i < nodePositions.length; i++) {
            for (let j = i + 1; j < nodePositions.length; j++) {
                const a = nodePositions[i];
                const b = nodePositions[j];

                // 计算距离
                const distance = Math.sqrt(
                    Math.pow(a.x - b.x, 2) + Math.pow(a.y - b.y, 2)
                );

                // 如果距离足够近，创建连接线
                if (distance < 30) {
                    this.createConnection(a, b, distance);
                }
            }
        }
    }

    /**
     * 创建单个连接线
     */
    createConnection(a, b, distance) {
        const line = document.createElement('div');
        line.className = 'data-connection';

        // 计算连接线参数
        const angle = Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI;
        const length = distance;
        const centerX = (a.x + b.x) / 2;
        const centerY = (a.y + b.y) / 2;

        // 混合颜色
        const color = a.color; // 使用第一个节点的颜色

        line.style.cssText = `
            position: absolute;
            left: ${centerX}%;
            top: ${centerY}%;
            width: ${length}%;
            height: 1px;
            background: linear-gradient(90deg, transparent, ${color}, transparent);
            transform: translate(-50%, -50%) rotate(${angle}deg);
            transform-origin: center;
            pointer-events: none;
            z-index: 3;
            opacity: ${0.3 - (distance / 100)};
            filter: blur(0.5px);
        `;

        this.effects.connections.appendChild(line);
    }

    /**
     * 创建工业状态指示器
     */
    createStatusIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'dataflow-status-indicator';
        indicator.style.cssText = `
            position: absolute;
            top: 12px;
            right: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 8px;
            background: rgba(10, 12, 16, 0.7);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: rgba(0, 212, 255, 0.8);
            z-index: 10;
            pointer-events: none;
        `;

        const dot = document.createElement('div');
        dot.className = 'status-dot animate-pulse';
        dot.style.cssText = `
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #00d4ff;
            box-shadow: 0 0 8px #00d4ff;
        `;

        const text = document.createElement('span');
        text.textContent = '数据流活跃';

        indicator.appendChild(dot);
        indicator.appendChild(text);
        this.container.appendChild(indicator);
        this.effects.statusIndicator = indicator;
    }

    /**
     * 启动动画循环
     */
    startAnimationLoop() {
        const animate = () => {
            if (!this.active) return;

            // 更新所有动态效果
            this.updateDynamicEffects();

            this.animationFrame = requestAnimationFrame(animate);
        };

        this.animationFrame = requestAnimationFrame(animate);
    }

    /**
     * 更新动态效果
     */
    updateDynamicEffects() {
        // 可以在这里添加更复杂的动态效果更新逻辑
        if (this.effects.grid) {
            // 网格动画已经通过CSS实现
        }
    }

    /**
     * 停止数据流可视化
     */
    stop() {
        if (!this.active) return;

        console.log('[DataFlowVisualizer] 停止数据流可视化');

        // 停止动画循环
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }

        // 清除定时器
        if (this.nodeInterval) {
            clearInterval(this.nodeInterval);
            this.nodeInterval = null;
        }

        if (this.connectionInterval) {
            clearInterval(this.connectionInterval);
            this.connectionInterval = null;
        }

        // 移除所有效果元素
        Object.values(this.effects).forEach(effect => {
            if (effect && effect.parentNode) {
                effect.remove();
            }
        });

        // 重置效果对象
        this.effects = {
            grid: null,
            scanlines: null,
            pulses: null,
            nodes: null,
            connections: null
        };

        this.active = false;
    }

    /**
     * 调整效果强度
     */
    setIntensity(intensity) {
        // intensity: 0-1
        const opacity = Math.max(0.1, Math.min(1, intensity));

        if (this.effects.grid) {
            this.effects.grid.style.opacity = opacity * 0.6;
        }

        if (this.effects.scanlines) {
            this.effects.scanlines.style.opacity = opacity * 0.8;
        }

        console.log(`[DataFlowVisualizer] 效果强度设置为: ${intensity}`);
    }

    /**
     * 切换效果可见性
     */
    toggleVisibility(visible) {
        const display = visible ? 'block' : 'none';

        Object.values(this.effects).forEach(effect => {
            if (effect && effect.style) {
                effect.style.display = display;
            }
        });

        console.log(`[DataFlowVisualizer] 效果可见性: ${visible ? '显示' : '隐藏'}`);
    }
}

// 全局导出
if (typeof window !== 'undefined') {
    window.DataFlowVisualizer = DataFlowVisualizer;
}

console.log('[DataFlowVisualizer] 模块加载完成');