// 大类资产配置指标监控面板 - 前端脚本

// 标的名称映射
const TICKER_NAMES = {
    '000300.SH': '沪深300',
    '000905.SH': '中证500',
    '000852.SH': '中证1000',
    '932000.CSI': '科创50',
    '8841431.WI': '万得微盘股指数',
    '881001.WI': '万得全A',
    'SH_510050IV.WI': '50ETF隐含波动率',
    'SH_510300IV.WI': '300ETF隐含波动率',
    'SH_510500IV.WI': '500ETF隐含波动率',
    'CFE_000852IV.WI': '中证1000股指隐含波动率',
};

// 标的颜色映射
const TICKER_COLORS = {
    '000300.SH': '#00b8a9',
    '000905.SH': '#f75b5b',
    '000852.SH': '#f7cc35',
    '932000.CSI': '#4caf50',
    '8841431.WI': '#9c27b0',
    '881001.WI': '#2196f3',
    'SH_510050IV.WI': '#ff9800',
    'SH_510300IV.WI': '#ffb74d',
    'SH_510500IV.WI': '#ff7043',
    'CFE_000852IV.WI': '#ab47bc',
};

// 指标分类配置（按数据类别 + 分析目的）
// 顶层是数据大类（量价指标类、宏观类、另类数据类），每个大类下包含投资目的子类
const INDICATOR_CATEGORIES = {
    '量价指标类': {
        description: '量价类技术指标',
        subcategories: {
            '趋势跟踪': { patterns: ['ma', 'ma_dev', 'high_new', 'low_new'], description: '均线、偏离度及新高新低' },
            '动量反转': { patterns: ['mom', 'rsi', 'rsi_analysis', 'return_acf1'], description: '动量、RSI及趋势连续度' },
            '波动风险': { patterns: ['vol', 'iv'], description: '年化波动率及隐含波动率' },
            '市场情绪': { patterns: ['amt', 'ma_turnover', 'pchg_abs', 'market_amt_ratio'], description: '成交额及换手率' },
            '风格切换': { patterns: ['rs', 'rt'], description: '相对强弱比' }
        }
    },
    '宏观类': {
        description: '宏观经济指标',
        subcategories: {}
    },
    '另类数据类': {
        description: '另类数据指标',
        subcategories: {}
    }
};

// 全局状态
let currentChartId = null;
let currentRange = '6M';
let currentRollingWindow = '1Y';  // 当前滚动窗口期
let currentShowStatsOverlay = localStorage.getItem('showStatsOverlay') !== 'false';  // 叠加层开关
let chartCache = {};  // 图表数据缓存
const CACHE_EXPIRY_MS = 5 * 60 * 1000;  // 缓存过期时间：5分钟
let chartEnhancer = null;  // 图表增强器实例
let dataFlowVisualizer = null;  // 数据流可视化实例
let allIndicators = null;  // 所有指标数据
const ENABLE_CHART_ENHANCER = false;  // 关闭闪烁高亮点效果
const ENABLE_DATA_FLOW_VISUALIZER = false;  // 关闭流动圆点/连接线效果

/* ================================================
   性能优化工具函数
   ================================================ */

/**
 * 防抖函数 - 延迟执行，避免频繁调用
 * @param {Function} func 要执行的函数
 * @param {number} wait 等待时间（毫秒）
 * @param {boolean} immediate 是否立即执行
 * @returns {Function} 防抖处理后的函数
 */
function debounce(func, wait = 300, immediate = false) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

/**
 * 节流函数 - 限制执行频率
 * @param {Function} func 要执行的函数
 * @param {number} limit 限制时间（毫秒）
 * @returns {Function} 节流处理后的函数
 */
