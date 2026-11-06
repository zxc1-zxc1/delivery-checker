# V2 设计说明

当前版本：`2.0.0.dev1`

## 设计目标

Delivery Checker 面向软件交付与实施现场，用于执行基础健康检查、保存诊断信息并生成可追溯报告。

V2 的重点不是增加复杂界面，而是将 V1 单文件脚本改造为职责清晰、可测试、可安装和可持续集成的命令行项目。

## 当前范围

已实现：

- 磁盘检查；
- TCP 连接检查；
- HTTP 状态检查；
- MySQL 连接和简单查询检查；
- 配置校验；
- 并发网络巡检；
- 可配置重试；
- 统一结果模型；
- SQLite 历史记录和旧表升级；
- CSV 报告；
- 终端与文件日志；
- 标准打包和命令行入口；
- 自动化测试、静态检查和 GitHub Actions。

不包含复杂账号权限、Web 管理后台和生产监控大盘。

## 模块职责

```text
cli.py              命令行入口、流程串联和终端展示
config.py           配置读取与字段校验
models.py           状态、错误类型和统一结果对象
checkers.py         磁盘、TCP、HTTP、MySQL 具体检查
runner.py           重试、耗时、并发调度和单项异常隔离
storage.py          SQLite 建表、升级、保存和历史查询
reporting.py        CSV 报告导出
logging_config.py   终端与文件日志配置
```

`main.py` 只保留兼容入口，实际命令行逻辑位于 `delivery_checker/cli.py`。

## 一次巡检的数据流

```text
读取 config.json
    ↓
校验配置结构和字段
    ↓
先执行磁盘检查
    ↓
构建 TCP、HTTP、MySQL 网络任务
    ↓
线程池并发执行，每项任务内部独立重试
    ↓
按原配置顺序收集统一结果
    ↓
终端展示并记录日志
    ↓
批量保存 SQLite
    ↓
导出 CSV
    ↓
根据结果返回退出码
```

配置错误返回 `2`，不会继续执行巡检。

## 统一结果模型

每项检查返回 `InspectionResult`，主要字段包括：

| 字段 | 含义 |
| --- | --- |
| `item` | 检查类型 |
| `target` | 检查目标 |
| `status` | `PASS` 或 `FAIL` |
| `message` | 面向使用者的结果说明 |
| `checked_at` | 带本地时区的 ISO 时间 |
| `duration_ms` | 整项检查总耗时 |
| `attempts` | 实际尝试次数 |
| `error_type` | 错误分类 |

`to_dict()` 负责将枚举转换为可保存和可导出的字符串。

## 错误分类

当前错误类型包括：

- `threshold`：磁盘空间低于阈值；
- `connection`：连接失败；
- `timeout`：连接或请求超时；
- `http_status`：HTTP 状态不符合要求；
- `configuration`：配置错误；
- `storage`：存储错误分类预留；
- `unexpected`：未预期异常。

`configuration` 主要用于配置处理；当前检查函数和调度器按各自边界返回相应结果。

## 重试设计

只有以下错误参与重试：

```text
timeout
connection
```

以下结果不盲目重试：

```text
PASS
threshold
http_status
unexpected
```

`max_attempts` 包含第一次执行，`retry_delay` 是两次尝试之间的等待秒数。

耗时从第一次尝试前开始统计，到最后一次尝试结束，因此包含重试等待时间。

## 并发设计

磁盘检查先顺序执行，网络任务统一进入 `ThreadPoolExecutor`。

选择线程池的原因是 TCP、HTTP 和 MySQL 检查主要等待网络 I/O，不是持续占用 CPU 的计算任务。

当前工作线程数：

```text
min(4, 网络任务数量)
```

结果顺序由任务列表和 Future 列表保持，不按照任务完成时间排序。

`_run_safely()` 是单项任务的异常边界。单项出现未预期异常时生成 `FAIL／unexpected` 结果，避免直接取消其他任务。

## MySQL 凭据设计

配置保存 `password_env`，其值是环境变量名称，不是真实密码。

调度器读取环境变量后将密码传给 PyMySQL，结果对象不保存密码字段，日志也不主动输出完整配置。

当前自动测试验证环境变量传参和模拟连接行为，不等同于真实 MySQL 现场验收。

## SQLite 设计

数据表主要字段：

```text
id
item
target
status
message
checked_at
duration_ms
attempts
error_type
```

保存时使用参数化 SQL 和 `executemany()`，统一提交事务，并在 `finally` 中关闭连接。

启动存储流程时通过 `PRAGMA table_info` 检查已有列。旧表缺少 V2 字段时使用 `ALTER TABLE` 补充：

- `duration_ms` 默认 0；
- `attempts` 默认 1；
- `error_type` 默认空字符串。

历史展示暂时保留原五列元组格式，以兼容旧入口；新增字段仍完整保存在数据库中。

## CSV 与日志

CSV 使用 `utf-8-sig`，包含统一结果的全部主要字段。

日志同时输出到终端和文件，记录事件、目标、状态、错误类型、尝试次数和耗时。

日志处理器已存在时不重复添加，避免同一事件被重复输出。

## 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 全部检查通过 |
| 1 | 巡检完成，但至少一项失败 |
| 2 | 配置或运行错误 |

巡检失败和程序运行错误必须区分，方便脚本或计划任务根据退出码处理。

## 测试策略

- 使用临时目录和临时数据库隔离存储测试；
- 使用 Mock 替代真实外部网络及 MySQL；
- 模拟 `time.sleep`，避免重试测试真实等待；
- 使用 `threading.Barrier` 验证网络任务确实能够并发；
- 使用旧表升级测试保护历史数据兼容性；
- 使用配置错误测试保护退出码行为。

质量检查命令：

```powershell
py -m ruff check .
py -m mypy src main.py
py -m pytest
```

GitHub Actions 在 Python 3.11 和 3.12 上执行相同检查。

## 安全与隐私

公开仓库不得包含：

- 真实客户名称和内部服务器地址；
- 数据库真实密码；
- Token 和其他凭据；
- 本地 SQLite 数据库；
- 本地巡检报告和日志；
- 真实业务或个人敏感数据。

凭据误提交后应立即吊销并重新生成，不能只删除当前文件。

## 当前限制

- 没有真实生产负载和长期运行验证；
- MySQL 自动化测试主要使用模拟对象；
- 并发线程数尚未开放为配置项；
- HTTP 当前只将状态码 200 视为通过；
- 命令行配置路径和输出目录尚未参数化；
- 尚未测量完整测试覆盖率百分比；
- 没有复杂账号权限和 Web 后台。

这些限制应在简历和面试中如实说明，不把学习项目包装成已经验证的生产系统。