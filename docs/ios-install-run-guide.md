# iOS 端安装、配置、运行与使用指南

本文面向没有完整 iOS 开发经验的用户，说明如何基于当前 `research-intelligence-ios` 项目，在 iOS 模拟器或真机上运行科研情报 App。

> 当前项目状态：`ios/ResearchIntelApp/ResearchIntelApp` 目录目前是 SwiftUI 源码骨架，还不是完整的 Xcode `.xcodeproj` 工程。因此第一步需要在 Xcode 中新建一个 iOS App 工程，再把现有的 `Models`、`Services`、`Views` 和 App 入口文件加入工程。

---

## 1. 当前项目结构说明

项目根目录：

```text
/mnt/f/AI2/research-intelligence-ios
```

主要目录：

```text
research-intelligence-ios/
├── backend/                         # FastAPI 后端
│   ├── app/main.py                   # FastAPI 入口
│   ├── app/api/v1.py                 # API 路由：主题、文章、今日简报
│   ├── app/core/topics.py            # 神经科学/生物材料/AI/骨科主题配置
│   ├── app/services/collectors/      # PubMed、bioRxiv、medRxiv、arXiv 采集器骨架
│   ├── app/services/summarizers/     # LLM 中文摘要服务骨架
│   └── app/tasks/daily_pipeline.py   # 每日采集与摘要流水线骨架
├── ios/
│   └── ResearchIntelApp/
│       └── ResearchIntelApp/
│           ├── Models/               # Swift 数据模型
│           ├── Services/             # APIClient、通知权限管理
│           ├── Views/                # 今日、主题、搜索、收藏、我的等页面
│           └── ResearchIntelApp.swift# SwiftUI App 入口
└── docs/
    ├── product-plan.md
    ├── architecture.md
    ├── next-steps.md
    └── ios-install-run-guide.md
```

当前 iOS 已有源码文件包括：

- `Models/Article.swift`：文章数据模型。
- `Models/Briefing.swift`：每日简报模型。
- `Models/Topic.swift`：主题模型。
- `Services/APIClient.swift`：访问 FastAPI 后端。
- `Services/NotificationManager.swift`：请求 iOS 通知权限。
- `Views/RootTabView.swift`：底部 Tab 导航。
- `Views/TodayView.swift`：今日简报列表。
- `Views/ArticleRowView.swift`：文章列表卡片。
- `Views/ArticleDetailView.swift`：文章详情页。
- `Views/TopicsView.swift`：主题切换页。
- `Views/SearchView.swift`：搜索页占位。
- `Views/FavoritesView.swift`：收藏页占位。
- `Views/SettingsView.swift`：推送设置和摘要偏好页。

当前后端已提供的基础接口：

```text
GET /health
GET /api/v1/topics
GET /api/v1/articles
GET /api/v1/briefings/today
```

当前 iOS 端默认后端地址位于 `Services/APIClient.swift`：

```swift
private let baseURL = URL(string: "http://127.0.0.1:8000/api/v1")!
```

---

## 2. 你需要准备什么设备和环境

### 2.1 必须有 macOS 才能做 iOS 原生开发

iOS 原生 App 必须使用 Xcode 构建。Xcode 只能安装在 macOS 上，不能直接安装在 Windows 或 Linux 上。

如果当前项目在 Windows 的 F 盘或 WSL 中，例如路径是 `/mnt/f/AI2/research-intelligence-ios`，你需要将项目同步到 Mac 上，常见方式：

1. 用 Git 推送到 GitHub、GitLab、Gitee，再在 Mac 上克隆。
2. 用移动硬盘、网盘、局域网共享复制到 Mac。
3. 如果 Mac 可以访问该磁盘共享，也可以直接打开共享目录，但更推荐复制到 Mac 本地磁盘，避免 Xcode 索引和构建变慢。

推荐 Mac 本地路径示例：

```text
~/Projects/research-intelligence-ios
```

### 2.2 推荐版本

建议使用：

- macOS：macOS 14 Sonoma、macOS 15 Sequoia 或更新版本。
- Xcode：Xcode 15.4 或更新版本；如果系统支持，优先使用 App Store 中最新稳定版 Xcode。
- Swift：Swift 5.9 或更新版本。
- iOS Deployment Target：建议设置为 iOS 17.0 或更高。