function throttle(func, limit = 300) {
    let inThrottle;
    return function() {
        const context = this;
        const args = arguments;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 批量DOM操作优化 - 使用文档片段
 * @param {Function} callback 包含DOM操作的回调函数
 * @param {HTMLElement} container 容器元素（可选）
 */
function batchDOMUpdate(callback, container = document.body) {
    if (typeof DocumentFragment !== 'undefined') {
        const fragment = document.createDocumentFragment();
        callback(fragment);
        container.appendChild(fragment);
    } else {
        callback();
    }
}

/**
 * 检测设备性能并返回数据流强度
 * @returns {number} 强度值 0.3-1.0
 */
function getDataFlowIntensity() {
    // 默认强度
    let intensity = 1.0;

    // 检测移动设备
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    if (isMobile) {
        intensity *= 0.6; // 移动设备降低强度
    }

    // 检测低电量模式
    if (navigator.getBattery) {
        navigator.getBattery().then(function(battery) {
            if (battery.level < 0.2 || battery.charging === false) {
                intensity *= 0.7; // 低电量时降低强度
            }
        }).catch(function() {
            // 忽略错误
        });
    }

    // 检测触摸设备（无悬停能力）
    if (matchMedia('(hover: none) and (pointer: coarse)').matches) {
        intensity *= 0.8; // 触摸设备降低强度
    }

    // 检测减少动画偏好
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
        intensity *= 0.5; // 用户偏好减少动画
    }

    // 确保强度在合理范围内
    return Math.max(0.3, Math.min(1.0, intensity));
}

// DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('[初始化] 开始初始化');

    // 检查 Plotly
    if (typeof Plotly === 'undefined') {
        console.error('[初始化] Plotly 未定义!');
        document.getElementById('mainChart').innerHTML = '<div class="welcome"><div class="welcome-icon">&#9888;</div><h2>加载失败</h2><p>Plotly 库未加载，请检查网络后刷新页面</p></div>';
        return;
    }
    console.log('[初始化] Plotly 已就绪');

    // 加载指标列表
    fetch('/api/indicators')
        .then(function(response) {
            console.log('[初始化] API响应:', response.status);
            if (!response.ok) {
                throw new Error('获取指标列表失败');
            }
            return response.json();
        })
        .then(function(data) {
            console.log('[初始化] 指标数据获取成功, 数量:', Object.keys(data.indicators).length);

            // 保存指标数据用于搜索
            allIndicators = data.indicators;

            // 渲染导航
            renderNavigator(data.indicators);

            // 绑定时间范围按钮
            bindRangeButtons();

            // 绑定滚动窗口选择按钮
            bindWindowButtons();
            // 绑定叠加层开关
            bindStatsOverlayToggle();

            // 绑定自定义日期范围
            bindCustomDateRange();

            // 绑定搜索功能
            bindSearchFunctionality();

            // 自动点击第一个指标
            var firstNavItem = document.querySelector('.indicator-item');
            if (firstNavItem) {
                console.log('[初始化] 自动点击第一个指标');
                firstNavItem.click();
            } else {
                console.error('[初始化] 未找到指标项');
                document.getElementById('mainChart').innerHTML = '<div class="welcome"><div class="welcome-icon">&#9888;</div><h2>暂无指标</h2><p>请检查数据源</p></div>';
            }
        })
        .catch(function(error) {
            console.error('[初始化] 失败:', error);
            document.getElementById('mainChart').innerHTML = '<div class="welcome"><div class="welcome-icon">&#9888;</div><h2>加载失败</h2><p>' + error.message + '</p></div>';
        });
});

// 获取标的名称
function getTickerName(ticker) {
    // 如果是相对强弱对比，ticker 格式是 "000300.SH_vs_000905.SH"
    if (ticker.includes('_vs_')) {
        const [a, b] = ticker.split('_vs_');
        return `${TICKER_NAMES[a] || a} vs ${TICKER_NAMES[b] || b}`;
    }
    return TICKER_NAMES[ticker] || ticker;
}

// 获取标的颜色
function getTickerColor(ticker) {
    if (ticker.includes('_vs_')) {
        const a = ticker.split('_vs_')[0];
        return TICKER_COLORS[a] || '#888888';
    }
    return TICKER_COLORS[ticker] || '#888888';
}

// 生成指标显示名称
function getIndicatorDisplayName(ind) {
    const tickerName = getTickerName(ind.ticker);
    const window = ind.window;

    switch (ind.pattern) {
        case 'ma':
            return `${tickerName} ${window}日均线`;
        case 'ma_dev':
            return `${tickerName} ${window}日偏离度`;
        case 'mom':
            return `${tickerName} ${window}日动量`;
        case 'vol':
            return `${tickerName} ${window}日波动率`;
        case 'iv':
            return `${tickerName} 隐含波动率`;
        case 'amt':
            return `${tickerName} 成交额`;
        case 'pchg_abs':
            return `${tickerName} 涨跌幅`;
        case 'high_new':
            return `${tickerName} ${window}日新高信号`;
        case 'low_new':
            return `${tickerName} ${window}日新低信号`;
        case 'return_acf1':
            return `${tickerName} ${window}日趋势连续度`;
        case 'rs':
            return `${tickerName} 相对强弱`;
        case 'rt':
            return `${tickerName} 相对换手率`;
        case 'rsi':
            return `${tickerName} RSI`;
        case 'rsi_analysis':
            return `${tickerName} RSI分析`;
        case 'ma_turnover':
            return `${tickerName} ${window}日换手率`;
        case 'market_amt_ratio':
            return `${tickerName} 市场占比`;
        default:
            return `${tickerName} ${ind.name}`;
    }
}

