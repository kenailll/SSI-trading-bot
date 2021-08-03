import requests
import json
import re
from bs4 import BeautifulSoup


class Request:
    def __init__(self):
        self.session = requests.Session()
        self.lst_stock = []
        self.user = ''
        self.pwd = ''
        self.pin = ''
        self.get_headers()
        self.day_night = 1

    def proxy_set(self, proxy):
        self.headers = ''
        self.session.cookies.clear()
        self.session.proxies.clear()
        self.session.proxies.update(proxy)
        self.get_headers()

    def get_headers(self):
        temp = self.session.get('https://webtrading.ssi.com.vn/Logon')
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36 Edg/89.0.774.50',
            'Cookie': temp.headers['Set-Cookie']
        }

    def login(self, username, password, pin):
        url = 'https://webtrading.ssi.com.vn/ajaxdata/Login.aspx'
        data = {
            'userName': username,
            'password': password,
            'secureCode': '',
            'resetFail': 0
        }
        response = self.session.post(url, data=data, headers=self.headers)
        status = json.loads(response.text)
        if response.ok and status[0] == '1':
            self.user = username
            self.pwd = password
            check_pin = self.order(stock='MSB', units=100, price=0, order='B', pin=pin)
            if check_pin[0] != 'Mã xác nhận không đúng (ECS016)' and check_pin[0] != 'Mã Pin/Token không được để trống (ECI005).':
                self.pin = pin
                self.info = self.contact_info()
            else:
                return check_pin[0]
        return status[2]

    def contact_info(self):
        url1 = 'https://webtrading.ssi.com.vn/ContactInfo.aspx'
        data = {
            'rParams': 'ContactInfo',
            'AccountNo': self.user + '1'
        }
        rq = self.session.post(url1, data=data, headers=self.headers)
        soup = BeautifulSoup(rq.text, 'html.parser')
        rq1 = soup.find('span', id='span1').text
        rq1 = rq1.strip()

        url2 = 'https://httpbin.org/ip'
        rq2 = self.session.get(url2, headers=self.headers)
        rq2 = json.loads(rq2.text)['origin']
        response = [rq1, rq2]
        return response

    def get_fav_list_stock(self):
        url = 'https://webtrading.ssi.com.vn/ajaxdata/GetFavoriteStockList.aspx'
        data = {
            'rParam': 'test'
        }
        rq = self.session.post(url, data=data, headers=self.headers)
        temp = rq.text.replace("'", '"')
        temp = temp.replace(',]', ']')
        temp = json.loads(temp)['Favorite']
        response = list()
        for item in temp:
            response.extend(item['StockList'])
        response = list(set(response))
        return response

    def get_price(self, lst_stock):
        str_stock = str(lst_stock)[1:-1]
        url = 'https://webtrading.ssi.com.vn/ajaxdata/GetPriceData.aspx'
        data = {
            'seqhose': -1,
            'seqhnx': -1,
            'sequpcom': -1,
            'catid': 0,
            'old_phase_hose': 0,
            'old_phase_hnx': 0,
            'old_phase_upcom': 0,
            'favs': 0,
            'liststock': str_stock,
            'currentFav': 'Default',
            'priceboardType': 'PriceboardIntraday',
        }

        rq = self.session.post(url, data=data, headers=self.headers)
        temp_str = re.sub(',(0+)(\d+)', r',\2', rq.text)
        temp_str = re.sub(',(-0-\d*),', '', temp_str)
        temp_str.replace(',]', ']')
        temp_dict = json.loads(temp_str)
        response = list()

        for item in temp_dict.keys():
            if str(item) == 'NEWSTOCK' or str(item) == 'TradeDate':
                continue
            else:
                for item_2 in temp_dict[item][0]:
                    temp = list()
                    temp.append(item_2[0])
                    temp.append(str(item))
                    for i in range(1, 11):
                        temp.append(str(item_2[i]))
                    temp.append(str(item_2[28]))
                    temp.append(str(item_2[11]))
                    for i in range(13, 19):
                        temp.append(str(item_2[i]))
                    temp.append(str(item_2[22]))
                    temp.append(str(item_2[23]))
                    temp.append(str(item_2[12]))
                    temp.append(str(item_2[19]))
                    response.append(temp)
        self.price_history = response
        return response

    def order(self, **kwargs):
        url = 'https://webtrading.ssi.com.vn/ajaxdata/Order.aspx'
        data = {
            'Type': 1,
            'StockSymbol': kwargs.get('stock', ''),
            'MarketName': kwargs.get('market_name', 'HOSE'),
            'OrderUnits': kwargs.get('units', ''),
            'OrderPrice': kwargs.get('price', ''),
            'PINCode': kwargs.get('pin', self.pin),
            'Side': kwargs.get('order', ''),
            'SavePINCode': 0,
            'Count': '',
            'DefaultAccountNo': kwargs.get('usr_num', self.user + '1'),
            'authenId': ''
        }
        response = self.session.post(url, data=data, headers=self.headers)
        response = json.loads(response.text)
        return response

    def get_all_cancel(self, **kwargs):
        url = 'https://webtrading.ssi.com.vn/ajaxdata/GetDataAllCancelOrderGroup.aspx'
        data = {
            'Channel': '',
            'Side': '',
            'Symbol': '',
            'listcond': 'pending,true|matched,true|semi,true|cancelling,true|cancelled,true|rejected,true',
            'AccountNoList': kwargs.get('usr_num', self.user + '1'),
        }
        rq = self.session.post(url, data=data, headers=self.headers)
        temp1 = json.loads(rq.text)[0]
        try:
            response = [[x[0], x[30]] for x in temp1]
        except:
            response = []
        return response

    def cancel_order(self, **kwargs):
        url = 'https://webtrading.ssi.com.vn/ajaxdata/ConfirmCancelGroup.aspx'
        data = {
            'idList': kwargs.get('id', ''),
            'orderPin': kwargs.get('pin', self.pin),
            'cancelType': 0,
            'listcond': 'pending,true|matched,true|semi,true|cancelling,true|cancelled,true|rejected,true',
            'AccountNoList': kwargs.get('usr_num', self.user + '1'),
            'Symbol': '',
            'PINCode': 0,
            'authenId': '',
        }
        response = self.session.post(url, data=data, headers=self.headers)
        return json.loads(response.text)

    def cancel_order_night(self, **kwargs):
        url = 'https://webtrading.ssi.com.vn/ajaxdata/ConfirmNOCancelGroup.aspx'
        data = {
            'idList': kwargs.get('id', ''),
            'orderPin': kwargs.get('pin', self.pin),
            'cancelType': 0,
            'listcond': 'pending,true|matched,true|semi,true|cancelling,true|cancelled,true|rejected,true',
            'AccountNoList': kwargs.get('usr_num', self.user + '1'),
            'Symbol': '',
            'PINCode': 0,
            'authenId': '',
        }
        response = self.session.post(url, data=data, headers=self.headers)
        return json.loads(response.text)

    def cancel_all(self):
        cancel_data = self.get_all_cancel()
        _ids = ','.join(x[0] for x in cancel_data)
        _user = ','.join(x[1] for x in cancel_data)

        if self.day_night:
            self.cancel_order(id=_ids, usr_num=_user)
            self.get_order_info()
        else:
            self.cancel_order_night(id=_ids, usr_num=_user)
            self.get_order_info_night()

    def get_order_info(self):
        url = 'https://webtrading.ssi.com.vn/ajaxdata/GetOrderInfo.aspx'
        data = {
            'channelId': '',
            'symbol': '',
            'side': '',
            'pagesize': 100,
            'pagestart': 1,
            'listcond': 'pending,true|matched,true|semi,true|cancelling,true|cancelled,true|rejected,true',
            'DefaultAccountNo': self.user + '1',
        }
        rq = self.session.post(url, data=data, headers=self.headers)
        temp1 = json.loads(rq.text)
        response = list()
        for item in temp1[1]:
            temp2 = list()
            temp2.append(temp1[1].index(item)+1)
            temp2.append(item[0])
            temp2.append(item[6])
            temp2.append('Mua') if item[2] == 'B' else temp2.append('Bán')
            temp2.append(item[3])
            temp2.append(item[4])
            temp2.append(item[5])
            if item[7] == '1':
                temp2.append('Đang chờ khớp')
            elif item[7] == '2':
                temp2.append('Khớp')
            elif item[7] == '3':
                temp2.append('Khớp 1 phần')
            elif item[7] == '4':
                temp2.append('Đang huỷ')
            elif item[7] == '5':
                temp2.append('Huỷ')
            response.append(temp2)
        self.order_history = response
        self.day_night = 1
        return response

    def get_order_info_night(self, **kwargs):
        url = 'https://webtrading.ssi.com.vn/ajaxdata/GetOrderInfoNight.aspx'
        data = {
            'channelId': '',
            'symbol': '',
            'side': '',
            'idList': '',
            'pagesize': 100,
            'pagestart': 1,
            'listcond': 'pending,true|matched,true|semi,true|cancelling,true|cancelled,true|rejected,true',
            'DefaultAccountNo': self.user + '1',
        }
        rq = self.session.post(url, data=data, headers=self.headers)
        temp1 = json.loads(rq.text)
        response = list()
        for item in temp1[1]:
            temp2 = list()
            temp2.append(item[1])
            temp2.append(item[0])
            temp2.append(item[6])
            temp2.append('Mua') if item[2] == 'B' else temp2.append('Bán')
            temp2.append(item[3])
            temp2.append(item[4])
            temp2.append(item[5])
            if item[8] == '1':
                temp2.append('Đang chờ khớp')
            elif item[8] == '2':
                temp2.append('Khớp')
            elif item[8] == '3':
                temp2.append('Khớp 1 phần')
            elif item[8] == '4':
                temp2.append('Đang huỷ')
            elif item[8] == '5':
                temp2.append('Huỷ')
            response.append(temp2)
        self.order_history = response
        self.day_night = 0
        return response
