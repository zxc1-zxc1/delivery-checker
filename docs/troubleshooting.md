# 排障手册

本文用于定位配置、巡检、存储、报告和测试中的常见问题。

排查时先确认错误属于哪一层，不要一开始就修改所有文件。

## 通用排查顺序

1. 确认当前目录；
2. 检查配置文件；
3. 查看具体失败项和错误类型；
4. 查看退出码；
5. 查看日志；
6. 必要时运行静态检查和测试。

常用命令：

```powershell
Get-Location
py -c "from delivery_checker.config import load_config; load_config(); print('配置校验通过')"
delivery-checker
$LASTEXITCODE
```

日志默认位于：

```text
logs/delivery_checker.log
```

## 找不到配置文件

典型提示：

```text
配置错误：配置文件不存在：config.json
```

原因通常是当前终端不在项目根目录。

检查：

```powershell
Get-Location
Get-ChildItem "config.json"
```

正确目录应类似：

```text
D:\code\delivery-checker
```

如果配置被误删，可以参考 `config.example.json` 重新创建，但不要覆盖其他正常配置。

## JSON 格式错误

典型提示：

```text
配置文件不是有效的 JSON
```

重点检查：

- 是否使用英文双引号；
- 字段之间是否有逗号；
- 最后一项后面是否多了逗号；
- 是否写入了 JSON 不支持的注释；
- 大括号和中括号是否成对。

错误示例：

```json
{
  "ports": [],
}
```

正确示例：

```json
{
  "ports": []
}
```

只校验配置，不执行网络检查：

```powershell
py -c "from delivery_checker.config import load_config; load_config(); print('配置校验通过')"
```

## 配置字段校验失败

常见情况：

| 字段 | 正确形式 |
| --- | --- |
| `port` | 1—65535 的整数 |
| `timeout` | 大于 0 的数字 |
| `max_attempts` | 大于或等于 1 的整数 |
| `retry_delay` | 大于或等于 0 的数字 |
| `url` | 包含 `http://` 或 `https://` |
| `host` | 非空字符串 |
| `min_free_gb` | 大于或等于 0 的数字 |

注意 `"port": "443"` 是字符串，不是整数，应改为：

```json
"port": 443
```

## 程序返回退出码 1

退出码 `1` 表示程序已经完成巡检，但至少一项失败，不等于程序自身崩溃。

查看输出中的：

- `item`：哪类检查失败；
- `target`：哪个目标失败；
- `error_type`：失败类别；
- `attempts`：尝试了几次；
- `duration_ms`：总耗时。

仓库演示配置故意包含异常端口，因此演示时返回 `1` 是预期现象。

## 程序返回退出码 2

退出码 `2` 表示配置或运行错误。

先执行配置校验：

```powershell
py -c "from delivery_checker.config import load_config; load_config(); print('配置校验通过')"
```

再查看终端错误和日志，不要在配置错误未解决时反复运行网络巡检。

## TCP 检查失败

常见错误类型：

- `timeout`：等待连接超时；
- `connection`：连接被拒绝或出现其他连接错误。

PowerShell 可进一步检查：

```powershell
Test-NetConnection "目标主机" -Port 目标端口
```

例如：

```powershell
Test-NetConnection "127.0.0.1" -Port 3306
```

排查方向：

1. 主机名或 IP 是否正确；
2. 端口是否正确；
3. 目标服务是否启动；
4. 本机或目标防火墙是否限制访问；
5. 路由、VPN 或代理是否影响连接。

TCP 连接成功不代表上层业务一定正常。

## HTTP 检查失败

`error_type=http_status` 表示请求到达了 HTTP 服务，但状态码不是当前程序要求的 200。

检查：

- URL 是否包含协议；
- 是否访问了正确路径；
- 服务是否要求登录或额外请求头；
- 是否发生重定向；
- 服务实际健康状态码是否为 200。

当前版本只把 HTTP 200 视为通过，不支持在配置中自定义期望状态码。

## MySQL 连接失败

先区分网络问题和认证问题。

### 网络连接问题

如果错误包含连接失败或 2003 等信息，检查：

```powershell
Test-NetConnection "127.0.0.1" -Port 3306
```