// 判断指标属于哪个投资目的分类
function getIndicatorCategory(ind) {
    const pattern = ind.pattern;

    for (const dataCat of Object.values(INDICATOR_CATEGORIES)) {
        for (const [subcat, subcatConfig] of Object.entries(dataCat.subcategories)) {
            if (subcatConfig.patterns.includes(pattern)) {
                return subcat;
            }
        }
    }
    return '其他';
}

// 渲染指标导航（按分析目的分类）
function renderNavigator(indicators) {
    const navContainer = document.querySelector('.sidebar-section:last-child');
    let html = '';

    // 按子类别（投资目的）组织指标
    const categorized = {};

    for (const dataConfig of Object.values(INDICATOR_CATEGORIES)) {
        for (const subcat of Object.keys(dataConfig.subcategories)) {
            categorized[subcat] = [];
        }
    }

    // 遍历所有指标，分类
    for (const [catName, types] of Object.entries(indicators)) {
        for (const [typeName, indList] of Object.entries(types)) {
            for (const ind of indList) {
                const category = getIndicatorCategory(ind);
                if (category && categorized[category] !== undefined) {
                    categorized[category].push(ind);
                }
            }
        }
    }

    // 生成HTML - 两级可折叠结构
    for (const [dataCat, dataConfig] of Object.entries(INDICATOR_CATEGORIES)) {
        // 检查是否有子类别有指标
        let hasIndicators = false;
        for (const [subcat, subcatConfig] of Object.entries(dataConfig.subcategories)) {
            if (categorized[subcat] && categorized[subcat].length > 0) {
                hasIndicators = true;
                break;
            }
        }
        if (!hasIndicators) continue;

        // 第一层：数据大类
        html += `
        <div class="category-group">
            <div class="category-header">
                <span class="category-title">${dataCat}</span>
                <span class="category-toggle">&#9660;</span>
            </div>
            <div class="category-items">`;

        // 第二层：投资目的子类
        for (const [subcat, subcatConfig] of Object.entries(dataConfig.subcategories)) {
            const inds = categorized[subcat];
            if (!inds || inds.length === 0) continue;

            html += `
                <div class="subcategory-title">
                    <span class="subcategory-toggle">&#9658;</span>
                    ${subcat}
                </div>
                <div class="subcategory-items">`;

            for (const ind of inds) {
                html += `
                    <div class="indicator-item" data-chart="${ind.id}">
                      <span class="indicator-dot" style="background: ${getTickerColor(ind.ticker)}"></span>
                      <span class="indicator-name">${getIndicatorDisplayName(ind)}</span>
                    </div>`;
            }

            html += `
                </div>`;
        }

        html += `
            </div>
        </div>`;
    }

    navContainer.innerHTML = html;

    // 绑定指标项点击事件
    document.querySelectorAll('.indicator-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.stopPropagation();

            document.querySelectorAll('.indicator-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            loadChart(this.dataset.chart);
        });
    });

    // 绑定第一层分类折叠事件（数据大类）
    document.querySelectorAll('.category-header').forEach(header => {
        header.addEventListener('click', function(e) {
            e.stopPropagation();
            const group = this.closest('.category-group');
            const items = group.querySelector('.category-items');

            if (group.classList.contains('collapsed')) {
                group.classList.remove('collapsed');
                items.style.maxHeight = items.scrollHeight + 'px';
            } else {
                group.classList.add('collapsed');
                items.style.maxHeight = '0px';
            }
        });

        // 初始化max-height
        const items = header.closest('.category-group').querySelector('.category-items');
        items.style.maxHeight = items.scrollHeight + 'px';
    });

    // 绑定第二层分类折叠事件（投资目的）
    document.querySelectorAll('.subcategory-title').forEach(title => {
        title.addEventListener('click', function(e) {
            e.stopPropagation();
            const group = this.closest('.subcategory-group') || this.parentElement;
            const items = this.nextElementSibling;

            if (items && items.classList.contains('subcategory-items')) {
                if (items.style.maxHeight === '0px' || !items.style.maxHeight) {
                    items.style.maxHeight = items.scrollHeight + 'px';
                    this.querySelector('.subcategory-toggle').style.transform = 'rotate(90deg)';
                } else {
                    items.style.maxHeight = '0px';
                    this.querySelector('.subcategory-toggle').style.transform = 'rotate(0deg)';
                }
            }
        });
    });
}

// 绑定时间范围按钮
function bindRangeButtons() {
    document.querySelectorAll('.range-preset[data-range]').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.range-preset[data-range]').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentRange = this.dataset.range;
            applyTimeRange();
        });
    });
}

