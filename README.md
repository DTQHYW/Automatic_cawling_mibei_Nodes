# 🚀 Automatic_cawling_mibei_Nodes

米贝最新节点全自动收割机。

通过 GitHub Actions 每日自动抓取公开节点订阅，统一整理为 **Base64 通用订阅** 与 **Clash YAML 订阅** 两种格式，方便 V2RayN、v2rayNG、Shadowrocket（小火箭）以及 Clash 系列客户端导入。

---

## ✨ 功能特性

- ⏰ **定时收割**：每天北京时间 0 点自动运行
- 🌐 **多源聚合**：支持 Base64 订阅、Clash YAML、原始 URI 文本
- 🧠 **协议解析**：支持 vmess / vless / ss / trojan
- 🔄 **自动去重**：基于协议、地址、端口、凭证去重
- 📝 **统一命名**：自动整理为统一的展示名称
-  **双格式输出**：`base64.txt` + `clash.yaml`
- 🤖 **GitHub Actions**：无需服务器，Actions 自动托管
- 📣 **可选通知**：支持邮件、Telegram、微信 Webhook

---

## 📂 项目结构

```
.
├── .github/workflows/harvest.yml   # GitHub Actions 工作流
├── src/                            # 核心模块
│   ├── parser.py                   # 节点抓取与解析
│   ├── converter.py                # 订阅格式转换
│   ├── notifier.py                 # 通知模块
│   └── utils.py                    # 工具函数
├── subscriptions/                  # 生成的订阅文件
│   ├── base64.txt                  # Base64 通用订阅
│   └── clash.yaml                  # Clash YAML 订阅
├── config.yaml                     # 配置文件
├── main.py                         # 单次收割入口
├── daemon.py                       # 本地守护进程入口
├── requirements.txt                # Python 依赖
└── README.md                       # 本文件
```

---

## 🛠️ 本地运行

### 1. 克隆仓库

```bash
git clone https://github.com/7huukdlnkjkjba/Automatic_cawling_mibei_Nodes.git
cd Automatic_cawling_mibei_Nodes
```

### 2. 安装依赖

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 3. 配置订阅源

编辑 `config.yaml`，在 `sources` 中填写你实际要抓取的订阅源：

```yaml
sources:
  - name: "mibei-base64"
    url: "https://example.com/mibei/subscribe/base64"
    type: "base64"
    enabled: true

  - name: "mibei-clash"
    url: "https://example.com/mibei/subscribe/clash"
    type: "clash"
    enabled: true
```

> ⚠️ 仓库默认填写的公共订阅源仅作为示例，请替换为你要收割的真实订阅源。

### 4. 运行收割

```bash
# 单次运行
python main.py

# 本地守护进程模式（按 config.yaml 中的 check_interval 定时运行）
python daemon.py
```

运行后会在 `subscriptions/` 目录下生成 `base64.txt` 和 `clash.yaml`。

---

## 📡 订阅链接

如果你通过 GitHub Actions 运行并启用 Pages，可直接通过以下地址访问（将 `用户名` 和 `仓库名` 替换为你自己的）：

| 格式 | 文件路径 |
|------|---------|
| Base64 通用订阅 | `https://用户名.github.io/仓库名/subscriptions/base64.txt` |
| Clash YAML 订阅 | `https://用户名.github.io/仓库名/subscriptions/clash.yaml` |

当然，也可以直接通过 GitHub Raw 地址获取：

```
https://raw.githubusercontent.com/用户名/仓库名/main/subscriptions/base64.txt
https://raw.githubusercontent.com/用户名/仓库名/main/subscriptions/clash.yaml
```

---

## 🧩 客户端导入

### V2RayN / v2rayNG / Shadowrocket（小火箭）

使用 `subscriptions/base64.txt` 对应的订阅链接：

1. 打开客户端订阅管理
2. 粘贴 Base64 订阅链接
3. 点击更新订阅
4. 从服务器列表选择节点

### Clash / Mihomo / Clash Verge / ClashX

使用 `subscriptions/clash.yaml` 对应的订阅链接：

1. 打开客户端的 Profiles / 配置订阅
2. 粘贴 Clash YAML 订阅链接
3. 下载并选择该配置文件

---

## ⚙️ 配置说明

```yaml
settings:
  check_interval: 3600       # 守护进程检查间隔（秒）
  timeout: 30                # HTTP 请求超时（秒）
  max_retries: 3             # 失败重试次数
  output_dir: "subscriptions"
  logs_dir: "logs"

sources:
  - name: "mibei-base64"
    url: "..."
    type: "base64"           # 可选：base64 | clash | raw_text
    enabled: true

output:
  base64: "subscriptions/base64.txt"
  clash: "subscriptions/clash.yaml"

filter:
  deduplicate: true          # 是否去重
  name_suffix: "udptoos.com" # 节点名称后缀

notification:
  email:
    enabled: false
    smtp_server: "smtp.example.com"
    smtp_port: 587
    username: ""
    password: ""
    sender: "your@email.com"
    recipient: "your@email.com"
  telegram:
    enabled: false
    bot_token: ""
    chat_id: ""
  wechat:
    enabled: false
    webhook_url: ""
```

---

## 🤖 GitHub Actions 配置

项目已包含 `.github/workflows/harvest.yml`：

- **触发方式**：
  - 每日 UTC 16:00（北京时间 0 点）自动执行
  - 支持手动触发 `workflow_dispatch`
- **执行流程**：
  1. 检出仓库
  2. 安装 Python 依赖
  3. 执行 `python main.py`
  4. 如果 `subscriptions/` 目录有变更，自动提交并推送

首次使用前，请确保仓库已开启 **Actions 写入权限**（Settings → Actions → General → Workflow permissions → Read and write permissions）。

---

## ⚠️ 免责声明

本项目仅用于技术研究和学习交流，不销售任何代理服务，也不对节点的可用性、速度、安全性做任何承诺。

使用公开节点时，请遵守所在地法律法规，请勿将公共节点用于账号登录、支付或其他敏感操作。

---

## 📄 许可证

MIT License
