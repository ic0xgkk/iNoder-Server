# encoding=utf8
import pymysql
import flask
import json
import threading
import logging
import time
import hashlib
import subprocess
import schedule

logname = time.strftime("%Y%m%d%H%M%S", time.localtime())
logname = './log/inoder-' + logname + '.log'
logging.basicConfig(filename=logname,
                    level=logging.DEBUG,
                    format='[%(levelname)s:%(asctime)s] %(message)s')
logging.warning("Server started")


class Database(object):
    def __init__(self, config):
        self.connect = pymysql.connect(host=config['db_host'],
                                       port=config['db_port'],
                                       user=config['db_user'],
                                       password=config['db_password'],
                                       db=config['db_name'],
                                       charset='utf8')

    def __del__(self):
        self.connect.close()


class FlaskApp(object):
    def __init__(self):
        self.app = flask.Flask(__name__)
        self.cookies = []
        self.config = None
        self.url_route()

    def start(self):
        config = self.config
        self.app.run(host=config['s_host'], port=config['s_port'], debug=False, threaded=True)

    def url_route(self):
        self.app.add_url_rule('/', 'site_login', self.site_login, methods=['GET'])
        self.app.add_url_rule('/api/login', 'api_login', self.api_login, methods=['POST'])
        self.app.add_url_rule('/status', 'site_status', self.site_status, methods=['GET'])
        self.app.add_url_rule('/api/action', 'api_action', self.api_action, methods=['POST'])

    def site_login(self):
        html = """
        <!DOCTYPE html>
        <html>
	    <head>
		<meta charset="utf-8" />
		<title>Login</title>
		<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
	    </head>

	    <body>
		<h1>
			<small>iHCS SSO</small>
		</h1>

		<h3>
			<small>WebUI</small>
		</h3>
		<br>You need to login

		<form id="User" action="/api/login" method="post">
			Username: 
			<input type="text" id="user" name="user" placeholder="Username"><br>
			Password: 
			<input type="password" id="pwd" name="pwd" placeholder="Password">
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
        return html

    def api_login(self):
        user = flask.request.form.get('user')
        pwd = flask.request.form.get('pwd')

        if user is None or pwd is None:
            return "Permission Denied"

        user = ''.join(list(filter(str.isdigit, user)))
        pwd = ''.join(list(filter(str.isalnum, pwd)))
        user = str(user)
        pwd = str(pwd)

        db = Database(self.config)
        cursor = db.connect.cursor()
        sql = "SELECT username, stu_name, stu_id, stu_pwd, stu_ip FROM User WHERE username=%s AND password=%s"
        cursor.execute(sql, (user, pwd))

        data = cursor.fetchone()

        if data is None:
            html = """
            <head>
                <meta charset="utf-8" />
                <title>Login Failed</title>
                <meta http-equiv="refresh" content="5;url=/"> 
            </head>
            <body>
                <strong>Login failed, please wait for refreshing</strong>
            </body>
            """
            cursor.close()
            del cursor, sql
            del db
            return html
        else:
            data = list(data)
            data[0] = str(data[0])
            data[1] = str(data[1])
            data[2] = str(data[2])
            data[3] = str(data[3])

            sql = "INSERT INTO LoginLog(username, sysTime, log) VALUES(%s, %s, %s)"
            strtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            ip = str(flask.request.headers['X-Real-Ip'])
            log = "Username %s which named %s login succeed from %s at %s" % (user, data[1], ip, strtime)
            try:
                cursor.execute(sql, (user, strtime, log))
                db.connect.commit()
            except pymysql.Error as e:
                db.connect.rollback()
                logging.error("Database failed %s" % e)
            cookie = hashlib.sha256()
            cookie.update((str(int(time.time())) + str(data[0]) + str(data[1])).encode('utf-8'))
            cookie = cookie.hexdigest()

            ts = time.time()
            self.cookies.append([data, cookie, ts])
            html = """
                        <head>
                            <meta charset="utf-8" />
                            <title>Login Succeed</title>
                            <meta http-equiv="refresh" content="2;url=/status"> 
                        </head>
                        <body>
                            <strong>Login succeed, please wait for refreshing</strong>
                        </body>
                        """
            resp: flask.Response = flask.make_response(html)
            resp.set_cookie(key="INODER", value=str(cookie), expires=int(time.time())+10*60, path='/')
            cursor.close()
            del cursor, sql
            del db
            return resp

    def cookies_scheduler(self):
        while True:
            for item in self.cookies:
                if time.time() - item[2] > 600:
                    self.cookies.remove(item)

            time.sleep(5)

    def site_status(self):
        cookie = flask.request.cookies.get('INODER')
        if cookie is None:
            return "Permission Denied"

        cookie = ''.join(list(filter(str.isalnum, cookie)))
        data = None
        for item in self.cookies:
            if item.count(cookie) == 1:
                data = item[0]
                break
            else:
                continue
        if data is None:
            return "Permission Denied"
        else:
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
    			<small>iHCS iNoder Server</small>
    		</h1>

    		<h3>
    			<small>WebUI (The page does not refresh automatically)</small>
    		</h3>

    		<br>
    		Load time: <strong>%s</strong><br>
    		Username: <strong>%s</strong><br>
    		Student Name: <strong>%s</strong><br>
    		Student ID: <strong>%s</strong><br>

    		<br>
    		<strong>Quick Offline(快速下线)</strong>
    		<form id="Operate" action="/api/action" method="post">
    			<input type="submit" name="action" value="OFF" />
    		</form>
    		<br>
    		<br>
    		<strong>Quick Online(快速上线)</strong>
    		<form id="Operate" action="/api/action" method="post">
    			<input type="submit" name="action" value="ON" />
    		</form>
    		<br>
    		<br>
    		<strong>特别注意</strong><br>
    		请确保使用快速上线时，客户端已经插上网线并且已经获取到IP地址，否则上线不会成功
    		<br>
    		若使用快速上线/快速下线后设备仍然没有上线/下线，请先询问周边他人是否整体断网了
    		<br>
    		若是特例问题，请联系管理员反馈
    		<br>
    		<br>
    		<strong>
    			Ice Cream 2019
    		</strong>
    		<br><br><br>
    	</body>
    </html>
            """
            strtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            html = html % (strtime, data[0], data[1], data[2])
            return html

    def api_action(self):
        cookie = flask.request.cookies.get('INODER')
        if cookie is None:
            return "Permission Denied"

        cookie = ''.join(list(filter(str.isalnum, cookie)))
        data = None
        for item in self.cookies:
            if item.count(cookie) == 1:
                data = item[0]
                break
            else:
                continue
        if data is None:
            return "Permission Denied"
        else:
            html = """
            <head>
            <meta charset="utf-8" />
            <title>Task Committed</title>
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
        </head>
        
        <body>
            <strong>任务已经提交，请等待几秒即可生效</strong><br>
            <strong>若超过1分钟还没有生效，请检查是否统一断网，若为个例问题请联系管理员</strong><br><br>
            <a href="/status"><strong>Go to Homepage</strong></a>
        </body>
        """
            action = flask.request.form.get('action')
            msg = ""
            op = ""
            if action is None:
                return "Permission Denied"
            if hash(action) == hash("OFF"):
                op = "Manual Offline"
                process = subprocess.run(['inoder', 'logout', data[4]], stdout=subprocess.PIPE)
                msg = str(process.stdout, encoding='ascii')
            elif hash(action) == hash("ON"):
                process = subprocess.run(['inoder', 'login', data[2], data[3], data[4]], stdout=subprocess.PIPE)
                msg = str(process.stdout, encoding='ascii')
                op = "Manual Online"
            else:
                return "Permission Denied"

            db = Database(self.config)
            cursor = db.connect.cursor()
            sql = "INSERT INTO OperateLog(username, operateType, sysTime, log) VALUES(%s, %s, %s, %s)"
            strtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            try:
                cursor.execute(sql, (data[0], op, strtime, msg))
                db.connect.commit()
            except pymysql.Error as e:
                db.connect.rollback()
                logging.error("Database failed %s" % e)
            cursor.close()
            del cursor, sql
            del db

            return html