// 绑定滚动窗口选择按钮
function bindWindowButtons() {
    document.querySelectorAll('.window-btn[data-window]').forEach(btn => {
        btn.addEventListener('click', function() {
            // 更新按钮状态
            document.querySelectorAll('.window-btn[data-window]').forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            // 更新当前窗口值
            const newWindow = this.dataset.window;
            if (newWindow !== currentRollingWindow) {
                currentRollingWindow = newWindow;
                console.log('[窗口选择] 切换到:', currentRollingWindow);

                // 如果当前有加载图表，重新加载以应用新窗口
                if (currentChartId) {
                    // 清除相关缓存，强制重新获取
                    Object.keys(chartCache).forEach(key => {
                        if (key.startsWith(currentChartId + '_')) {
                            delete chartCache[key];
                        }
                    });
                    loadChart(currentChartId);
                }
            }
        });
    });
}

// 绑定叠加层开关按钮
function bindStatsOverlayToggle() {
    const btn = document.getElementById('statsOverlayToggle');
    if (!btn) return;

    const updateButtonState = () => {
        if (currentShowStatsOverlay) {
            btn.classList.add('active');
            btn.textContent = '叠加层: 开';
        } else {
            btn.classList.remove('active');
            btn.textContent = '叠加层: 关';
        }
    };

    updateButtonState();

    btn.addEventListener('click', function() {
        currentShowStatsOverlay = !currentShowStatsOverlay;
        localStorage.setItem('showStatsOverlay', String(currentShowStatsOverlay));
        updateButtonState();

        // 切换后重载当前图以应用新设置
        if (currentChartId) {
            Object.keys(chartCache).forEach(key => {
                if (key.startsWith(currentChartId + '_')) {
                    delete chartCache[key];
                }
            });
            loadChart(currentChartId);
        }
    });
}

// 绑定自定义日期范围
function bindCustomDateRange() {
    const applyBtn = document.getElementById('applyCustomRange');
    if (applyBtn) {
        applyBtn.addEventListener('click', applyCustomDateRangeHandler);
    }
}

// 绑定搜索功能
function bindSearchFunctionality() {
    const searchInput = document.querySelector('.search-input');
    const searchClear = document.querySelector('.search-clear');

    if (!searchInput || !searchClear) {
        console.warn('[搜索] 搜索元素未找到');
        return;
    }

    console.log('[搜索] 绑定搜索功能');

    // 搜索输入事件 - 使用防抖优化性能
    const debouncedSearch = debounce(function(e) {
        const query = e.target.value.trim();
        performSearch(query);
    }, 300);

    searchInput.addEventListener('input', debouncedSearch);

    // 清除搜索
    searchClear.addEventListener('click', function() {
        searchInput.value = '';
        searchInput.focus();
        performSearch('');
    });

    // 键盘快捷键
    searchInput.addEventListener('keydown', function(e) {
        // ESC键清除搜索
        if (e.key === 'Escape') {
            searchInput.value = '';
            performSearch('');
            searchInput.blur();
        }
        // Ctrl+F 或 Cmd+F 聚焦搜索框
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            searchInput.focus();
            searchInput.select();
        }
    });
}

// 执行搜索
function performSearch(query) {
    if (!allIndicators) {
        console.warn('[搜索] 指标数据未加载');
        return;
    }

    console.log('[搜索] 执行搜索, 关键词:', query);

    if (!query) {
        // 恢复原始导航
        renderNavigator(allIndicators);
        rebindNavigationEvents();
        return;
    }

    // 过滤指标
    const filteredIndicators = filterIndicators(query);

    // 渲染搜索结果（扁平化列表）
    renderSearchResults(filteredIndicators, query);
}

// 过滤指标
function filterIndicators(query) {
    const filtered = {};
    const queryLower = query.toLowerCase();

    // 遍历所有指标
    for (const [catName, types] of Object.entries(allIndicators)) {
        for (const [typeName, indList] of Object.entries(types)) {
            for (const ind of indList) {
                // 检查是否匹配
                if (isIndicatorMatch(ind, queryLower)) {
                    if (!filtered[catName]) {
                        filtered[catName] = {};
                    }
                    if (!filtered[catName][typeName]) {
                        filtered[catName][typeName] = [];
                    }
                    filtered[catName][typeName].push(ind);
                }
            }
        }
    }

    return filtered;
}

