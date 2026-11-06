# 配置手册

本文说明 `config.json` 的字段、默认值和校验规则。

程序从运行命令时所在的目录读取 `config.json`。开始修改前，建议先复制一份备份。

## 完整结构

配置由四个顶层字段组成：

```json
{
  "disk": {
    "path": ".",
    "min_free_gb": 10
  },
  "ports": [],
  "http_checks": [],
  "mysql_checks": []
}
```

- `disk`：磁盘检查；
- `ports`：TCP 检查数组；
- `http_checks`：HTTP 检查数组；
- `mysql_checks`：MySQL 检查数组。

数组为空表示不执行该类型检查。建议保留所有顶层字段，即使暂时不使用某个数组，也将其写成 `[]`。

JSON 不支持注释，最后一个字段后面不能多写逗号。

## 磁盘检查

示例：

```json
"disk": {
  "path": ".",
  "min_free_gb": 10
}
```

| 字段 | 是否必填 | 说明 |
| --- | --- | --- |
| `path` | 否 | 要检查的磁盘路径 |
| `min_free_gb` | 否 | 最小剩余空间，默认 10 GB |

Windows 示例：

```json
"disk": {
  "path": "D:/",
  "min_free_gb": 20
}
```

路径建议使用 `/`。`min_free_gb` 必须是大于或等于 0 的数字，不能写成 `"10"` 这样的字符串。

剩余空间低于阈值时：

- `status` 为 `FAIL`；
- `error_type` 为 `threshold`；
- 不进行无意义的重试。

## TCP 检查

示例：

```json
"ports": [
  {
    "host": "www.baidu.com",
    "port": 443,
    "timeout": 3,
    "max_attempts": 2,
    "retry_delay": 0.2
  }
]
```

| 字段 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `host` | 是 | 无 | 主机名或 IP 地址 |
| `port` | 是 | 无 | 1—65535 的整数端口 |
| `timeout` | 否 | 3 | 单次连接超时秒数 |
| `max_attempts` | 否 | 1 | 最大尝试次数 |
| `retry_delay` | 否 | 0.2 | 重试前等待秒数 |

`max_attempts` 包含第一次尝试。例如设置为 2，表示最多执行两次，不是首次执行后再额外重试两次。

TCP 检查只说明能否建立 TCP 连接，不代表上层应用的业务功能一定正常。

## HTTP 检查

示例：

```json
"http_checks": [
  {
    "url": "https://www.baidu.com",
    "timeout": 5,
    "max_attempts": 2,
    "retry_delay": 0.2
  }
]
```

| 字段 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `url` | 是 | 无 | 完整的 HTTP 或 HTTPS 地址 |
| `timeout` | 否 | 5 | 单次请求超时秒数 |
| `max_attempts` | 否 | 1 | 最大尝试次数 |
| `retry_delay` | 否 | 0.2 | 重试前等待秒数 |

URL 必须包含协议，例如：

```text
https://example.com/health
```

不能只写 `example.com`。

当前检查将 HTTP 200 视为通过。其他状态码会归为 `http_status`，不会因为增加重试次数就把确定性的状态码错误当成网络波动。

## MySQL 检查

示例：

```json
"mysql_checks": [
  {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "inspector",
    "database": "test",
    "password_env": "DELIVERY_CHECKER_MYSQL_PASSWORD",
    "timeout": 5,
    "max_attempts": 2,
    "retry_delay": 0.2
  }
]
```

| 字段 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `host` | 是 | 无 | MySQL 主机名或 IP |
| `port` | 否 | 3306 | MySQL 端口 |
| `user` | 是 | 无 | 数据库用户名 |
| `database` | 否 | null | 要连接的数据库 |
| `password_env` | 否 | `DELIVERY_CHECKER_MYSQL_PASSWORD` | 保存密码的环境变量名称 |
| `timeout` | 否 | 5 | 连接和读写超时秒数 |
| `max_attempts` | 否 | 1 | 最大尝试次数 |
| `retry_delay` | 否 | 0.2 | 重试前等待秒数 |

程序连接成功后执行：

```sql
SELECT 1
```

因此它同时验证了基本连接和简单查询能力，但不代表所有业务表和复杂 SQL 都已验证。

### 设置数据库密码

在 PowerShell 当前终端执行：

```powershell
$env:DELIVERY_CHECKER_MYSQL_PASSWORD = "替换为实际密码"
```

然后启动：

```powershell
delivery-checker
```

使用结束后清除：

```powershell
Remove-Item Env:DELIVERY_CHECKER_MYSQL_PASSWORD
```

`password_env` 应填写环境变量名称，而不是真实密码。

错误示例：

```json
"password_env": "my-real-password"
```

正确示例：

```json
"password_env": "DELIVERY_CHECKER_MYSQL_PASSWORD"
```

如果没有设置对应环境变量，程序会使用空字符串尝试连接，可能因身份认证失败而返回 `FAIL`。

## 重试规则

只有以下错误会重试：

- `timeout`；
- `connection`。

以下结果不会盲目重试：

- `PASS`；
- `threshold`；
- `http_status`；
- `unexpected`。

耗时统计包含一项检查的所有尝试和重试等待时间，因此重试后的 `duration_ms` 通常更大。

## 并发和结果顺序

磁盘检查先执行，TCP、HTTP 和 MySQL 网络任务进入同一个线程池。

线程池最多同时使用 4 个工作线程；任务不足 4 个时按实际任务数创建。

最终结果仍按照配置中的类别和项目顺序输出，不按照网络任务的完成先后排列。

## 单独校验配置

只检查配置，不执行巡检：

```powershell
py -c "from delivery_checker.config import load_config; load_config(); print('配置校验通过')"
```

配置正确时输出：

```text
配置校验通过
```

配置错误时，正式程序返回退出码 `2`，不会继续执行检查。

## 修改后的验证顺序

```powershell
py -c "from delivery_checker.config import load_config; load_config(); print('配置校验通过')"
delivery-checker
$LASTEXITCODE
```

退出码含义：

- `0`：全部通过；
- `1`：至少一项巡检失败；
- `2`：配置或运行错误。