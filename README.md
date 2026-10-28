\# 实施交付环境巡检工具



\## 项目简介



一个面向软件实施与交付场景的命令行巡检工具，用于在系统部署或交付前检查磁盘、网络端口和HTTP服务状态，并保存巡检历史、导出CSV报告。



项目仅使用Python标准库，不依赖第三方包，适合在不便安装额外依赖的环境中运行。



\## 已实现功能



\- 磁盘剩余空间检查，支持自定义最低空间阈值；

\- TCP端口连通性检查，支持连接超时设置；

\- HTTP健康检查，记录HTTP状态码或请求异常；

\- 使用JSON配置文件管理巡检项；

\- 使用SQLite保存巡检历史；

\- 查询最近的巡检记录；

\- 导出UTF-8-SIG编码的CSV报告，便于使用Excel查看；

\- 自动统计PASS和FAIL数量；

\- 根据巡检结果返回程序退出状态码；

\- 使用unittest验证统计、数据库和CSV导出功能。



\## 技术栈



Python 3、SQLite、JSON、CSV、unittest。



\## 项目结构



```text

delivery-checker/

├── main.py              # 巡检、存储、查询和报告导出逻辑

├── config.json          # 巡检对象及阈值配置

├── test\_checker.py      # 自动化测试

├── data/                # SQLite数据库

└── reports/             # CSV巡检报告