// 检查指标是否匹配搜索
function isIndicatorMatch(ind, queryLower) {
    // 匹配标的名称
    const tickerName = getTickerName(ind.ticker).toLowerCase();
    if (tickerName.includes(queryLower)) {
        return true;
    }

    // 匹配指标显示名称
    const displayName = getIndicatorDisplayName(ind).toLowerCase();
    if (displayName.includes(queryLower)) {
        return true;
    }

    // 匹配指标模式
    if (ind.pattern && ind.pattern.toLowerCase().includes(queryLower)) {
        return true;
    }

    // 匹配指标ID
    if (ind.id && ind.id.toLowerCase().includes(queryLower)) {
        return true;
    }

    return false;
}

// 重新绑定导航事件（搜索后需要重新绑定）
function rebindNavigationEvents() {
    // 绑定指标项点击事件
    document.querySelectorAll('.indicator-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.stopPropagation();

            document.querySelectorAll('.indicator-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            loadChart(this.dataset.chart);
        });
    });

    // 绑定分类折叠事件
    bindCategoryToggleEvents();
}

// 绑定分类折叠事件
function bindCategoryToggleEvents() {
    // 第一层分类折叠事件（数据大类）
    document.querySelectorAll('.category-header').forEach(header => {
        header.addEventListener('click', function(e) {
            e.stopPropagation();
            const group = this.closest('.category-group');
            const items = group.querySelector('.category-items');

            if (group.classList.contains('collapsed')) {
                group.classList.remove('collapsed');
                items.style.maxHeight = items.scrollHeight + 'px';
            } else {
                group.classList.add('collapsed');
                items.style.maxHeight = '0px';
            }
        });

        // 初始化max-height
        if (!header.closest('.category-group').classList.contains('collapsed')) {
            const items = header.closest('.category-group').querySelector('.category-items');
            if (items) {
                items.style.maxHeight = items.scrollHeight + 'px';
            }
        }
    });

    // 第二层分类折叠事件（投资目的）
    document.querySelectorAll('.subcategory-title').forEach(title => {
        title.addEventListener('click', function(e) {
            e.stopPropagation();
            const items = this.nextElementSibling;

            if (items && items.classList.contains('subcategory-items')) {
                if (items.style.maxHeight === '0px' || !items.style.maxHeight) {
                    items.style.maxHeight = items.scrollHeight + 'px';
                    this.querySelector('.subcategory-toggle').style.transform = 'rotate(90deg)';
                } else {
                    items.style.maxHeight = '0px';
                    this.querySelector('.subcategory-toggle').style.transform = 'rotate(0deg)';
                }
            }
        });
    });
}

// 渲染搜索结果（扁平化列表）
function renderSearchResults(filteredIndicators, query) {
    const navContainer = document.querySelector('.sidebar-section:last-child');
    if (!navContainer) return;

    let html = '';
    let resultCount = 0;

    // 统计结果数量
    for (const [catName, types] of Object.entries(filteredIndicators)) {
        for (const [typeName, indList] of Object.entries(types)) {
            resultCount += indList.length;
        }
    }

    // 搜索结果标题
    html += `
        <div class="search-results-header">
            <div class="search-results-title">搜索结果</div>
            <div class="search-results-count">${resultCount} 个结果</div>
            <div class="search-query">"${query}"</div>
        </div>
    `;

    // 如果没有结果
    if (resultCount === 0) {
        html += `
            <div class="no-results">
                <div class="no-results-icon">&#128269;</div>
                <div class="no-results-text">未找到匹配的指标</div>
                <div class="no-results-hint">尝试使用不同的关键词</div>
            </div>
        `;
    } else {
        // 扁平化列表显示所有结果
        html += `<div class="search-results-list">`;

        for (const [catName, types] of Object.entries(filteredIndicators)) {
            for (const [typeName, indList] of Object.entries(types)) {
                for (const ind of indList) {
                    html += `
                        <div class="nav-item search-result-item" data-chart="${ind.id}">
                            <span class="nav-dot" style="background: ${getTickerColor(ind.ticker)}"></span>
                            <span class="nav-text">${getIndicatorDisplayName(ind)}</span>
                            <span class="search-result-category">${getIndicatorCategory(ind)}</span>
                        </div>
                    `;
                }
            }
        }

        html += `</div>`;
    }

    navContainer.innerHTML = html;

    // 绑定结果项的点击事件
    document.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.stopPropagation();

            // 清除所有激活状态
            document.querySelectorAll('.indicator-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            loadChart(this.dataset.chart);
        });
    });
}

// 应用自定义日期范围
function applyCustomDateRangeHandler() {
    const startInput = document.getElementById('customStartDate');
    const endInput = document.getElementById('customEndDate');

    if (!startInput || !endInput) return;

    const startDate = startInput.value;
    const endDate = endInput.value;

    if (startDate && endDate) {
        document.querySelectorAll('.range-btn[data-range]').forEach(b => b.classList.remove('active'));
        applyTimeRange(startDate, endDate);
    }
}

