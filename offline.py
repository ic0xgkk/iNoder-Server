import json
import subprocess
import time


def block_user():
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    buser = config['blocked']
    for user in buser:
        try:
            process = subprocess.run(['./inoder-support-binary', 'logout', config['interface'], user['addr']],
                                     stdout=subprocess.PIPE, timeout=60)
            stdout = str(process.stdout, encoding='ascii')
            print("下线成功：" + user['name'] + "，" + stdout)
        except subprocess.TimeoutExpired:
            print("超时处理")
        time.sleep(2)


if __name__ == '__main__':
    while True:
        block_user()
        time.sleep(30)
