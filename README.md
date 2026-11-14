# NetGateShow

一个 Windows 桌面置顶悬浮球：显示当前网络**出口 IP / 节点所在地**，并用 🟢🟡🔴 表示连接状态。单个 exe，无需安装任何运行库。

## 功能

- **小球模式**：显示出口国家英文代码（JP、US、HK…）和响应延迟，外圈颜色表示状态
- **详情面板**（双击切换）：位置（国家 · 省 · 市）、出口 IP、运营商 / AS 号、状态、更新时间、刷新间隔
- **状态颜色**
  - 🟢 绿色：延迟低于阈值（默认 800ms）
  - 🟡 黄色：延迟偏高，或主查询接口失败、改用了备用接口
  - 🔴 红色：所有接口都无法访问，并显示原因（代理连接失败、请求超时、DNS 解析失败等）
- **刷新间隔**按秒设置：预设 10 / 15 / 30 / 60 / 120 / 300 秒，或自定义（5–86400 秒）
- 拖动可移动位置并记住；右键菜单可设置不透明度、开机自启、复制出口信息等
- 只允许运行一个实例；不写日志

## 适用的上网方式

它向公网 IP 查询服务（ip-api.com，备用 ipwho.is、ipinfo.io）发请求，所以测到的就是实际出口，不依赖任何特定代理软件：

- **直连**：显示运营商出口
- **VPN / TUN 模式**（WireGuard、OpenVPN、v2rayN / sing-box / Clash 的 TUN 等）：自动生效
- **系统代理模式**：每次检测都会读取 Windows 系统代理设置，换软件或开关代理都能跟上
- **只开本地端口、不改系统代理的软件**：在配置文件里填写 `proxy`（支持 `http://` 和 `socks5://`）

> 暂不解析 PAC 脚本；PAC 模式下会按直连检测。按规则分流时，显示的是“访问查询服务时”所走的线路。

## 下载使用

到 [Releases](../../releases) 下载 `NetGateShow.exe`，放到任意文件夹，双击运行即可。首次运行会在 exe 同目录生成配置文件 `NetGateShow.json`。

## 配置文件 `NetGateShow.json`

| 字段 | 默认值 | 说明 |
|---|---|---|
| `interval_sec` | `30` | 刷新间隔（秒） |
| `good_latency_ms` | `800` | 绿 / 黄的延迟分界 |
| `use_system_proxy` | `true` | 是否通过系统代理检测 |
| `proxy` | `""` | 手动指定代理，如 `socks5://127.0.0.1:1080`；填写后优先于系统代理 |
| `opacity_pct` | `100` | 不透明度（20–100） |
| `expanded` | `false` | 是否显示详情面板 |
| `x`, `y` | 自动 | 窗口位置 |

## 资源开销（估算）

内存约 10–20 MB；CPU 平时接近 0%；每次检测约 1–2 KB 流量（30 秒间隔约 4 MB/天）。

## 从源码构建

需要 Go 1.21+，仅使用标准库（Win32 + GDI+ 直接调用，无 cgo）。

```bash
# Windows
go build -trimpath -ldflags "-H windowsgui -s -w" -o NetGateShow.exe .

# 在 Linux / macOS 上交叉编译
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "-H windowsgui -s -w" -o NetGateShow.exe .
```

`rsrc_windows_amd64.syso` 包含程序图标和清单（DPI 感知、通用控件 v6），由 `mkres.py` 生成（需要 Python + Pillow）：

```bash
python3 mkres.py rsrc_windows_amd64.syso app.ico
```

发布：改 `VERSION` 里的版本号（如 `1.0.2`），可选写 `release-notes/v1.0.2.md`，推到 `main`。GitHub Actions 会在云端编译 `NetGateShow.exe`，发现这个版本还没发布就自动打 tag、创建 Release；版本号没变的推送只编译、不发布。

注意：`win32.go` 里包装 Windows 调用的 `call()` 必须带 `//go:uintptrescapes`，否则传给 Windows 的局部变量地址可能在栈搬家后失效，导致偶尔崩溃（v1.0.1 修复）。

## 文件说明

- `main.go`：窗口、绘制、菜单、配置
- `net.go`：出口检测、系统代理读取
- `win32.go`：Win32 / GDI+ 接口声明
- `mkres.py`：生成图标与清单资源
