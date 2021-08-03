from GUI import *
from ssi_rq import *
import queue
import threading


class ThreadedClient:
    def __init__(self, master):
        self.master = master
        self.price_queue = queue.Queue()
        self.order_queue = queue.Queue()
        self.auto_queue = queue.Queue()
        self.process_queue = queue.Queue()
        self.details_queue = queue.Queue()

        self.old_price = []
        self.old_order = []
        self.old_auto = []

        self.auto_order = []

        self.request = Request()

        self.gui = GuiPart(master, self, self.end_app, self.request)
        self.gui.login_screen(self.gui.get_saved_login())
        self.running = 1
        self.thread1 = threading.Thread(target=self.worker)
        self.thread1.start()

        self.period_call()

    def period_call(self):
        if self.process_queue.qsize():
            func = self.process_queue.get(0)
            try:
                func[0](*func[1])
            except:
                func[0]()

        if self.price_queue.qsize():
            self.price_queue.get(0)
            if self.old_price != self.request.price_history:
                self.old_price = self.request.price_history
                self.gui.update_price(self.request.price_history)

        if self.order_queue.qsize():
            self.order_queue.get(0)
            if self.old_order != self.request.order_history:
                self.old_order = self.request.order_history
                self.gui.update_order(self.request.order_history)

        if self.auto_queue.qsize():
            adata = self.auto_queue.get(0)
            if adata:
                if self.old_auto != adata:
                    self.old_auto = adata
                    self.gui.update_auto(adata)

        if self.details_queue.qsize():
            self.gui.update_details(self.details_queue.get(0))

        if not self.running:
            import sys
            sys.exit(1)
        self.master.after(100, self.period_call)

    def worker(self):
        while self.running:
            if self.gui.login:
                lst_stock = self.request.get_fav_list_stock()
                if not lst_stock:
                    self.gui.login = 0
                    self.gui.login_scr = None
                    self.request.session.cookies.clear()
                else:
                    try:
                        self.request.get_price(lst_stock)
                        self.price_queue.put(1)
                        try:
                            self.request.get_order_info()
                            self.order_queue.put(1)
                        except:
                            self.request.get_order_info_night()
                            self.order_queue.put(1)
                        self.auto_queue.put(self.auto_order_data())
                    except:
                        pass
            else:
                if not self.gui.login_scr:
                    self.gui.login_screen(self.gui.get_saved_login())

    def auto_order_data(self):
        if self.auto_order:
            data = []
            for item in self.auto_order:
                temp = list()
                temp.append(self.auto_order.index(item)+1)
                temp.append(item.kwargs['user_num'])
                temp.append(item.name)
                temp.append('Mua') if item.kwargs['order'] == 'B' else temp.append('Bán')
                temp.append(item.kwargs['stock'])
                temp.append(item.kwargs['units'])
                try:
                    temp.append(item.price_check)
                except:
                    temp.append(item.kwargs['price'])
                temp.append('%d/%d' % (item.order_count, item.total_ord))
                if item.status == 0:
                    temp.append('Đã huỷ')
                elif item.status == 1:
                    temp.append('Đang đặt lệnh')
                elif item.status == 2:
                    temp.append('Đã hoàn thành')
                data.append(temp)
            return data

    def end_app(self):
        for item in self.auto_order:
            item.end()
        self.running = 0