// 计算日期范围（基于图表数据的最新日期）
function getDateRange(range, dataEndDate) {
    const now = new Date(dataEndDate || new Date());
    let startDate = new Date(now);

    switch(range) {
        case '1M': startDate.setMonth(startDate.getMonth() - 1); break;
        case '3M': startDate.setMonth(startDate.getMonth() - 3); break;
        case '6M': startDate.setMonth(startDate.getMonth() - 6); break;
        case 'YTD': startDate = new Date(now.getFullYear(), 0, 1); break;
        case '1Y': startDate.setFullYear(startDate.getFullYear() - 1); break;
        case '2Y': startDate.setFullYear(startDate.getFullYear() - 2); break;
        case '3Y': startDate.setFullYear(startDate.getFullYear() - 3); break;
        case '5Y': startDate.setFullYear(startDate.getFullYear() - 5); break;
        case 'ALL': return null;
    }
    return startDate;
}

// 加载图表 - 使用同步回调模式避免 Promise 挂起问题
function loadChart(chartId) {
    console.log('[loadChart] 开始加载图表:', chartId);

    // 获取元素引用
    const container = document.getElementById('mainChart');
    const titleEl = document.getElementById('chartTitle');
    const legendEl = document.getElementById('chartLegend');

    if (!container || !titleEl || !legendEl) {
        console.error('[loadChart] DOM 元素未找到');
        return;
    }

    // 显示加载状态 - 使用纯文本加载提示
    container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#8b949e;font-size:14px;">&#128260; 加载中...</div>';
    titleEl.textContent = '加载中...';
    legendEl.innerHTML = '';

    console.log('[loadChart] 步骤1: 加载状态已显示');

    // 检查 Plotly
    if (typeof Plotly === 'undefined') {
        console.error('[loadChart] Plotly 未定义');
        container.innerHTML = '<div class="welcome"><div class="welcome-icon">&#9888;</div><h2>加载失败</h2><p>Plotly 库未加载，请刷新页面</p></div>';
        return;
    }
    console.log('[loadChart] 步骤2: Plotly 已加载');

    // 清除之前的图表
    console.log('[loadChart] 步骤3: 清除旧图表');
    // 销毁图表增强器
    if (chartEnhancer && typeof chartEnhancer.destroy === 'function') {
        chartEnhancer.destroy();
        chartEnhancer = null;
        console.log('[loadChart] 图表增强器已销毁');
    }
    // 停止数据流可视化
    if (dataFlowVisualizer && typeof dataFlowVisualizer.stop === 'function') {
        dataFlowVisualizer.stop();
        dataFlowVisualizer = null;
        console.log('[loadChart] 数据流可视化已停止');
    }
    Plotly.purge(container);

    // 获取图表数据 - 带缓存过期检查（缓存键包含 rolling window）
    const cacheKey = chartId + '_' + currentRollingWindow + '_stats' + (currentShowStatsOverlay ? '1' : '0');
    const cachedEntry = chartCache[cacheKey];
    let chartConfig = null;
    let cacheValid = false;

    if (cachedEntry) {
        // 检查缓存格式：可能是旧格式（直接数据）或新格式（{data, timestamp}）
        if (cachedEntry.data && cachedEntry.timestamp) {
            // 新格式：检查是否过期
            const age = Date.now() - cachedEntry.timestamp;
            if (age < CACHE_EXPIRY_MS) {
                chartConfig = cachedEntry.data;
                cacheValid = true;
                console.log(`[loadChart] 缓存有效，年龄: ${Math.round(age/1000)}秒`);
            } else {
                console.log(`[loadChart] 缓存已过期，年龄: ${Math.round(age/1000)}秒`);
                delete chartCache[chartId]; // 清除过期缓存
            }
        } else {
            // 旧格式：直接使用，视为永久有效（向后兼容）
            chartConfig = cachedEntry;
            cacheValid = true;
            console.log('[loadChart] 使用旧格式缓存');
        }
    }

    if (!cacheValid) {
        console.log('[loadChart] 步骤4: 从API获取数据');
        fetch(`/api/charts/${chartId}?window=${currentRollingWindow}&show_stats=${currentShowStatsOverlay}`)
            .then(function(response) {
                console.log('[loadChart] API响应状态:', response.status);
                if (!response.ok) {
                    throw new Error('图表不存在');
                }
                return response.json();
            })
            .then(function(data) {
                console.log('[loadChart] API数据获取成功');
                chartCache[cacheKey] = {
                    data: data,
                    timestamp: Date.now()
                };
                renderChartWithData(container, titleEl, legendEl, data, chartId);
            })
            .catch(function(error) {
                console.error('[loadChart] 获取数据失败:', error);
                container.innerHTML = '<div class="welcome"><div class="welcome-icon">&#9888;</div><h2>加载失败</h2><p>' + error.message + '</p></div>';
            });
    } else {
        console.log('[loadChart] 步骤4: 使用缓存数据');
        renderChartWithData(container, titleEl, legendEl, chartConfig, chartId);
    }
}

