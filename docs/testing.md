# 测试与质量检查

本项目使用 pytest 统一发现和运行测试，测试代码主要基于 Python 标准库 `unittest` 编写。

静态检查由 Ruff 和 MyPy 负责，行为验证由 pytest 负责，三者用途不同。

## 完整检查命令

在项目根目录执行：

```powershell
py -m ruff check .
py -m mypy src main.py
py -m pytest
```

当前测试数量为 21 项。后续增加测试后，应以 pytest 实际收集数量为准。

也可以继续使用原 unittest 入口：

```powershell
py -m unittest discover -v
```

## 测试目录

```text
tests/
├── test_checker.py
├── test_config.py
├── test_main.py
├── test_models.py
├── test_mysql_checker.py
├── test_reporting.py
├── test_runner.py
└── test_storage.py
```

## 当前覆盖范围

| 测试文件 | 主要验证内容 |
| --- | --- |
| `test_checker.py` | 早期统计、SQLite 和 CSV 功能回归测试 |
| `test_config.py` | 合法配置、端口、URL、超时、重试参数和 MySQL 环境变量名称校验 |
| `test_main.py` | 配置错误返回退出码 2 |
| `test_models.py` | 结果模型默认值和字典转换 |
| `test_mysql_checker.py` | MySQL 成功查询、连接失败及密码不出现在结果中 |
| `test_reporting.py` | CSV 导出及 V2 新增字段 |
| `test_runner.py` | 重试、不可重试错误、网络并发、稳定顺序和环境变量传参 |
| `test_storage.py` | 旧数据库升级、新字段保存和历史查询兼容性 |

## 运行部分测试

只运行一个文件：

```powershell
py -m pytest tests/test_runner.py
```

只运行一个测试类：

```powershell
py -m pytest tests/test_runner.py::RunnerTest
```

只运行一个测试方法：

```powershell
py -m pytest tests/test_runner.py::RunnerTest::test_timeout_is_retried
```

显示更详细的信息：

```powershell
py -m pytest -v
```

## 临时目录和临时数据库

存储及报告测试使用 `tempfile.TemporaryDirectory()`。

测试结束后，临时目录会自动清理，不需要使用开发者的正式巡检数据库，也不会把测试数据写入正式报告目录。

这样可以降低测试之间的相互影响，并避免测试污染本地历史记录。

## 为什么使用 Mock

网络、HTTP 和 MySQL 测试不应依赖真实外部服务。

使用 Mock 可以：

- 模拟第一次超时、第二次成功；
- 模拟连接失败；
- 模拟 MySQL 返回 `(1,)`；
- 验证 `SELECT 1` 是否被调用；
- 验证密码是否从指定环境变量传入；
- 避免测试受到外部网站和本地 MySQL 状态影响。

Mock 只能验证代码与依赖的交互方式，不能代替真实环境验收。

## 重试测试

测试会模拟以下情况：

1. 第一次返回 `timeout`；
2. 第二次返回 `PASS`；
3. 验证最终尝试次数为 2。

同时会模拟 `threshold` 错误，验证即使允许多次尝试，也只执行一次。

`time.sleep` 会被模拟，因此测试不会真实等待重试间隔。

## 并发测试

并发测试使用 `threading.Barrier(2)`。

屏障要求 TCP 和 HTTP 两个模拟任务都到达指定位置后才能继续。如果代码退化为串行执行，第一个任务会等待超时，测试不能全部通过。

测试还会检查：

- 最终顺序为磁盘、TCP、HTTP；
- 所有模拟结果均为 `PASS`；
- 并发执行没有改变报告顺序。

## SQLite 升级测试

测试会先手工建立只有五个业务字段的旧表，并插入一条旧记录。

随后调用新版保存函数，验证：

- 自动增加 `duration_ms`、`attempts` 和 `error_type`；
- 新记录正确保存三个新增字段；
- 旧记录使用默认值；
- 原来的五列历史查询仍能工作。

测试使用独立临时数据库，不操作 `data/inspections.db`。

## GitHub Actions

工作流文件：

```text
.github/workflows/ci.yml
```

在 Python 3.11 和 3.12 环境分别执行：

```text
安装项目和开发依赖
Ruff 检查
MyPy 检查
pytest 测试
```

CI 绿色表示本次提交通过这些自动检查，不代表已经完成真实客户现场验证。

## 当前未覆盖的验证

当前自动测试不替代以下工作：

- 真实 MySQL 服务连接和账号权限验收；
- 真实客户内网、防火墙、VPN 和代理环境验证；
- 大量任务下的性能与压力测试；
- 长期连续运行和资源占用观察；
- 生产安全评审；
- 所有异常分支的完整覆盖。

当前没有配置测试覆盖率百分比，因此不宣称达到某个未测量的覆盖率数字。

## 修改代码后的建议顺序

```powershell
py -m ruff check .
py -m mypy src main.py
py -m pytest
py main.py
$LASTEXITCODE
```

如果演示配置仍包含故意失败的端口，正式运行返回 `1` 是预期结果。

不要为了让测试通过而删除正常断言、屏蔽真实错误或提交敏感数据。
