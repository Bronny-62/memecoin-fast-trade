# GMGN Monitor Chrome 插件

## 功能说明

拦截 `gmgn.ai` 网站的 WebSocket 推送数据，过滤出 `twitter_user_monitor_basic` 频道的推文监控信号，并实时转发到本地交易系统执行自动交易。

- 自动劫持页面 WebSocket，对原有页面功能零干扰
- 访问 `gmgn.ai` 时自动打开侧边栏
- 侧边栏实时显示连接状态、数据计数与日志流
- Service Worker 持久运行，侧边栏关闭后仍继续转发数据

## 安装步骤

### 1. 加载插件

1. 打开 Chrome 浏览器
2. 访问 `chrome://extensions/`
3. 打开右上角的 **"开发者模式"** (Developer mode)
4. 点击 **"加载已解压的扩展程序"** (Load unpacked)
5. 选择本目录：`gmgn_monitor_extension/`

### 2. 启动本地交易系统

在项目根目录运行：

```bash
./start_monitor.sh
```

确保 WebSocket 服务运行在 `ws://localhost:8051/ws`

### 3. 连接交易系统

1. 访问 `https://gmgn.ai`，插件侧边栏会自动打开
2. 点击侧边栏中的 **"Trade System Connect"** 按钮
3. 按钮变灰、状态点变绿表示连接成功

### 4. 验证工作状态

侧边栏中有三个状态指示器：

| 指示器 | 说明 |
|--------|------|
| Page Status | 绿色表示 gmgn.ai 页面已加载 |
| Injector | 绿色表示 WebSocket 拦截器已激活并捕获到流量 |
| Trade System (8051) | 绿色表示与本地交易系统连接正常 |

**Captured** 计数：捕获到的 `twitter_user_monitor_basic` 频道消息数量
**Filtered** 计数：被过滤掉的其他频道消息数量

## 数据样本采集

日志区域会实时显示拦截到的原始数据：

1. 等待日志区域出现推文推送条目
2. 点击条目旁的 **"Copy"** 按钮（仅在消息长度 > 50 字符时出现）
3. 将复制内容提供给开发者进行格式映射

## 常见问题

**Q: 访问 gmgn.ai 后侧边栏没有自动弹出？**
A: 点击浏览器右上角的插件图标可手动打开侧边栏。

**Q: Injector 状态一直是 "Pending"？**
A: 打开浏览器开发者工具（F12），查看 Console 是否有报错；检查 Network 标签是否有 WebSocket 连接建立。

**Q: Trade System 显示 "Disconnected"？**
A: 确认本地服务已启动：

```bash
ps aux | grep terminal_server.py
```

**Q: Captured 计数为 0，但 Filtered 持续增加？**
A: 这是正常现象，说明拦截器正常工作，但当前没有 `twitter_user_monitor_basic` 频道的推送。等待目标用户有推文活动即可。

## 技术架构

```
gmgn.ai WebSocket
    │
    ▼
injector.js          ← 运行在页面主世界，monkey-patch WebSocket 构造函数
    │  CustomEvent(GMGN_WS_INTERCEPT)
    ▼
content.js           ← 运行在扩展隔离世界，桥接页面事件与扩展运行时
    │  chrome.runtime.sendMessage
    ▼
background.js        ← Service Worker，过滤频道、维护状态、转发数据
    │  WebSocket(ws://localhost:8051/ws)
    ▼
terminal_server.py   ← 本地交易系统，执行关键词匹配与自动交易
    │
    ▼
side_panel.js        ← 侧边栏 UI，轮询并展示 background 状态
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `manifest.json` | 插件配置清单，Manifest V3 |
| `background.js` | Service Worker，核心逻辑：频道过滤、WebSocket 转发、状态管理 |
| `injector.js` | 注入页面主世界，劫持 WebSocket 构造函数，捕获所有消息 |
| `content.js` | 内容脚本，注入 `injector.js` 并桥接页面事件到扩展运行时 |
| `side_panel.html` | 侧边栏 HTML 结构 |
| `side_panel.js` | 侧边栏逻辑，与 background 通信，渲染状态和日志 |
| `icons/` | 插件图标（16px、48px、128px） |

## 权限说明

| 权限 | 用途 |
|------|------|
| `sidePanel` | 使用 Chrome 侧边栏 API |
| `scripting` | 动态注入内容脚本 |
| `tabs` | 监听页面加载，自动打开侧边栏 |
| `host_permissions: gmgn.ai/*` | 在目标页面注入脚本 |
| `host_permissions: localhost/*` | 连接本地交易系统 WebSocket |
