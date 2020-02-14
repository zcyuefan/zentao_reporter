# zentao_reporter

一款开源版禅道报告生成工具，便捷生成一段时间内禅道用户bug、任务相关报告。
结合Crontab实现日报、周报、月报功能，直观的统计每个员工的工作。

## 项目地址
欢迎star和fork
[https://github.com/zcyuefan/zentao_reporter](https://github.com/zcyuefan/zentao_reporter)

## 已实现功能

- [x] BUG创建、激活、关闭、解决、当前待处理BUG情况汇总
- [x] BUG创建详细
- [x] BUG激活详细
- [x] BUG关闭详细
- [x] BUG解决详细
- [x] 当前待处理BUG详细
- [x] 进行的任务，以及当期消耗工时
- [x] 当前待处理任务详细
- [x] 未来3天（可以设置）任务完成情况。
- [x] 结合crontab实现自动生成日报、周报、月报

## TODO
以下是本工具预计增加的功能，也欢迎大家多提意见和参与开发！

- 邮件发送
- 在线查看？
- 在线生成？

## 安装和使用

### 1. 在禅道数据库中运行sql目录中的文件

目的是创建本工具需要查询的视图

### 2. 安装依赖

```bash
pip install -r requirments.txt
```

### 3.结合实际修改配置文件config.py

### 4.运行程序
通过命令运行
```bash
# 生成当日日报
python zentao_reporter.py --today --report-type daily
# 生成周报
python zentao_reporter.py --today --report-type weekly
# 生成月报
python zentao_reporter.py --today --report-type monthly
# 生成2020-01-02至2020-02-11报告
python zentao_reporter.py --from-date 2020-01-02 --to-date 2020-02-11
```

--help查看帮助
```bash
(venv) F:\00projects\zentao_reporter>python zentao_reporter.py --help
Usage: zentao_reporter.py [OPTIONS]

  生成禅道报告

Options:
  --report-type [daily|weekly|monthly]
                                  报告类型, 不选择则生成普通报告
  --from-date [%Y-%m-%d]          报告开始日期，如 --to-date 2020-02-03
  --to-date [%Y-%m-%d]            报告结束日期，如 --to-date 2020-02-14
  --today                         以今日为报告结束日期，等同 --to-date 今日
  --help                          Show this message and exit.
```

crontab 自动生成实例

```bash
# 每日19点生成日报
0 19 * * * /usr/bin/python3 /opt/zbox/app/zentao_reporter/zentao_reporter.py --today --report-type daily
# 每周六19点生成周报
0 19 * * 6 /usr/bin/python3 /opt/zbox/app/zentao_reporter/zentao_reporter.py --today --report-type weekly
# 每月最后一日19点生成月报
0 19 28-31 * * [ `date -d tomorrow +\%e` -eq 1 ] && (/usr/bin/python3 /opt/zbox/app/zentao_reporter/zentao_reporter.py --today --report-type monthly)
```

## 生成报告截图
![img](https://github.com/zcyuefan/zentao_reporter/blob/master/img/screenshot.png)