// 渲染图表（从缓存或刚获取的数据）
function renderChartWithData(container, titleEl, legendEl, chartConfig, chartId) {
    console.log('[renderChartWithData] 开始渲染, chartId:', chartId);

    // 更新标题
    titleEl.textContent = chartConfig.title;

    console.log('[renderChartWithData] 数据格式检查:', {
        hasData: !!chartConfig.data,
        dataLength: chartConfig.data ? chartConfig.data.length : 0,
        hasLayout: !!chartConfig.layout
    });

    // 设置超时保护
    var renderTimeout = setTimeout(function() {
        console.error('[renderChartWithData] 渲染超时!');
        container.innerHTML = '<div class="welcome"><div class="welcome-icon">&#9888;</div><h2>渲染超时</h2><p>请刷新页面重试</p></div>';
    }, 20000);

    // 使用 Plotly.newPlot
    try {
        Plotly.newPlot(container, chartConfig.data, chartConfig.layout, {
            responsive: true,
            displayModeBar: true,
            scrollZoom: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            displaylogo: false,
        }).then(function() {
            clearTimeout(renderTimeout);
            console.log('[renderChartWithData] 渲染成功!');

            // 强制清除可能残留的加载状态
            var loadingEl = container.querySelector('.loading');
            if (loadingEl) {
                loadingEl.remove();
            }

            // 更新图例
            legendEl.innerHTML = '';
            if (chartConfig.data && chartConfig.data.length > 0) {
                var colors = ['#00b8a9', '#f75b5b', '#f7cc35', '#4caf50', '#9c27b0', '#2196f3'];
                chartConfig.data.forEach(function(trace, i) {
                    if (trace.name) {
                        var color = colors[i % colors.length];
                        legendEl.innerHTML += '<span class="legend-item"><span class="legend-line" style="background: ' + color + '"></span>' + trace.name + '</span>';
                    }
                });
            }

            currentChartId = chartId;

            // 初始化图表增强器（可开关）
            if (ENABLE_CHART_ENHANCER) {
                console.log('[renderChartWithData] 初始化图表增强器');
                if (typeof ChartEnhancer !== 'undefined') {
                    // 销毁旧的增强器实例
                    if (chartEnhancer && typeof chartEnhancer.destroy === 'function') {
                        chartEnhancer.destroy();
                    }
                    // 创建新的增强器实例
                    chartEnhancer = new ChartEnhancer('mainChart');
                    console.log('[renderChartWithData] 图表增强器初始化完成');
                } else {
                    console.warn('[renderChartWithData] ChartEnhancer 未定义，请检查脚本加载');
                }
            }

            // 初始化数据流可视化（可开关）
            if (ENABLE_DATA_FLOW_VISUALIZER) {
                console.log('[renderChartWithData] 初始化数据流可视化');
                if (typeof DataFlowVisualizer !== 'undefined') {
                    // 停止旧的可视化实例
                    if (dataFlowVisualizer && typeof dataFlowVisualizer.stop === 'function') {
                        dataFlowVisualizer.stop();
                    }
                    // 创建新的可视化实例
                    dataFlowVisualizer = new DataFlowVisualizer('mainChart');
                    dataFlowVisualizer.start();
                    // 根据设备性能调整数据流强度
                    const intensity = getDataFlowIntensity();
                    dataFlowVisualizer.setIntensity(intensity);
                    console.log(`[renderChartWithData] 数据流可视化启动完成，强度: ${intensity.toFixed(2)}`);
                } else {
                    console.warn('[renderChartWithData] DataFlowVisualizer 未定义，请检查脚本加载');
                }
            }

            // 应用时间范围
            console.log('[renderChartWithData] 应用时间范围');
            applyTimeRange();
        }).catch(function(err) {
            clearTimeout(renderTimeout);
            console.error('[renderChartWithData] 渲染失败:', err);
            container.innerHTML = '<div class="welcome"><div class="welcome-icon">&#9888;</div><h2>渲染失败</h2><p>' + err.message + '</p></div>';
        });
    } catch (e) {
        clearTimeout(renderTimeout);
        console.error('[renderChartWithData] Plotly.newPlot 抛出异常:', e);
        container.innerHTML = '<div class="welcome"><div class="welcome-icon">&#9888;</div><h2>渲染异常</h2><p>' + e.message + '</p></div>';
    }
}

