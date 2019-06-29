# encoding=utf8
import json
import logging
import time
import subprocess
import schedule

logname = time.strftime("%Y%m%d%H%M%S", time.localtime())
logname = './log/inoder-sbs-' + logname + '.log'
logging.basicConfig(filename=logname,
                    level=logging.DEBUG,
                    format='[%(levelname)s:%(asctime)s] %(message)s')
logging.warning("Server started")


class ReAuth(object):
    def __init__(self):
        self.config = self.load_config()

    def everyday_morning(self):
        users = self.config['user']
        for user in users:
            stdout = self.sbs_opt(['logout', self.config['interface'], user['addr']])
            time.sleep(1)
            try:
                self.ana_opt_stdout(stdout)
            except Exception as e:
                logging.error("未知问题：" + str(e))
        time.sleep(3)
        for user in users:
            stdout = self.sbs_opt(['login', user['username'], user['password'],
                                   self.config['interface'], user['addr']])
            time.sleep(1)
            try:
                self.ana_opt_stdout(stdout)
            except Exception as e:
                logging.error("未知问题：" + str(e))

    def everyday_afternoon(self):
        users = self.config['user']
        for user in users:
            stdout = self.sbs_opt(['login', user['username'], user['password'],
                                   self.config['interface'], user['addr']])
            time.sleep(30)
            logging.info("中午二次认证记录：" + user['name'] + "，" + str(stdout))

    def load_config(self):
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config

    def sbs_opt(self, args):
        if args[0] == 'login':
            try:
                process = subprocess.run(['./inoder-support-binary', 'login', args[1], args[2], args[3], args[4]],
                                         stdout=subprocess.PIPE, timeout=60)
                stdout = str(process.stdout, encoding='ascii')
                return stdout
            except subprocess.TimeoutExpired:
                logging.warning("上线超时")
                return None
        elif args[0] == 'logout':
            try:
                process = subprocess.run(['./inoder-support-binary', 'logout', args[1], args[2]],
                                         stdout=subprocess.PIPE, timeout=60)
                stdout = str(process.stdout, encoding='ascii')
                return stdout
            except subprocess.TimeoutExpired:
                logging.warning("下线超时")
                return None
        else:
            logging.error("参数错误")
            return None

    def ana_opt_stdout(self, stdout):
        err_code = {
            "CE01": "创建套接字时错误，可能是没有root权限",
            "CE02": "设置发送超时失败",
            "CE03": "设置接收超时失败",
            "CE04": "发送失败或者超时",
            "CE05": "接收失败或者超时",
            "CE06": "Unknow problem and failed to auth",
            "CE07": "获取网卡IP创建套接字失败（该函数在本分支内禁用）",
            "CE08": "从网卡接口获取IP失败（此函数在本分支禁用）",
            "CS01": "下线成功",
            "CS02": "上线成功",
            "E63013": "用户已被加入黑名单",
            "E63018": "用户不存在或者用户没有申请该服务",
            "E63019": "用户处于暂停状态",
            "E63022": "在线用户数量限制",
            "E63023": "用户密码错误",
            "E63024": "端口绑定检查失败",
            "E63025": "MAC地址绑定检查失败",
            "E63026": "静态IP地址绑定检查失败",
            "E63029": "IP或MAC地址绑定检查失败",
            "E63031": "用户密码错误，该用户已经被加入黑名单",
            "E63032": "密码错误，密码连续错误次数超过阈值将会加入黑名单",
            "E63047": "认证客户端版本太低",
            "E63048": "设备IP绑定检查失败",
            "E63049": "设备VLAN绑定检查失败",
            "E63100": "无效认证客户端版本"
        }
        if stdout is None:
            return None
        keys = str(stdout).split(':')
        if keys[0] == 'ERROR':
            try:
                logging.error("认证失败："+ keys[1] + "，" + err_code[keys[1]])
            except KeyError:
                logging.error('认证失败，其他错误:' + keys[1])
        elif keys[0] == 'SUCC':
            logging.info("认证通过：" + keys[1] + "，" + err_code[keys[1]])


if __name__ == '__main__':
    ra = ReAuth()
    schedule.every().day.at("07:10").do(ra.everyday_morning)
    schedule.every().day.at("13:20").do(ra.everyday_afternoon)

    while True:
        time.sleep(3)
        schedule.run_pending()





