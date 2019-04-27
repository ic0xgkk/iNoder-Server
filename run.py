from flask import Flask, make_response, Response
from flask import request
import random
import time
import json
import logging
import ping3
import threading
import subprocess
import routeros_api

logname = time.strftime("%Y%m%d%H%M%S", time.localtime())
logname = './log/pyf-' + logname + '.log'
logging.basicConfig(filename=logname,
                    level=logging.DEBUG,
                    format='[%(levelname)s:%(asctime)s] %(message)s')
logging.warning("Server started")


class FApp(object):
    def __init__(self, pin: int, user: str):
        self.app = Flask(__name__)
        self.cookie = []
        self.pin = pin
        self.user = user
        self.run_status = "Starting"
        self.fuckh3c = None

    def start(self, host: str = '0.0.0.0', port: int = 2000, debug=False, threaded=True):
        self.app.run(host, port, debug=debug, threaded=threaded)

    def url_route(self):
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        self.app.add_url_rule('/', 'login', self.login, methods=['POST'])
        self.app.add_url_rule('/api/action', 'api_action', self.api_action, methods=['POST'])

    def index(self):
        login_web = """
<!DOCTYPE html>
<html>
	<head>
		<meta charset="utf-8" />
		<title>Login</title>
		<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
	</head>
	
	<body>
		<h1>
			<small>pyfuck_h3c</small>
		</h1>
		
		<h3>
			<small>WebUI :Input your PIN</small>
		</h3>
			
		<form id="InputPIN" action="" method="post">							
			<input type="pin" id="pin" name="pin" placeholder="PIN">
			<br>
			<br>
			<input type="submit" value="Submit">
		</form>
		
		<br>
		<strong>
			Ice Cream 2019
		</strong>
	</body>
</html>
        """
        try:
            cookie = int(request.cookies.get('pyf'))
        except (ValueError, TypeError):
            return login_web

        if self.cookie.count(cookie) == 1:
            return self.get_status()
        else:
            return login_web

    def login(self):
        try:
            pin = int(request.form.get('pin'))
        except ValueError:
            return "PIN incorrect"

        if pin == self.pin:
            cookie = random.randint(10000000, 99999999)
            self.cookie.append(cookie)

            html = """
<head>
    <meta charset="utf-8" />
    <title>Login Success</title>
    <meta http-equiv="refresh" content="2;url=/"> 
</head>
<body>
    <strong>Login succeed, please wait for refreshing</strong>
</body>
            """
            resp: Response = make_response(html)
            resp.set_cookie(key="pyf", value=str(cookie), max_age=3600)

            return resp
        else:
            logging.warning("Login failed")
            return "PIN incorrect"

    def get_status(self):
        html = """
    <!DOCTYPE html>
    <html>
    	<head>
    		<meta charset="utf-8" />
    		<title>Status</title>
    		<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    	</head>

    	<body>
    		<h1>
    			<small>pyfuck_h3c</small>
    		</h1>

    		<h3>
    			<small>WebUI (Need to refresh it by yourself)</small>
    		</h3>

    		<br>
    		Load time: <strong>%s</strong><br>
    		Username：<strong>%s</strong><br>
    		Running Status：<strong>%s</strong><br>
    		Checking Status：<strong>%s</strong><br>

    		<br>
    		Execute：<br>
    		<form id="Operate" action="/api/action" method="post">
    			<input type="submit" name="op" value="Offline" />
    			<input type="submit" name="op" value="Relink" />
    			<input type="submit" name="op" value="Online" />
    		</form>

    		<br>
    		<strong>
    			Ice Cream 2019
    		</strong>

    		<br><br><br>
    	</body>
    </html>
    """
        strtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        html = html % (strtime, self.user, self.run_status, self.fuckh3c.check_status)
        resp = make_response(html)
        return resp

    def api_action(self):
        try:
            cookie = int(request.cookies.get('pyf'))
        except (ValueError, TypeError):
            return "PIN incorrect"

        if self.cookie.count(cookie) == 1:
            pass
        else:
            return "PIN incorrect"

        try:
            operate = hash(str(request.form.get('op')))
        except ValueError:
            return "PIN incorrect"

        html = """
        <head>
            <meta charset="utf-8" />
            <title>Operate Success</title>
            <meta http-equiv="refresh" content="2;url=/"> 
        </head>
        <body>
            <strong>Operate succeed, please wait for refreshing</strong>
        </body>
        """

        if operate == hash("Offline"):
            self.fuckh3c.fapp_logout()
            return html
        elif operate == hash("Relink"):
            self.fuckh3c.fapp_relink()
            return html
        elif operate == hash("Online"):
            self.fuckh3c.fapp_login()
            return html
        else:
            return "Unknow Operate"