// 应用时间范围
function applyTimeRange(rangeOrStart, endDate) {
    if (!currentChartId) return;

    const container = document.getElementById('mainChart');
    if (!container || !container.data || container.data.length === 0) return;

    // 找到主数据trace（带 tozeroy 填充的是主数据线）
    let mainTrace = null;
    for (let i = 0; i < container.data.length; i++) {
        const t = container.data[i];
        if (t.x && t.x.length > 1) {
            // 主数据线使用 tozeroy 填充
            if (t.fill === 'tozeroy') {
                mainTrace = t;
                break;
            }
        }
    }
    // 如果没找到，使用最长的那个trace（通常是主数据线）
    if (!mainTrace) {
        let maxLen = 0;
        for (let i = 0; i < container.data.length; i++) {
            const t = container.data[i];
            if (t.x && t.x.length > maxLen) {
                maxLen = t.x.length;
                mainTrace = t;
            }
        }
    }
    // 如果还是没找到，使用第一个trace
    if (!mainTrace) mainTrace = container.data[0];

    if (!mainTrace.x || mainTrace.x.length === 0) return;

    // 辅助函数：解析日期字符串，处理多种格式
    function parseDate(dateStr) {
        if (!dateStr) return null;
        // 将空格替换为'T'以支持ISO格式
        const normalized = dateStr.replace(' ', 'T');
        const date = new Date(normalized);
        return isNaN(date.getTime()) ? null : date;
    }

    let startDate, endDateVal;

    if (endDate !== undefined) {
        // 自定义区间
        startDate = parseDate(rangeOrStart);
        endDateVal = parseDate(endDate);
    } else {
        // 预设区间
        const range = rangeOrStart || currentRange;
        // 使用数据的最新日期作为"今天"
        const dataEndDate = mainTrace.x[mainTrace.x.length - 1];

        console.log('applyTimeRange:', range, 'currentRange:', currentRange, 'dataEndDate:', dataEndDate);

        if (range === 'ALL') {
            // ALL: 显示数据的全历史范围
            Plotly.relayout(container, {
                'xaxis.range': [mainTrace.x[0], mainTrace.x[mainTrace.x.length - 1]],
                'xaxis.rangeslider.visible': true
            });
            return;
        }

        startDate = getDateRange(range, dataEndDate);
        endDateVal = parseDate(dataEndDate);
    }

    if (!startDate) {
        // ALL或其他特殊情况：显示全数据
        Plotly.relayout(container, {
            'xaxis.range': [mainTrace.x[0], mainTrace.x[mainTrace.x.length - 1]],
            'xaxis.rangeslider.visible': true
        });
        return;
    }

    const startMs = startDate.getTime();
    const endMs = endDateVal ? endDateVal.getTime() : startMs;

    console.log('startMs:', startMs, 'endMs:', endMs);
    console.log('mainTrace.x[0]:', mainTrace.x[0], 'last:', mainTrace.x[mainTrace.x.length - 1]);

    // 找到在范围内的起始和结束索引
    let visibleStart = 0;
    let visibleEnd = mainTrace.x.length - 1;

    // 找到第一个 >= startMs 的索引
    for (let i = 0; i < mainTrace.x.length; i++) {
        const dateMs = new Date(mainTrace.x[i]).getTime();
        if (!isNaN(dateMs) && dateMs >= startMs) {
            visibleStart = i;
            break;
        }
    }

    // 找到最后一个 <= endMs 的索引
    for (let i = mainTrace.x.length - 1; i >= 0; i--) {
        const dateMs = new Date(mainTrace.x[i]).getTime();
        if (!isNaN(dateMs) && dateMs <= endMs) {
            visibleEnd = i;
            break;
        }
    }

    console.log('visibleStart:', visibleStart, 'visibleEnd:', visibleEnd);

    // 确保有效范围
    if (visibleStart <= visibleEnd) {
        // 使用 Plotly 兼容的日期格式
        const rangeStart = mainTrace.x[visibleStart];
        const rangeEnd = mainTrace.x[visibleEnd];
        console.log('Setting range:', [rangeStart, rangeEnd]);

        Plotly.relayout(container, {
            'xaxis.range': [rangeStart, rangeEnd],
            'yaxis.autorange': true,  // 保持 Y 轴自适应
        });
    }
}