同时确认 MySQL 服务已启动，并允许来自当前机器的连接。

### 用户名或密码问题

如果错误包含访问被拒绝或 1045 等信息，检查：

- 用户名是否正确；
- 密码环境变量是否已在当前终端设置；
- `password_env` 是否填写了变量名称，而不是密码本身；
- 账号是否有从当前主机连接的权限。

PowerShell 设置方式：

```powershell
$env:DELIVERY_CHECKER_MYSQL_PASSWORD = "实际密码"
```

检查变量是否存在时，不要直接输出密码。可执行：

```powershell
Test-Path Env:DELIVERY_CHECKER_MYSQL_PASSWORD
```

返回 `True` 只表示变量存在，不表示密码一定正确。

使用结束后清除：

```powershell
Remove-Item Env:DELIVERY_CHECKER_MYSQL_PASSWORD
```

## SQLite 保存或查询失败

默认数据库：

```text
data/inspections.db
```

排查：

1. 当前账号是否能写入项目目录；
2. `data` 目录是否可创建；
3. 数据库是否被其他工具锁定；
4. 磁盘空间是否充足；
5. 是否误把数据库文件替换成了目录。

旧表升级只负责补充 `duration_ms`、`attempts` 和 `error_type` 三列。操作重要数据前仍应先备份数据库。

本地演示数据库不提交到 GitHub。

## CSV 报告问题

默认目录：

```text
reports
```

找不到报告时，先确认程序是否完整执行到导出阶段，并检查终端是否出现其他错误。

CSV 使用 `utf-8-sig` 编码。如果通过 PowerShell 查看中文乱码，可指定：

```powershell
Get-Content "报告文件路径.csv" -Encoding UTF8
```

报告字段应包括：

```text
item,target,status,message,checked_at,duration_ms,attempts,error_type
```

## PowerShell 显示中文乱码

UTF-8 文档如果使用默认 `Get-Content` 显示乱码，可执行：

```powershell
Get-Content "docs\configuration.md" -Encoding UTF8
```

如果指定 UTF-8 后中文正常，说明文件没有损坏，只是读取编码不同，不要重写文件。

## 找不到 `delivery_checker` 包

典型错误：

```text
ModuleNotFoundError: No module named 'delivery_checker'
```

标准解决方式是在项目根目录重新安装：

```powershell
py -m pip install -e ".[dev]"
```

然后验证：

```powershell
py -c "import delivery_checker; print(delivery_checker.__file__)"
```

正常情况下不再需要手动设置 `PYTHONPATH`。

## 找不到 `delivery-checker` 命令

先确认项目已安装：

```powershell
py -m pip show delivery-checker
```

如果原入口能够运行，可以暂时使用：

```powershell
py main.py
```

再检查命令位置：

```powershell
Get-Command delivery-checker
```

如果项目已经安装但命令仍无法识别，通常是 Python 的 `Scripts` 目录未加入 PATH。修改 PATH 前先记录当前值，不要随意覆盖系统环境变量。

## 测试或静态检查失败

安装开发依赖：

```powershell
py -m pip install -e ".[dev]"
```

分别运行：

```powershell
py -m ruff check .
py -m mypy src main.py
py -m pytest
```

Ruff 只负责其配置的规范和错误规则；MyPy 负责类型检查；pytest 负责行为测试。三者不能相互替代。

修改代码后如果只有测试失败，应先阅读失败断言和 traceback，不要通过删除测试来获得绿色结果。

## GitHub Actions 失败

先在本地执行与 CI 相同的三条命令：

```powershell
py -m ruff check .
py -m mypy src main.py
py -m pytest
```

如果本地通过而云端失败，再检查：

- 是否漏提交文件；
- 依赖是否已写入 `pyproject.toml`；
- 测试是否依赖本机路径或外部网站；
- 是否只在某个 Python 版本失败；
- CI 日志中具体失败的是哪一个步骤。

## 敏感信息误提交

如果真实密码或 Token 已经进入 Git 或 GitHub：

1. 立即使凭据失效并重新生成；
2. 再清理仓库中的敏感内容；
3. 检查日志和提交历史；
4. 不要只删除当前文件就认为风险已经解除。

本地数据库、巡检报告和日志不应提交到公开仓库。