为什么建议 iOS 17.0：

- 当前源码使用 SwiftUI。
- 当前页面中使用了 `ContentUnavailableView`，这是 iOS 17 起比较稳妥的系统组件。
- 当前 `APIClient.swift` 使用了较新的 `URL.appending(path:)` 和 `URL.append(queryItems:)` 写法。

如果你希望支持 iOS 16 或更低版本，需要替换 `ContentUnavailableView` 等较新的 API。

### 2.3 Apple ID 和开发者账号

运行到模拟器：

- 通常不需要付费 Apple Developer Program。
- 安装 Xcode 后即可运行。

运行到真机：

- 需要在 Xcode 登录 Apple ID。
- 免费 Apple ID 也可以把 App 安装到自己的真机测试，但证书有效期和能力有限。
- 如果要 TestFlight、正式上架、稳定使用 APNs 推送，建议注册付费 Apple Developer Program。

### 2.4 后端运行环境

后端是 FastAPI，需要 Python 环境。

建议：

- Python 3.11 或 3.12。
- pip。
- 可选：Docker Desktop，用于后续 PostgreSQL、Redis、容器化部署。

---

## 3. 先启动本地 FastAPI 后端

iOS App 的今日简报和主题列表需要访问后端 API。建议先把后端跑起来，再运行 iOS App。

在 Mac 或你的后端运行机器上进入项目后端目录：