class RouterOS(object):
    def __init__(self, config):
        self.rapi = routeros_api.RouterOsApiPool(config['host'], config['ros_user'], config['ros_pwd'],
                                                 config['api_port'], config['use_ssl'], config['verify_ssl'])
        self.rapi.api = self.rapi.get_api()
        self.address = self.rapi.api.get_resource("/ip/address")
        for item in self.address.get():
            if item['interface'] == config['ros_ifname']:
                self.ip = str(item['address']).split('/', 1)[0]

        self.rapi.disconnect()

    def get_ip(self):
        return self.ip


class FuckH3C(object):
    def __init__(self, fapp: FApp, config):
        self.check_status = ""
        self.fapp = fapp
        self.username = config['username']
        self.password = config['password']
        self.ifname = config['ifname']

        tmp = RouterOS(config)
        self.ip = tmp.get_ip()
        del tmp

    def login(self):
        if self.check_network() == 1:
            return True

        subprocess.run(['fuckh3c', 'login', self.username, self.password, self.ifname, self.ip])

        time.sleep(2)

        if self.check_network() == -1:
            logging.error("Auth finished but still can not connect to network")
            return False

        self.check_status = "Online"

    def logout(self):
        if self.check_network() == -1:
            logging.warning("Network failed, no needs to logout")
            return True

        subprocess.run(['fuckh3c', 'logout', self.ifname, self.ip])
        time.sleep(2)

        if self.check_network() == 1:
            logging.error("Logout failed")
            return False

        self.check_status = "Offline"

    def check_network_th(self):
        time.sleep(30)
        while True:
            if self.check_network() == -1:
                self.check_status = "Offline"
            else:
                self.check_status = "Online"
            time.sleep(120)

    def check_network(self):
        delay_1 = ping3.ping("223.5.5.5", timeout=1, ttl=64, unit="ms")
        delay_2 = ping3.ping("114.114.114.114", timeout=1, ttl=64, unit="ms")
        delay_3 = ping3.ping("223.6.6.6", timeout=1, ttl=64, unit="ms")
        delay_4 = ping3.ping("1.1.1.1", timeout=1, ttl=64, unit="ms")
        if delay_1 is None and delay_2 is None and delay_3 is None and delay_4 is None:
            return -1  # Offline
        else:
            return 1  # Online

    def schedule(self):
        self.logout()
        time.sleep(2)
        self.login()
        self.fapp.run_status = "Running"

    def start(self):
        # 状态检查线程
        check_th = threading.Thread(target=self.check_network_th, args=())
        check_th.daemon = True
        check_th.start()

        # 上线
        self.schedule()

    def fapp_login(self):
        self.login()

    def fapp_relink(self):
        self.logout()
        time.sleep(1)
        self.login()

    def fapp_logout(self):
        self.logout()


def get_config():
    with open("config.json", "r", encoding='utf-8') as f:
        config = json.load(f)
        f.close()
    return config


def init():
    config = get_config()

    fapp = FApp(config['PIN'], config['username'])
    fapp.fuckh3c = FuckH3C(fapp, config)

    # WebUI线程启动
    fapp.url_route()
    fapp_th = threading.Thread(target=fapp.start, args=())
    fapp_th.daemon = True
    fapp_th.start()

    # Auth启动
    fapp.fuckh3c.start()

    while True:
        time.sleep(3600)


if __name__ == '__main__':
    init()

