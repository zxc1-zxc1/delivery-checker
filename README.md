# Delivery Checker

面向软件交付与实施现场的巡检、诊断和报告命令行工具。

项目从单文件脚本逐步重构为标准的 `src` 目录 Python 包，支持磁盘、TCP、HTTP 和 MySQL 健康检查，并将结果统一保存到 SQLite 和 CSV。

&gt; 当前版本为 `2.0.0.dev1`，属于 V2 开发版本。项目具备自动化测试、静态检查和持续集成，但尚未经过真实生产负载、安全评审和长期运行验证，不宣称是已经验证过的企业生产级系统。

## 主要功能

- 磁盘剩余空间与阈值检查；
- TCP 主机和端口连接检查；
- HTTP/HTTPS 状态检查；
- MySQL 连接及 `SELECT 1` 查询检查；
- TCP、HTTP 和 MySQL 网络任务并发执行；
- 连接错误和超时可配置重试；
- 统一记录错误类型、尝试次数和耗时；
- JSON 配置读取与字段校验；
- SQLite 历史记录及旧表结构自动升级；
- CSV 巡检报告导出；
- 终端与文件双日志；
- 通过退出码区分巡检失败和运行错误；
- Ruff、MyPy、pytest 和 GitHub Actions 自动检查。

## 项目结构

```text
delivery-checker/
├── main.py                     # 原运行方式的兼容入口
├── config.json                 # 本地正式配置
├── config.example.json         # 不含敏感信息的配置示例
├── pyproject.toml              # 打包、依赖和工具配置
├── src/
│   └── delivery_checker/
│       ├── cli.py              # 命令行入口和结果展示
│       ├── models.py           # 统一结果模型和枚举
│       ├── checkers.py         # 各类具体检查
│       ├── config.py           # 配置读取与校验
│       ├── runner.py           # 并发调度、耗时和重试
│       ├── storage.py          # SQLite 保存、查询和表升级
│       ├── reporting.py        # CSV 报告
│       └── logging_config.py   # 日志配置
├── tests/                      # 自动化测试
├── docs/                       # 设计和使用文档
├── data/                       # 本地数据库，不上传 Git
├── reports/                    # 本地报告，不上传 Git
└── logs/                       # 本地日志，不上传 Git