```bash
cd /path/to/research-intelligence-ios/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

如果只是模拟器访问，下面这种也可以：

```bash
uvicorn app.main:app --reload
```

但如果要让 iPhone 真机通过局域网访问 Mac 上的后端，必须让后端监听 `0.0.0.0`：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3.1 验证后端是否正常

在浏览器打开：

```text
http://127.0.0.1:8000/health
```

预期看到类似：

```json
{"status":"ok","service":"Research Intelligence API"}
```

再打开：

```text
http://127.0.0.1:8000/api/v1/topics
```

应该看到神经科学、生物材料、AI、骨科四个主题。

打开：

```text
http://127.0.0.1:8000/api/v1/briefings/today
```

应该看到今日简报示例数据。

---

## 4. 理解模拟器、真机和后端地址的区别

### 4.1 iOS 模拟器访问本机后端

如果 FastAPI 后端运行在同一台 Mac 上，iOS 模拟器通常可以使用：

```text
http://127.0.0.1:8000/api/v1
```

当前 `APIClient.swift` 默认就是这个地址，因此模拟器运行时一般不用改。

### 4.2 iPhone 真机访问 Mac 上的本地后端

如果 App 在真机上运行，`127.0.0.1` 指的是 iPhone 自己，不是 Mac。因此真机不能用：

```text
http://127.0.0.1:8000/api/v1
```

真机需要使用 Mac 的局域网 IP，例如：

```text
http://192.168.1.10:8000/api/v1
```

获取 Mac 局域网 IP 的方法：

方法一：macOS 系统设置

1. 打开 System Settings。
2. 进入 Wi-Fi。
3. 点击当前网络详情。
4. 查看 IP Address。

方法二：终端命令

```bash
ipconfig getifaddr en0
```

如果你用有线网络，可能是：

```bash
ipconfig getifaddr en1
```

然后把 `APIClient.swift` 中的地址改成：

```swift
private let baseURL = URL(string: "http://你的Mac局域网IP:8000/api/v1")!
```

例如：

```swift
private let baseURL = URL(string: "http://192.168.1.10:8000/api/v1")!
```

同时确认：

- iPhone 和 Mac 在同一个 Wi-Fi。
- FastAPI 使用 `--host 0.0.0.0` 启动。
- macOS 防火墙允许 Python 或终端接收连接。
- 路由器没有开启客户端隔离。

### 4.3 使用远程服务器后端

如果你把后端部署到云服务器，建议配置 HTTPS 域名，例如：

```text
https://api.your-domain.com/api/v1
```

然后在 `APIClient.swift` 中改为：

```swift
private let baseURL = URL(string: "https://api.your-domain.com/api/v1")!
```

远程服务器建议使用 HTTPS。这样可以避免 iOS App Transport Security 对 HTTP 的限制，也更适合将来上架。

---

## 5. 在 Xcode 中新建 SwiftUI iOS 工程

因为当前 iOS 目录还只是源码骨架，没有完整 `.xcodeproj`，所以需要创建 Xcode 工程。

### 5.1 新建工程

1. 打开 Xcode。
2. 选择 File → New → Project。
3. 在 iOS 分类下选择 App。
4. 点击 Next。
5. 填写：

```text
Product Name: ResearchIntelApp
Team: 选择你的 Apple ID 或开发者团队
Organization Identifier: com.yourname 或 com.yourcompany
Bundle Identifier: Xcode 会自动生成，例如 com.yourname.ResearchIntelApp
Interface: SwiftUI
Language: Swift
Storage: None
Include Tests: 可以先不勾选
```

6. 点击 Next。
7. 选择保存位置。

推荐保存方式：

- 如果你不熟悉 Xcode，建议先保存到 Mac 本地一个新目录，例如：

```text
~/Projects/ResearchIntelApp-Xcode
```

然后再把当前项目中的 Swift 文件导入进去。

进阶方式：

- 也可以把工程建在当前仓库的 `ios/ResearchIntelApp` 目录下，但要小心不要覆盖已有源码。

### 5.2 设置最低 iOS 版本

创建工程后：

1. 点击左侧项目根节点。
2. 选择 Targets → ResearchIntelApp。
3. 找到 General。
4. 将 Minimum Deployments 设置为 iOS 17.0 或更高。

---

## 6. 将现有 SwiftUI 源码加入 Xcode 工程

当前源码在：

```text
/path/to/research-intelligence-ios/ios/ResearchIntelApp/ResearchIntelApp
```

其中包含：

```text
Models/
Services/
Views/
ResearchIntelApp.swift
```

### 6.1 避免两个 App 入口文件

Xcode 新建项目时会自动生成一个 App 入口文件，可能叫：

```text
ResearchIntelAppApp.swift
```

当前项目也有一个入口文件：

```text
ResearchIntelApp.swift
```

这两个文件里通常都会有 `@main`。一个 iOS App 只能有一个 `@main` 入口。如果两个都存在，构建会报错。

你有两种选择。

#### 方案 A：使用当前项目自带的 `ResearchIntelApp.swift`

推荐新手使用这个方案。

步骤：

1. 在 Xcode 中删除新项目自动生成的 App 入口文件，例如 `ResearchIntelAppApp.swift`。
2. 删除自动生成的 `ContentView.swift`。
3. 把当前项目的 `ResearchIntelApp.swift`、`Models`、`Services`、`Views` 拖入 Xcode 项目。
4. 拖入时勾选：
   - Copy items if needed。
   - Create groups。
   - Add to targets: ResearchIntelApp。

#### 方案 B：保留 Xcode 自动生成的 App 入口文件

如果你保留 Xcode 自动生成的入口文件，就不要导入当前项目的 `ResearchIntelApp.swift`。

然后把自动生成入口文件中的内容改成：

```swift
import SwiftUI

