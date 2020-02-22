#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    zentao_reporter
    -----------------------------
    程序入口
    :copyright: (c) 2020 by zcyuefan.
    :license: LICENSE_NAME, see LICENSE_FILE for more details.
"""
import os
import MySQLdb
import click
from config import default_config
from jinja2 import Template
from datetime import datetime, timedelta


class Reporter:
    """报告生成类"""

    def __init__(self, from_date, to_date, config=default_config):
        self.from_date = from_date
        self.to_date = to_date
        self.config = config
        self.report = {}
        self.template_file_name = 'report.html'
        self.report_title = '{}至{}禅道报告'.format(self.from_date, self.to_date)
        self.conn = self._connect_db(config.ZENTAO_DB)

    @staticmethod
    def _connect_db(db_params):
        """
        建立数据库连接
        :param db_params:
        :return:
        """
        if isinstance(db_params, tuple):
            return MySQLdb.connect(*db_params)
        elif isinstance(db_params, dict):
            return MySQLdb.connect(**db_params)
        else:
            raise TypeError('db_params参数类型错误，当前值为{}{}'.format(db_params, type(db_params)))

    def get_build_stat(self, from_date, to_date):
        """
        查询版本信息
        :param from_date: 起始日期
        :param to_date: 终止日期
        :return: [(版本名称，打包日期,完成需求，解决bug)]
        """
        print('正在获取版本信息……')
        stat = []
        query_detail = "SELECT `name`, date, stories, bugs FROM zt_build WHERE deleted<>0 AND date BETWEEN %s AND %s ORDER BY id desc"
        detail = self._query(query_detail, (from_date, to_date))
        for i in detail:
            if i[3]:
                query_bugs = 'SELECT GROUP_CONCAT(CONCAT("#",`id`,`title`) separator "<br />") FROM zt_bug WHERE id in (%s);' % \
                             i[3].strip(',')
                bugs = self._query(query_bugs)[0][0]
            else:
                bugs = ''
            if i[2]:
                query_stories = 'SELECT GROUP_CONCAT(CONCAT("#",`id`,`title`) separator "<br />") FROM zt_story WHERE id in (%s);' % \
                                i[2].strip(',')
                stories = self._query(query_stories)[0][0]
            else:
                stories = ''
            stat.append([i[0], i[1], stories, bugs])
        return stat

    def get_user_stat(self, user, from_date, to_date):
        """
        返回一个用户的报告
        :param user: 禅道account
        :param from_date: 起始日期
        :param to_date: 终止日期
        :return: {
            'account': 用户account,
            'realname': 用户真名,
            'bug': {
                'open': 创建bug情况,
                'close': 关闭bug情况,
                'active': 激活bug情况,
                'resolve': 解决bug情况,
                'current': 当前被指派bug情况
            },
            'task': {
                'do': 完成任务工时情况,
                'current': 当前被指派任务情况
            }
        }
        """
        print('正在获取%s报告……' % user)
        return {
            'account': user,
            'realname': self._get_user_realname(user),
            'from_date': from_date,
            'to_date': to_date,
            'bug': {
                'open': self._query_user_open_bug(user, from_date, to_date),
                'close': self._query_user_close_bug(user, from_date, to_date),
                'active': self._query_user_active_bug(user, from_date, to_date),
                'resolve': self._query_user_resolve_bug(user, from_date, to_date),
                'current': self._query_user_current_bug(user)
            },
            'task': {
                'do': self._query_user_do_task(user, from_date, to_date),
                'current': self._query_user_current_task(user),
                'short_period': self._query_user_short_period_task(user, to_date),
                'month_done': self._query_user_month_done_task(user, to_date)
            }
        }

    def _get_user_realname(self, user):
        """
        查询account真名
        :param user:
        :return: realname
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT `realname` FROM zt_user WHERE account=%s", (user,))
        entry = cursor.fetchone()
        return entry[0]

    def _query_user_open_bug(self, user, from_date, to_date):
        """
        查询用户创建的bug
        :param user: 禅道account
        :param from_date: 起始日期
        :param to_date: 终止日期
        :return: {
        'detail': [查询出的列表，包括日期，严重程度，bug总数，bug详情],
        'summary': {'致命':1, '严重':3, '一般': 5, '提示': '6'},
        'total': 总数
        }
        """
        stat = {}
        query_detail = "SELECT `day`, `severity`, `bugopen`, `bugs` FROM `ztv_userdayopenbug` WHERE `account` = %s AND `day` BETWEEN %s AND %s"
        stat['detail'] = self._query(query_detail, (user, from_date, to_date))
        query_summary = "SELECT `severity`, SUM(`bugopen`) FROM `ztv_userdayopenbug` WHERE `account` = %s AND `day` BETWEEN %s AND %s GROUP BY severity"
        summary = self._query(query_summary, (user, from_date, to_date))
        stat['summary'] = {i[0]: i[1] for i in summary}
        stat['total'] = sum([i[1] for i in summary])
        return stat

    def _query_user_close_bug(self, user, from_date, to_date):
        """
        查询用户关闭的bug
        :param user: 禅道account
        :param from_date: 起始日期
        :param to_date: 终止日期
        :return: {
        'detail': [查询出的列表，包括日期，严重程度，bug总数，bug详情],
        'summary': {'致命':1, '严重':3, '一般': 5, '提示': '6'},
        'total': 总数
        }
        """
        stat = {}
        query_detail = "SELECT `day`, `severity`, `bugclose`, `bugs` FROM `ztv_userdayclosebug` WHERE `account` = %s AND `day` BETWEEN %s AND %s"
        stat['detail'] = self._query(query_detail, (user, from_date, to_date))
        query_summary = "SELECT `severity`, SUM(`bugclose`) FROM `ztv_userdayclosebug` WHERE `account` = %s AND `day` BETWEEN %s AND %s GROUP BY severity"
        summary = self._query(query_summary, (user, from_date, to_date))
        stat['summary'] = {i[0]: i[1] for i in summary}
        stat['total'] = sum([i[1] for i in summary])
        return stat

    def _query_user_active_bug(self, user, from_date, to_date):
        """
        查询用户激活的bug
        :param user: 禅道account
        :param from_date: 起始日期
        :param to_date: 终止日期
        :return: {
        'detail': [查询出的列表，包括日期，严重程度，bug总数，bug详情],
        'summary': {'致命':1, '严重':3, '一般': 5, '提示': '6'},
        'total': 总数
        }
        """
        stat = {}
        query_detail = "SELECT `day`, `severity`, `bugactive`, `bugs` FROM `ztv_userdayactivebug` WHERE `account` = %s AND `day` BETWEEN %s AND %s"
        stat['detail'] = self._query(query_detail, (user, from_date, to_date))
        query_summary = "SELECT `severity`, SUM(`bugactive`) FROM `ztv_userdayactivebug` WHERE `account` = %s AND `day` BETWEEN %s AND %s GROUP BY severity"
        summary = self._query(query_summary, (user, from_date, to_date))
        stat['summary'] = {i[0]: i[1] for i in summary}
        stat['total'] = sum([i[1] for i in summary])
        return stat

    def _query_user_resolve_bug(self, user, from_date, to_date):
        """
        查询用户解决的bug
        :param user: 禅道account
        :param from_date: 起始日期
        :param to_date: 终止日期
        :return: {
        'detail': [查询出的列表，包括日期，严重程度，bug总数，bug详情],
        'summary': {'致命':1, '严重':3, '一般': 5, '提示': '6'},
        'total': 总数
        'code_error_percent': 代码错误比例
        }
        """
        stat = {}
        query_detail = "SELECT `day`, `severity`, `bugresolve`, `bugs` FROM `ztv_userdayresolvebug` WHERE `account` = %s AND `day` BETWEEN %s AND %s"
        stat['detail'] = self._query(query_detail, (user, from_date, to_date))
        query_summary = "SELECT `severity`, SUM(`bugresolve`) FROM `ztv_userdayresolvebug` WHERE `account` = %s AND `day` BETWEEN %s AND %s GROUP BY severity"
        summary = self._query(query_summary, (user, from_date, to_date))
        stat['summary'] = {i[0]: i[1] for i in summary}
        stat['total'] = int(sum([i[1] for i in summary]))
        query_code_error_count = "SELECT COUNT(0) FROM zt_bug WHERE resolvedBy=%s AND type='codeerror' AND resolvedDate BETWEEN %s AND %s"
        code_error_count = self._query(query_code_error_count, (user, from_date + ' 00:00:00', to_date + ' 23:59:59'))
        stat['code_error_percent'] = round(code_error_count[0][0] / stat['total'], 2) if stat['total'] else 0
        return stat

    def _query_user_current_bug(self, user):
        """
        查询用户当前被指派的bug
        :param user: 禅道account
        :return: {
        'detail': [查询出的列表，包括严重程度，bug总数，bug详情],
        'summary': {'致命':1, '严重':3, '一般': 5, '提示': '6'},
        'total': 总数
        }
        """
        stat = {}
        query_detail = "SELECT `severity`, `bugassign`, `bugs` FROM `ztv_usercurrentbug` WHERE `account` = %s"
        detail = self._query(query_detail, (user,))
        stat['detail'] = detail
        stat['summary'] = {i[0]: i[1] for i in detail}
        stat['total'] = sum([i[1] for i in detail])
        return stat

    def _query_user_do_task(self, user, from_date, to_date):
        """
        查询用户完成和进行工时的task
        :param user: 禅道account
        :param from_date: 起始日期
        :param to_date: 终止日期
        :return: {
        'detail': [查询出的列表，包括日期，taskid，taskname，预计工时, 消耗工时， 剩余工时],
        'total_consumed': 总消耗工时
        }
        """
        stat = {}
        query_detail = "SELECT `day`, `taskid`, `taskname`, `estimate`,`consumed`,`left` FROM `ztv_userdaydotask` WHERE `account` = %s AND `day` BETWEEN %s AND %s"
        stat['detail'] = self._query(query_detail, (user, from_date, to_date))
        stat['total_consumed'] = sum([i[4] for i in stat['detail']])
        return stat

    def _query_user_month_done_task(self, user, to_date):
        """
        查询用户当月完成的task
        :param user: 禅道account
        :param to_date: 终止日期
        :return: {
        'count': 总数，'estimate':预计工时, 'consumed':消耗工时, 'left':剩余工时
        }
        """
        month = to_date[:7]
        first_day = month + '-01'
        query_detail = "select count(*), ROUND(sum(`zt_task`.`estimate`), 2) AS `estimate`,ROUND(sum(`zt_task`.`consumed`),2) AS `consumed`,ROUND(sum(`zt_task`.`left`),2) AS `left` from `zt_task` where ((`zt_task`.`deleted`='0') AND (`zt_task`.`finishedBy` = %s) AND (`zt_task`.`parent` <> -1) AND (`zt_task`.`finishedDate` BETWEEN %s AND %s) and (`zt_task`.`status` in ('closed','done')) AND (`zt_task`.`closedReason` <> 'cancel'))"
        result = self._query(query_detail, (user, first_day + ' 00:00:00', to_date + ' 23:59:59'))
        return {
            'count': result[0][0], 'estimate': result[0][1], 'consumed': result[0][2], 'left': result[0][3]
        }

    def _query_user_current_task(self, user):
        """
        查询用户当前被指派的task
        :param user: 禅道account
        :return: {
        'detail': [查询出的列表，包括状态，指派task总数，task详细],
        'summary': {'doing':1, 'done':3, 'wait': 5},
        'total': 总数
        }
        """
        stat = {}
        query_detail = "SELECT `status`, `taskassign`, `tasks` FROM `ztv_usercurrenttask` WHERE `account` = %s"
        detail = self._query(query_detail, (user,))
        stat['detail'] = detail
        stat['summary'] = {i[0]: i[1] for i in detail}
        stat['total'] = sum([i[1] for i in detail])
        return stat

    def _query_user_short_period_task(self, user, to_date):
        """
        查询用户未来短期task情况
        :param user: 禅道account
        :return: {
        'detail': 查询出的列表，包括deadline，taskid，taskname, taskstatus, estimate, consumed, left
        'summary': {'estimate':预计消耗总工时, 'consumed':已经消耗总工时, 'left':剩余总工时 },
        }
        """
        stat = {}
        deadline = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=self.config.SHORT_PERIOD_DAY)
        deadline_str = deadline.strftime('%Y-%m-%d')
        query_detail = "select `zt_task`.`deadline` AS `deadline`,`zt_task`.`id` AS `id`,`zt_task`.`name` AS `name`,`zt_task`.`status` AS `status`,`zt_task`.`estimate` AS `estimate`,`zt_task`.`consumed` AS `consumed`,`zt_task`.`left` AS `left` from `zt_task` where ((`zt_task`.`assignedTo` = %s) AND (`zt_task`.`parent` <> -1) AND (`zt_task`.`deadline` <= %s) and (`zt_task`.`status` not in ('closed','cancel')));"
        detail = self._query(query_detail, (user, deadline_str))
        stat['detail'] = detail
        query_summary = "select ROUND(sum(`zt_task`.`estimate`), 2) AS `estimate`,ROUND(sum(`zt_task`.`consumed`),2) AS `consumed`,ROUND(sum(`zt_task`.`left`),2) AS `left` from `zt_task` where ((`zt_task`.`assignedTo` = %s) AND (`zt_task`.`parent` <> -1) AND (`zt_task`.`deadline` <= %s) and (`zt_task`.`status` not in ('closed','cancel')))"
        summary = self._query(query_summary, (user, deadline_str))
        if len(summary) > 0:
            stat['summary'] = {
                'estimate': summary[0][0], 'consumed': summary[0][1], 'left': summary[0][2]
            }
        else:
            stat['summary'] = {
                'estimate': 0, 'consumed': 0, 'left': 0
            }
        stat['period'] = self.config.SHORT_PERIOD_DAY
        return stat

    def _query(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        entries = cursor.fetchall()
        print('执行SQL:%s' % cursor._executed)
        return entries

    def gen_report(self):
        print('正在获取报告……')
        self.report['title'] = self.report_title
        self.report['build'] = self.get_build_stat(self.from_date, self.to_date)
        self.report['group_stat'] = {}
        for group, group_users in self.config.ZENTAO_USERS.items():
            self.report['group_stat'][group] = []
            for user in group_users:
                self.report['group_stat'][group].append(self.get_user_stat(user, self.from_date, self.to_date))
        print(self.report)
        return self.report

    def gen_html_report(self):
        print('正在生成报告……')
        template_path = os.path.join(self.config.TEMPLATES_PATH, self.template_file_name)
        if not os.path.isdir(self.config.REPORTS_PATH):
            os.makedirs(self.config.REPORTS_PATH)

        report_path = os.path.join(self.config.REPORTS_PATH, self.report_title + '.html')
        with open(template_path, "r", encoding='utf-8') as fp_r:
            template_content = fp_r.read()
            with open(report_path, 'w', encoding='utf-8') as fp_w:
                rendered_content = Template(
                    template_content,
                    # extensions=["jinja2.ext.loopcontrols"]
                ).render(self.report)
                fp_w.write(rendered_content)
        print('报告生成成功，保存位置：%s' % report_path)

    def send_email(self):
        pass


class DailyReporter(Reporter):
    """日报"""

    def __init__(self, date, config=default_config):
        super().__init__(from_date=date, to_date=date, config=config)
        self.report_title = '{}禅道日报'.format(date)


class WeeklyReporter(Reporter):
    """周报"""

    def __init__(self, to_date, config=default_config):
        to_datetime = datetime.strptime(to_date, '%Y-%m-%d')
        monday = to_datetime - timedelta(days=to_datetime.weekday())
        monday_str = monday.strftime('%Y-%m-%d')
        sunday = monday + timedelta(days=6)
        sunday_str = sunday.strftime('%Y-%m-%d')
        super().__init__(from_date=monday_str, to_date=to_date, config=config)
        self.report_title = '{}至{}禅道周报'.format(monday_str, sunday_str)


class MonthlyReporter(Reporter):
    """月报"""

    def __init__(self, to_date, config=default_config):
        month = to_date[:7]
        first_day = month + '-01'
        super().__init__(from_date=first_day, to_date=to_date, config=config)
        self.report_title = '{}禅道月报'.format(month)


@click.command()
@click.option('--report-type', type=click.Choice(['daily', 'weekly', 'monthly'], case_sensitive=False),
              help='报告类型, 不选择则生成普通报告')
@click.option('--from-date', type=click.DateTime(formats=('%Y-%m-%d',)), help='报告开始日期，如 --to-date 2020-02-03')
@click.option('--to-date', type=click.DateTime(formats=('%Y-%m-%d',)), help='报告结束日期，如 --to-date 2020-02-14')
@click.option('--today', is_flag=True, help='以今日为报告结束日期，等同 --to-date 今日')
def build_zentao_report(report_type, from_date, to_date, today):
    """生成禅道报告"""
    if today and to_date:
        raise click.BadParameter('参数 --to-date 和 --today 冲突, 只能给其中一个参数赋值')
    elif today and not to_date:
        to_date_str = datetime.now().strftime('%Y-%m-%d')
    elif not today and to_date:
        to_date_str = to_date.strftime('%Y-%m-%d')
    else:
        raise click.MissingParameter('参数 --to-date 或 --today 必填')
    if from_date and report_type:
        raise click.BadParameter('--report-type 和 --from-date 冲突, 选择报告类型后，报告开始日期值将固定')
    elif from_date and not report_type:
        from_date_str = from_date.strftime('%Y-%m-%d')
        reporter = Reporter(from_date_str, to_date_str)
    elif not from_date and report_type == 'daily':
        reporter = DailyReporter(to_date_str)
    elif not from_date and report_type == 'weekly':
        reporter = WeeklyReporter(to_date_str)
    elif not from_date and report_type == 'monthly':
        reporter = MonthlyReporter(to_date_str)
    else:
        raise click.MissingParameter('参数 --from-date 或 --report-type 必填')
    reporter.gen_report()
    reporter.gen_html_report()


if __name__ == "__main__":
    build_zentao_report()
