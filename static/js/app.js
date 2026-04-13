// 大类资产配置指标监控面板 - 前端脚本

// 标的名称映射
const TICKER_NAMES = {
    '000300.SH': '沪深300',
    '000905.SH': '中证500',
    '000852.SH': '中证1000',
    '932000.CSI': '科创50',
    '8841431.WI': '万得微盘股指数',
    '881001.WI': '万得全A',
};

// 标的颜色映射
const TICKER_COLORS = {
    '000300.SH': '#00b8a9',
    '000905.SH': '#f75b5b',
    '000852.SH': '#f7cc35',
    '932000.CSI': '#4caf50',
    '8841431.WI': '#9c27b0',
    '881001.WI': '#2196f3',
};

// 指标分类配置（按数据类别 + 分析目的）
// 顶层是数据大类（量价指标类、宏观类、另类数据类），每个大类下包含投资目的子类
const INDICATOR_CATEGORIES = {
    '量价指标类': {
        description: '量价类技术指标',
        subcategories: {
            '趋势跟踪': { patterns: ['ma', 'ma_dev'], description: '均线及偏离度' },
            '动量反转': { patterns: ['mom', 'rsi'], description: '动量指标及RSI' },
            '波动风险': { patterns: ['vol'], description: '年化波动率' },
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
let chartCache = {};  // 图表数据缓存

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

            // 渲染导航
            renderNavigator(data.indicators);

            // 绑定时间范围按钮
            bindRangeButtons();

            // 绑定自定义日期范围
            bindCustomDateRange();

            // 自动点击第一个指标
            var firstNavItem = document.querySelector('.nav-item');
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
        case 'amt':
            return `${tickerName} 成交额`;
        case 'pchg_abs':
            return `${tickerName} 涨跌幅`;
        case 'rs':
            return `${tickerName} 相对强弱`;
        case 'rt':
            return `${tickerName} 相对换手率`;
        case 'rsi':
            return `${tickerName} RSI`;
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
                    <div class="nav-item" data-chart="${ind.id}">
                      <span class="nav-dot" style="background: ${getTickerColor(ind.ticker)}"></span>
                      <span class="nav-text">${getIndicatorDisplayName(ind)}</span>
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
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.stopPropagation();

            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
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
    document.querySelectorAll('.range-btn[data-range]').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.range-btn[data-range]').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentRange = this.dataset.range;
            applyTimeRange();
        });
    });
}

// 绑定自定义日期范围
function bindCustomDateRange() {
    const applyBtn = document.getElementById('applyCustomRange');
    if (applyBtn) {
        applyBtn.addEventListener('click', applyCustomDateRangeHandler);
    }
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
    Plotly.purge(container);

    // 获取图表数据
    let chartConfig = chartCache[chartId];

    if (!chartConfig) {
        console.log('[loadChart] 步骤4: 从API获取数据');
        fetch(`/api/charts/${chartId}`)
            .then(function(response) {
                console.log('[loadChart] API响应状态:', response.status);
                if (!response.ok) {
                    throw new Error('图表不存在');
                }
                return response.json();
            })
            .then(function(data) {
                console.log('[loadChart] API数据获取成功');
                chartCache[chartId] = data;
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
    if (!container || !container.data || !container.data[0]) return;

    const trace = container.data[0];
    if (!trace.x || trace.x.length === 0) return;

    let startDate, endDateVal;

    if (endDate !== undefined) {
        // 自定义区间
        startDate = new Date(rangeOrStart);
        endDateVal = new Date(endDate);
    } else {
        // 预设区间
        const range = rangeOrStart || currentRange;
        // 使用数据的最新日期作为"今天"
        const dataEndDate = trace.x[trace.x.length - 1];

        console.log('applyTimeRange:', range, 'currentRange:', currentRange, 'dataEndDate:', dataEndDate);

        if (range === 'ALL') {
            // ALL: 显示数据的全历史范围
            Plotly.relayout(container, {
                'xaxis.range': [trace.x[0], trace.x[trace.x.length - 1]],
                'xaxis.rangeslider.visible': true
            });
            return;
        }

        startDate = getDateRange(range, dataEndDate);
        endDateVal = new Date(dataEndDate);
    }

    if (!startDate) {
        // ALL或其他特殊情况：显示全数据
        Plotly.relayout(container, {
            'xaxis.range': [trace.x[0], trace.x[trace.x.length - 1]],
            'xaxis.rangeslider.visible': true
        });
        return;
    }

    const startMs = startDate.getTime();
    const endMs = endDateVal.getTime();

    console.log('startMs:', startMs, 'endMs:', endMs);
    console.log('trace.x[0]:', trace.x[0], 'last:', trace.x[trace.x.length - 1]);

    // 找到在范围内的起始和结束索引
    let visibleStart = 0;
    let visibleEnd = trace.x.length - 1;

    // 找到第一个 >= startMs 的索引
    for (let i = 0; i < trace.x.length; i++) {
        const dateMs = new Date(trace.x[i]).getTime();
        if (!isNaN(dateMs) && dateMs >= startMs) {
            visibleStart = i;
            break;
        }
    }

    // 找到最后一个 <= endMs 的索引
    for (let i = trace.x.length - 1; i >= 0; i--) {
        const dateMs = new Date(trace.x[i]).getTime();
        if (!isNaN(dateMs) && dateMs <= endMs) {
            visibleEnd = i;
            break;
        }
    }

    console.log('visibleStart:', visibleStart, 'visibleEnd:', visibleEnd);

    // 确保有效范围
    if (visibleStart <= visibleEnd) {
        // 使用 Plotly 兼容的日期格式
        const rangeStr = [trace.x[visibleStart], trace.x[visibleEnd]];
        console.log('Setting range:', rangeStr);

        Plotly.relayout(container, {
            'xaxis.range': rangeStr,
            'xaxis.rangeslider.visible': true,
            'yaxis.autorange': true,  // 保持 Y 轴自适应
        });
    }
}