@main
struct ResearchIntelAppApp: App {
    var body: some Scene {
        WindowGroup {
            RootTabView()
        }
    }
}
```

再导入：

```text
Models/
Services/
Views/
```

不要导入：

```text
ResearchIntelApp.swift
```

### 6.2 检查 Target Membership

导入后，点击每个 Swift 文件，打开右侧 File Inspector，确认 Target Membership 中勾选了你的 App target。

如果没有勾选，会出现类似错误：

```text
Cannot find type 'Article' in scope
Cannot find 'RootTabView' in scope
```

解决方式：

1. 选中文件。
2. 右侧 File Inspector。
3. 勾选 ResearchIntelApp target。
4. 重新构建。

---

## 7. 配置 Bundle Identifier 和签名

### 7.1 Bundle Identifier

在 Xcode 中：

1. 点击项目根节点。
2. 选择 Targets → ResearchIntelApp。
3. 进入 Signing & Capabilities。
4. Bundle Identifier 设置为全局唯一值，例如：

```text
com.yourname.ResearchIntelApp
```

如果提示重复，就换一个，例如：

```text
com.yourname.researchintel.dev
```

### 7.2 Signing

模拟器：

- 通常 Xcode 自动处理即可。

真机：

1. 在 Signing & Capabilities 中勾选 Automatically manage signing。
2. Team 选择你的 Apple ID 或开发者团队。
3. 连接 iPhone。
4. 在顶部运行设备中选择你的 iPhone。
5. 如果提示需要信任证书，按 Xcode 或 iPhone 上的提示操作。

如果是真机第一次运行，还需要：

1. iPhone 打开 Settings。
2. 进入 Privacy & Security。
3. 打开 Developer Mode。
4. 重启 iPhone。
5. 重新连接 Mac。

如果使用免费 Apple ID，安装到真机后可能还要到：

```text
Settings → General → VPN & Device Management
```

信任你的开发者证书。

---

## 8. 配置网络访问权限和 ATS

### 8.1 为什么需要配置 ATS

iOS 默认更推荐 HTTPS。如果 App 访问 HTTP 地址，例如：

```text
http://127.0.0.1:8000/api/v1
http://192.168.1.10:8000/api/v1
```

可能会遇到 App Transport Security 限制。

常见报错：

```text
App Transport Security has blocked a cleartext HTTP resource load
```

开发阶段可以临时放开 HTTP，正式上线建议使用 HTTPS。

### 8.2 在 Xcode 里添加 ATS 配置

如果项目没有单独显示 `Info.plist` 文件，可以在 Xcode Target 的 Info 页面添加。

路径：

1. 点击项目根节点。
2. 选择 Targets → ResearchIntelApp。
3. 进入 Info。
4. 在 Custom iOS Target Properties 中添加：

```text
App Transport Security Settings
```

类型选择 Dictionary。

在这个 Dictionary 下添加：

```text
Allow Local Networking = YES
```

如果本地局域网 IP 访问仍然被拦截，开发阶段可以临时添加：

```text
Allow Arbitrary Loads = YES
```

注意：`Allow Arbitrary Loads = YES` 只建议开发测试使用。正式上线建议删除，并改为 HTTPS 后端。

### 8.3 iOS 本地网络权限说明

如果真机访问局域网 IP，iOS 可能触发本地网络权限要求。可以在 Info 中添加：

```text
Privacy - Local Network Usage Description
```

值填写：

```text
用于在开发测试时连接同一局域网内的科研情报后端服务。
```

---

## 9. 配置后端 API 地址

当前 API 地址写在：

```text
ios/ResearchIntelApp/ResearchIntelApp/Services/APIClient.swift
```

默认：

```swift
private let baseURL = URL(string: "http://127.0.0.1:8000/api/v1")!
```

### 9.1 模拟器连接本机后端

如果后端运行在同一台 Mac：

```swift
private let baseURL = URL(string: "http://127.0.0.1:8000/api/v1")!
```

### 9.2 真机连接 Mac 后端

例如 Mac IP 是 `192.168.1.10`：

```swift
private let baseURL = URL(string: "http://192.168.1.10:8000/api/v1")!
```

FastAPI 启动命令必须是：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 9.3 连接远程后端

推荐使用 HTTPS：

```swift
private let baseURL = URL(string: "https://api.your-domain.com/api/v1")!
```

### 9.4 后续更好的做法

当前为了简单，API 地址直接写在 Swift 文件中。后续可以改成：

- Debug 使用本地地址。
- Release 使用正式服务器地址。
- 用 `.xcconfig` 管理不同环境。
- 用 Info.plist 或 Build Settings 注入 API Base URL。

---

## 10. 在 iOS 模拟器运行

### 10.1 启动后端

先启动 FastAPI：

```bash
cd /path/to/research-intelligence-ios/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

浏览器确认：

```text
http://127.0.0.1:8000/api/v1/briefings/today
```

可以访问。

### 10.2 选择模拟器

在 Xcode 顶部设备选择器中选择一个 iOS 17+ 模拟器，例如：

```text
iPhone 15 / iPhone 16 / 任意 iOS 17+ 模拟器
```

### 10.3 运行

点击 Xcode 左上角 Run 按钮，或按：

```text
Command + R
```

成功后，模拟器中会打开 App。

你应该看到底部 Tab：