def schedule_login(config):
    db = Database(config)
    cursor = db.connect.cursor()
    sql = "SELECT username, stu_name, stu_id, stu_pwd, stu_ip FROM User"
    cursor.execute(sql)

    data = cursor.fetchall()

    if data is None:
        cursor.close()
        del cursor, sql
        del db
        return None

    data = list(data)

    for item in data:
        item = list(item)
        item[0] = str(item[0])
        item[1] = str(item[1])
        item[2] = str(item[2])
        item[3] = str(item[3])
        op = "Schedule Offline"
        process = subprocess.run(['inoder', 'logout', item[4]], stdout=subprocess.PIPE)
        msg = str(process.stdout, encoding='ascii')
        sql = "INSERT INTO OperateLog(username, operateType, sysTime, log) VALUES(%s, %s, %s, %s)"
        strtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        try:
            cursor.execute(sql, (item[0], op, strtime, msg))
            db.connect.commit()
        except pymysql.Error as e:
            db.connect.rollback()
            logging.error("Database failed %s" % e)

        time.sleep(1)

        op = "Schedule Online"
        process = subprocess.run(['inoder', 'login', item[2], item[3], item[4]], stdout=subprocess.PIPE)
        msg = str(process.stdout, encoding='ascii')
        sql = "INSERT INTO OperateLog(username, operateType, sysTime, log) VALUES(%s, %s, %s, %s)"
        strtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        try:
            cursor.execute(sql, (item[0], op, strtime, msg))
            db.connect.commit()
        except pymysql.Error as e:
            db.connect.rollback()
            logging.error("Database failed %s" % e)
    cursor.close()
    del cursor, sql
    del db


def init():
    with open("config.json", "r", encoding='utf-8') as f:
        config = json.load(f)
        f.close()

    fapp = FlaskApp()
    fapp.config = config

    schedule.every().day.at("07:05").do(schedule_login, config)

    t = threading.Thread(target=fapp.cookies_scheduler, args=())
    t.daemon = True
    t.start()

    ft = threading.Thread(target=fapp.start, args=())
    ft.daemon = True
    ft.start()

    while True:
        time.sleep(1)
        schedule.run_pending()


if __name__ == '__main__':
    init()



