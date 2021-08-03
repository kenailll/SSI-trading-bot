class Proxies:
    def __init__(self):
        with open('proxies.txt', 'r') as f:
            data = [x.strip() for x in f.readlines()]
            self.proxies = data

    def get_proxies(self, proxy):
        proxy_ip = proxy.split(':')
        proxy_url = "http://{user}:{passwd}@{ip}:{port}/".format(
            user=proxy_ip[2],
            passwd=proxy_ip[3],
            ip=proxy_ip[0],
            port=proxy_ip[1]
        )
        return {"http": proxy_url, "https": proxy_url}