```text
今日 / 主题 / 搜索 / 收藏 / 我的
```

如果今日页显示加载失败，优先检查：

- 后端是否启动。
- `APIClient.swift` 地址是否正确。
- 浏览器是否能打开 `/api/v1/briefings/today`。
- Xcode 控制台是否有 ATS 或网络错误。

---

## 11. 在 iPhone 真机运行

### 11.1 准备 iPhone

1. 用数据线连接 iPhone 和 Mac，或使用 Xcode 支持的无线调试。
2. iPhone 上信任这台 Mac。
3. iOS 16 及以上打开 Developer Mode：
   - Settings → Privacy & Security → Developer Mode。
   - 开启后按提示重启。
4. Xcode 顶部设备选择器选择你的 iPhone。

### 11.2 配置签名

在 Xcode：

1. Targets → ResearchIntelApp。
2. Signing & Capabilities。
3. Team 选择你的 Apple ID。
4. 勾选 Automatically manage signing。
5. Bundle Identifier 改成唯一值。

### 11.3 配置 API 地址

把 `APIClient.swift` 改成 Mac 的局域网 IP：

```swift
private let baseURL = URL(string: "http://192.168.1.10:8000/api/v1")!
```

不要用：

```swift
private let baseURL = URL(string: "http://127.0.0.1:8000/api/v1")!
```

因为在真机上，`127.0.0.1` 是手机自己。

### 11.4 启动后端

Mac 上启动：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

在 iPhone Safari 中访问：

```text
http://192.168.1.10:8000/api/v1/briefings/today
```

如果 Safari 都打不开，App 也打不开。先排查局域网、Mac 防火墙和后端监听地址。

### 11.5 运行到真机

点击 Xcode Run，或按 Command + R。

如果提示无法安装或无法验证开发者：

1. iPhone 打开 Settings。
2. General → VPN & Device Management。
3. 信任你的开发者证书。
4. 回到 Xcode 再运行。

---

## 12. App 当前功能如何使用

### 12.1 今日简报

入口：底部 Tab → 今日。

当前行为：

- App 调用后端 `/api/v1/briefings/today`。
- 页面展示今日重点和全部内容。
- 当前后端返回的是示例文章数据，后续接入真实每日流水线后会显示真实抓取结果。

你可以点击任意文章进入详情页。

### 12.2 详情页

入口：今日简报列表 → 点击文章。

详情页展示：

- 中文标题或英文标题。
- 来源，例如 PubMed、arXiv。
- 中文精炼摘要。
- 原始摘要。
- 打开原文链接。

当前原文链接会跳转到系统浏览器或内置 Link 行为。

### 12.3 主题切换

入口：底部 Tab → 主题。

当前行为：

- App 调用后端 `/api/v1/topics`。
- 显示神经科学、生物材料、AI、骨科四个主题。
- 每个主题有 Toggle 开关。

当前限制：

- Toggle 状态只在当前页面内存中变化。
- 还没有持久化到账号或本地存储。
- 还没有联动今日简报过滤。

后续应实现：

- 把用户订阅主题保存到本地或后端。
- 今日简报根据选中的主题请求不同数据。
- 支持自定义主题关键词。

### 12.4 搜索

入口：底部 Tab → 搜索。

当前行为：

- 当前是 UI 占位页面。
- 顶部有搜索框。
- 还没有真正调用后端搜索接口。

后端目前已经有 `/api/v1/articles?q=关键词` 的初步接口骨架，后续需要在 SwiftUI 中接入。

### 12.5 收藏

入口：底部 Tab → 收藏。

当前行为：

- 当前是 UI 占位页面。
- 还没有收藏按钮、收藏列表持久化和后端收藏接口。

后续应实现：

- 在详情页增加收藏按钮。
- 用本地 SwiftData、UserDefaults 或后端 API 保存收藏状态。
- 收藏页读取收藏文章。

### 12.6 已读

当前状态：

- 还没有实现已读标记。
- 点击详情页后不会保存已读状态。

后续应实现：

- 打开详情页时记录已读。
- 列表中显示已读样式。
- 支持隐藏已读或仅看未读。

### 12.7 我的 / 推送设置

入口：底部 Tab → 我的。

当前行为：

