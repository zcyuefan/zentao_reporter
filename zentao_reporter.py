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
from config import default_config
from jinja2 import Template
from datetime import datetime, timedelta


class Reporter:

    def __init__(self, from_date, to_date, config=default_config):
        self.from_date = from_date
        self.to_date = to_date
        self.config = config
        self.summary = []
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
                'short_period': self._query_user_short_period_task(user, to_date)
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
        }
        """
        stat = {}
        query_detail = "SELECT `day`, `severity`, `bugresolve`, `bugs` FROM `ztv_userdayresolvebug` WHERE `account` = %s AND `day` BETWEEN %s AND %s"
        stat['detail'] = self._query(query_detail, (user, from_date, to_date))
        query_summary = "SELECT `severity`, SUM(`bugresolve`) FROM `ztv_userdayresolvebug` WHERE `account` = %s AND `day` BETWEEN %s AND %s GROUP BY severity"
        summary = self._query(query_summary, (user, from_date, to_date))
        stat['summary'] = {i[0]: i[1] for i in summary}
        stat['total'] = sum([i[1] for i in summary])
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
        detail = self._query(query_detail, (user, ))
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
        'detail': [查询出的列表，包括日期，taskid，taskname，消耗工时],
        'total_consumed': 总消耗工时
        }
        """
        stat = {}
        query_detail = "SELECT `day`, `taskid`, `taskname`, `consumed` FROM `ztv_userdaydotask` WHERE `account` = %s AND `day` BETWEEN %s AND %s"
        stat['detail'] = self._query(query_detail, (user, from_date, to_date))
        stat['total_consumed'] = sum([i[3] for i in stat['detail']])
        return stat

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
        detail = self._query(query_detail, (user, ))
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
        query_summary = "select ROUND(sum(`zt_task`.`estimate`), 2) AS `estimate`,ROUND(sum(`zt_task`.`consumed`),2) AS `consumed`,ROUND(sum(`zt_task`.`left`),2) AS `left` from `zt_task` where ((`zt_task`.`assignedTo` = %s) AND (`zt_task`.`parent` <> -1) AND (`zt_task`.`deadline` <= %s) and (`zt_task`.`status` not in ('closed','cancel'))) GROUP BY assignedTo"
        summary = self._query(query_summary, (user, deadline_str))
        stat['summary'] = {
            'estimate': summary[0][0], 'consumed': summary[0][1], 'left': summary[0][2]
        }
        stat['period'] = self.config.SHORT_PERIOD_DAY
        return stat

    def _query(self, query, params):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        entries = cursor.fetchall()
        print('执行SQL:%s' %cursor._executed)
        return entries

    def gen_summary(self):
        print('正在获取报告……')
        for user in self.config.ZENTAO_USERS:
            self.summary.append(self.get_user_stat(user, self.from_date, self.to_date))
        return self.summary

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
                ).render({'title': self.report_title, 'summary': self.summary})
                fp_w.write(rendered_content)
        print('报告生成成功，保存位置：%s' % report_path)

    def send_email(self):
        pass


class DailyReporter(Reporter):
    def __init__(self, date, config=default_config):
        super().__init__(from_date=date, to_date=date, config=config)
        self.report_title = '{}禅道日报'.format(date)


if __name__ == "__main__":
    my_reporter = DailyReporter('2020-02-13')
    # my_reporter = Reporter('2020-02-12', '2020-02-12')
    my_reporter.gen_summary()
    print(my_reporter.summary)
    my_reporter.gen_html_report()