- 可以点击请求通知权限。
- iOS 会弹出通知授权窗口。

当前限制：

- 目前只请求本地通知权限。
- 还没有接入 APNs 设备 token 注册。
- 还没有后端每日推送任务。

后续实现 APNs 时，需要：

- Xcode 开启 Push Notifications capability。
- Apple Developer 后台配置 App ID 和 APNs。
- App 获取 device token 并上传后端。
- 后端使用 APNs key 给指定 device token 推送。

---

## 13. 常见问题排查

### 13.1 App 显示“加载失败”或无法连接后端

优先检查：

1. 后端是否启动。
2. 浏览器能否打开 `/health`。
3. 浏览器能否打开 `/api/v1/briefings/today`。
4. `APIClient.swift` 中的 baseURL 是否正确。
5. 模拟器和真机是否使用了正确地址。
6. Xcode 控制台是否出现 ATS 错误。

模拟器：

- 后端在同一台 Mac 上，通常用 `127.0.0.1`。

真机：

- 不能用 `127.0.0.1`。
- 要用 Mac 局域网 IP。
- 后端要用 `--host 0.0.0.0` 启动。
- iPhone 和 Mac 要在同一个 Wi-Fi。

### 13.2 真机 Safari 也打不开后端地址

如果 iPhone Safari 打不开：

```text
http://Mac局域网IP:8000/api/v1/briefings/today
```

说明不是 App 问题，而是网络问题。

检查：

- Mac 和 iPhone 是否同一 Wi-Fi。
- Mac 防火墙是否拦截 Python 或终端。
- FastAPI 是否监听 `0.0.0.0`。
- 路由器是否开启 AP Isolation 或客户端隔离。
- IP 地址是否写错。

### 13.3 ATS 网络限制

错误类似：

```text
App Transport Security has blocked a cleartext HTTP resource load
```

解决方式：

开发阶段：

- 在 Target → Info 中添加 App Transport Security Settings。
- 设置 Allow Local Networking = YES。
- 必要时临时设置 Allow Arbitrary Loads = YES。

正式环境：

- 使用 HTTPS 后端。
- 删除 Allow Arbitrary Loads。

### 13.4 签名失败

常见错误：

```text
No profiles for 'com.xxx.ResearchIntelApp' were found
Signing for ResearchIntelApp requires a development team
```

解决方式：

1. Xcode 登录 Apple ID。
2. Targets → Signing & Capabilities。
3. Team 选择你的账号。
4. 勾选 Automatically manage signing。
5. Bundle Identifier 改成唯一值。
6. 清理构建后重试。

清理构建：

```text
Product → Clean Build Folder
```

快捷键：

```text
Shift + Command + K
```

### 13.5 真机提示无法验证开发者

解决方式：

1. iPhone 打开 Settings。
2. General → VPN & Device Management。
3. 找到你的 Apple ID 开发者证书。
4. 点击 Trust。
5. 回到 App 或 Xcode 重新运行。

### 13.6 构建失败：有两个 `@main`

错误可能类似：

```text
'main' attribute can only apply to one type in a module
```

原因：

- Xcode 自动生成的 App 入口文件和当前项目的 `ResearchIntelApp.swift` 都包含 `@main`。

解决方式：

二选一：

- 删除 Xcode 自动生成的 App 入口文件，保留当前项目的 `ResearchIntelApp.swift`。
- 或保留 Xcode 自动生成的 App 入口文件，不导入当前项目的 `ResearchIntelApp.swift`，并把入口页面改成 `RootTabView()`。

### 13.7 构建失败：找不到 `RootTabView`、`Article`、`Topic`

错误可能类似：

```text
Cannot find 'RootTabView' in scope
Cannot find type 'Article' in scope
Cannot find type 'Topic' in scope
```

原因：

- 文件没有加入 target。
- 文件没有导入工程。
- 文件路径是红色的，Xcode 找不到文件。

解决方式：

1. 选中对应 Swift 文件。
2. 打开右侧 File Inspector。
3. 勾选 Target Membership。
4. 如果文件是红色，删除引用后重新 Add Files。
5. Product → Clean Build Folder。

### 13.8 构建失败：`ContentUnavailableView` 不可用

错误可能类似：

```text
'ContentUnavailableView' is only available in iOS 17.0 or newer
```

解决方式：

- 把 Deployment Target 设置为 iOS 17.0 或更高。
- 或将 `ContentUnavailableView` 替换成普通 `VStack`、`Image`、`Text`。

### 13.9 构建失败：`URL.appending(path:)` 不可用

原因：

- Xcode 或 iOS SDK 太旧。

解决方式：

- 升级 Xcode。
- 或把 URL 拼接改成兼容写法，例如使用 `URLComponents`。

### 13.10 JSON 解码失败

错误可能显示：

```text
The data couldn’t be read because it isn’t in the correct format
```

排查：

1. 浏览器打开 `/api/v1/briefings/today`，确认返回是 JSON。
2. 确认后端没有报 500。
3. 确认 Swift 模型字段和后端 JSON 字段对应。
4. 如果是日期字段解析失败，可以临时把 `publishedAt` 改成 `String?`，或给 `JSONDecoder` 增加兼容 fractional seconds 的日期解析策略。

### 13.11 iOS 模拟器访问 localhost 的误区

对 iOS 模拟器：

- 如果后端运行在同一台 Mac，`127.0.0.1` 通常可以访问 Mac 本机服务。

对 iPhone 真机：

- `127.0.0.1` 是 iPhone 自己，不能访问 Mac。

如果后端运行在另一台机器、Docker、WSL 或云服务器：

- 不要使用模拟器或真机自己的 `127.0.0.1`。
- 使用后端所在机器的可访问 IP 或域名。

### 13.12 Xcode 文件变红

原因：

- Xcode 工程引用的文件路径失效。
- 文件被移动或删除。

解决方式：

1. 在 Xcode 中删除红色引用，选择 Remove Reference，不要 Move to Trash。
2. 重新 Add Files。
3. 勾选 Copy items if needed 和 Target Membership。

---

## 14. 推荐的首次运行顺序

新手建议按这个顺序：

1. 在 Mac 上安装 Xcode。
2. 把 `research-intelligence-ios` 项目复制到 Mac 本地。
3. 启动后端：`uvicorn app.main:app --host 0.0.0.0 --port 8000`。
4. 浏览器验证 `/health`、`/api/v1/topics`、`/api/v1/briefings/today`。
5. 在 Xcode 新建 SwiftUI iOS App 工程。
6. 设置 Deployment Target 为 iOS 17.0。
7. 删除 Xcode 自动生成的入口文件和 `ContentView.swift`。
8. 导入当前项目的 `ResearchIntelApp.swift`、`Models`、`Services`、`Views`。
9. 确认 Target Membership。
10. 如果用模拟器，保持 `APIClient.swift` 的 `127.0.0.1`。
11. 如果用真机，把 `APIClient.swift` 改成 Mac 局域网 IP。
12. 配置 Signing & Capabilities。
13. 配置 ATS 开发例外。
14. 选择模拟器或真机，点击 Run。
15. 打开 App 的今日页和主题页确认数据加载。

---

## 15. 当前骨架到可用产品还缺什么

当前已经能搭起最小端到端雏形，但距离完整产品还需要补充：

- 创建正式 `.xcodeproj` 并纳入仓库。
- 实现搜索页调用后端 `/articles?q=`。
- 实现收藏按钮、收藏页和持久化。
- 实现已读状态。
- 实现主题选择与今日简报联动。
- 接入真实数据库，不再只用示例数据。
- 完善 PubMed 的 efetch 元数据抓取。
- 接入真实 LLM 摘要。
- 接入 APNs 推送和设备 token 注册。
- 部署 HTTPS 后端。
- 增加错误提示、加载重试和离线缓存。

---

## 16. 快速判断问题在哪一层

如果 App 不能正常显示，按这个顺序判断：

1. 后端层：浏览器能否访问接口。
2. 网络层：模拟器或真机能否访问接口。
3. ATS 层：Xcode 控制台是否有 HTTP 被拦截。
4. 数据层：接口 JSON 是否符合 Swift 模型。
5. 工程层：Swift 文件是否加入 target。
6. 签名层：真机是否有有效开发者证书。

只要逐层排查，通常能快速定位问题。
