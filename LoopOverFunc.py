import queue
import time as t
from datetime import date
import threading


class LoopOverFunc:
    def __init__(self, master, process, time, backend, total_units, **kwargs):
        self.queue = queue.Queue()
        self.master = master
        self.process = process
        self.kwargs = kwargs
        self.name = 'Bằng tay'
        self.order_count = 0
        self.status = 1
        self.time = int(time * 1000)
        self.backend = backend
        self.total_ord = int(total_units / self.kwargs['units'])
        self.worker(self.total_ord)
        self.loop_call()

    def loop_call(self):
        if self.queue.qsize():
            data = self.queue.get()
            try:
                response = self.backend.order(**self.kwargs)
                temp = 'Mua' if self.kwargs.get('order') == 'B' else 'Bán'
                self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), '%s %s giá %s lệnh %d:  Response: %s' %
                                                (temp, self.kwargs.get('stock', ''), self.kwargs.get('price', ''), data, response)])
                if response[1] == '1':
                    self.order_count += 1
                else:
                    self.queue.put(data)
            except:
                pass
        else:
            if self.order_count == self.total_ord:
                self.status = 2
            else:
                self.status = 0
            try:
                self.master.after_cancel(self.loop)
            except:
                pass
            self.master.destroy()
            return 0
        self.loop = self.master.after(self.time, self.loop_call)

    def worker(self, times):
        if self.kwargs['order'] == 'B':
            order_type = 'mua'
        else:
            order_type = 'bán'
        self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'),
                                        'Bạn đã đặt %d lệnh %s %s giá %s' % (
                                            times, order_type, self.kwargs['stock'], self.kwargs['price'])])
        for time in range(times):
            self.queue.put(time + 1)

    def end(self):
        if self.order_count == self.total_ord:
            self.status = 2
        else:
            self.status = 0
        try:
            self.master.after_cancel(self.loop)
            self.master.destroy()

            if self.kwargs['order'] == 'B':
                order_type = 'mua'
            else:
                order_type = 'bán'
            self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), 'Bạn đã huỷ %d lệnh %s %s giá %s' %
                                            (self.total_ord - self.order_count, order_type, self.kwargs['stock'],
                                             self.kwargs['price'])])
        except:
            pass


class LoopWithCond:
    def __init__(self, master, process, time, backend, cond0, cond1, total_units, **kwargs):
        self.queue = queue.Queue()
        self.master = master
        self.process = process
        self.kwargs = kwargs
        self.running = 1
        self.name = 'Tự động'
        self.ord_id_list = []
        self.time = int(time * 1000)
        self.backend = backend
        self.cond0 = cond0
        self.cond1 = cond1
        self.tag = {6: 'Giá 3', 8: 'Giá 2', 10: 'Giá 1', 15: 'Giá 1', 17: 'Giá 2', 19: 'Giá 3'}
        self.order_count = 0
        self.status = 1
        self.total_ord = int(total_units/self.kwargs['units'])
        self.price_check = [a for a in self.backend.price_history if self.kwargs['stock'] in a][0][self.cond1 - 1]
        self.worker(self.total_ord)
        self.loop_call()
        thread = threading.Thread(target=self.price_change)
        thread.start()

    def loop_call(self):
        if self.queue.qsize():
            self.kwargs['price'] = [a for a in self.backend.price_history if self.kwargs['stock'] in a][0][self.cond1 - 1]
            data = self.queue.get()

            try:
                market_units = int([a for a in self.backend.price_history if self.kwargs['stock'] in a][0][self.cond1])
            except:
                market_units = 0

            try:
                temp = [a for a in self.backend.order_history
                        if (self.kwargs['stock'] in a)
                        and (a[7] == 'Khớp 1 phần' or a[7] == 'Đang chờ khớp')
                        and (self.kwargs['price'] == a[6])
                        and (self.kwargs['order'] == a[3])
                        ]
                indiv_units = sum(int(a[5]) for a in temp)
            except:
                indiv_units = 0

            if self.cond0 == '>=':
                if market_units + indiv_units >= self.kwargs['mimax']:
                    try:
                        response = self.backend.order(**self.kwargs)
                        ord_time = int(t.time())
                        if response[1] == '1':
                            try:
                                self.backend.get_order_info()
                            except:
                                self.backend.get_order_info_night()
                            self.ord_id_list.extend([a[1] for a in self.backend.order_history
                                                     if (ord_time <= int(t.mktime(
                                    t.strptime(str(date.today()) + a[2], '%Y-%m-%d%H:%M:%S'))) <= ord_time + 5)
                                                     and (a[4] == self.kwargs.get('stock', ''))
                                                     and (a[6] == self.kwargs.get('price', ''))])
                            self.order_count += 1
                        else:
                            self.queue.put(data)
                        temp = 'Mua' if self.kwargs.get('order') == 'B' else 'Bán'
                        self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), '%s %s %s lệnh %d:  Response: %s'
                                                        % (temp, self.kwargs.get('stock', ''), self.tag[self.cond1], data, response)])
                    except:
                        pass
                else:
                    temp = 'Mua' if self.kwargs.get('order') == 'B' else 'Bán'
                    self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), '%s %s %s lệnh %d:  Response: Khối lượng giao dịch trên sàn thấp hơn giá trị mong muốn'
                                                    % (temp, self.kwargs.get('stock', ''), self.tag[self.cond1], data)])
                    self.queue.put(data)
            else:
                if market_units + indiv_units <= self.kwargs['mimax']:
                    try:
                        response = self.backend.order(**self.kwargs)
                        ord_time = int(t.time())
                        if response[1] == '1':
                            try:
                                self.backend.get_order_info()
                            except:
                                self.backend.get_order_info_night()
                            self.ord_id_list.extend([a[1] for a in self.backend.order_history
                                                     if (ord_time <= int(t.mktime(t.strptime(str(date.today()) + a[2], '%Y-%m-%d%H:%M:%S'))) <= ord_time + 5)
                                                     and (a[4] == self.kwargs.get('stock', ''))
                                                     and (a[6] == self.kwargs.get('price', ''))])
                            self.order_count += 1
                        else:
                            self.queue.put(data)

                        temp = 'Mua' if self.kwargs.get('order') == 'B' else 'Bán'
                        self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), '%s %s %s lệnh %d:  Response: %s'
                                                        % (temp, self.kwargs.get('stock', ''), self.tag[self.cond1], data, response)])
                    except:
                        pass
                else:
                    temp = 'Mua' if self.kwargs.get('order') == 'B' else 'Bán'
                    self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), '%s %s %s lệnh %d:  Response: Khối lượng giao dịch trên sàn vượt quá giá trị mong muốn'
                                                    % (temp, self.kwargs.get('stock', ''), self.tag[self.cond1], data)])
                    self.queue.put(data)
        else:
            self.kwargs['price'] = [a for a in self.backend.price_history if self.kwargs['stock'] in a][0][self.cond1 - 1]
            order_status = [x for x in self.backend.order_history if
                            ((x[1] in self.ord_id_list) and (x[7] == r'Đang chờ khớp'))]

            if not order_status:
                self.running = 0
                if self.order_count == self.total_ord:
                    self.status = 2
                else:
                    self.status = 0
                try:
                    self.master.after_cancel(self.loop)
                except:
                    pass
                self.master.destroy()
                return 0
            else:
                pass
        self.loop = self.master.after(self.time, self.loop_call)

    def worker(self, times):
        order_type = 'mua' if self.kwargs['order'] == 'B' else 'bán'
        self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), 'Bạn đã đặt %d lệnh %s %s giá %s'
                                        % (times, order_type, self.kwargs['stock'], self.price_check)])
        for time in range(times):
            self.queue.put(time + 1)

    def end(self):
        self.running = 0
        if self.order_count == self.total_ord:
            self.status = 2
        else:
            self.status = 0

        try:
            self.master.after_cancel(self.loop)
            self.master.destroy()

            if self.kwargs['order'] == 'B':
                order_type = 'mua'
            else:
                order_type = 'bán'
            self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), 'Bạn đã huỷ %d lệnh %s %s giá %s'
                                            % (self.total_ord - self.order_count, order_type, self.kwargs['stock'],
                                               self.kwargs['price'])])
        except:
            pass

    def reset(self, total_ord):
        try:
            self.master.after_cancel(self.loop)
        except:
            pass
        id_ = ','.join(self.ord_id_list)
        user_ = ','.join([self.kwargs['user_num'] for x in range(len(self.ord_id_list))])
        if self.backend.day_night:
            self.backend.cancel_order(id=id_, usr_num=user_)
        else:
            self.backend.cancel_order_night(id=id_, usr_num=user_)
        if self.kwargs['order'] == 'B':
            order_type = 'mua'
        else:
            order_type = 'bán'
        self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), 'Huỷ %d lệnh %s %s giá %s do thị trường thay đổi'
                                        % (self.order_count, order_type, self.kwargs['stock'],
                                           self.kwargs['price'])])
        self.order_count = 0
        with self.queue.mutex:
            self.queue.queue.clear()
        self.worker(total_ord)

    def price_change(self):
        while self.running:
            self.kwargs['price'] = [a for a in self.backend.price_history if self.kwargs['stock'] in a][0][self.cond1 - 1]
            if self.kwargs['price'] != self.price_check:
                self.price_check = self.kwargs['price']
                order_status = [x for x in self.backend.order_history if((x[1] in self.ord_id_list) and (x[7] == r'Khớp'))]
                self.reset(self.total_ord - len(order_status))
                self.loop_call()
            if not self.running:
                return 0


class LoopWithCond2:
    def __init__(self, master, process, time, backend, cond0, cond1, total_units, **kwargs):
        self.queue = queue.Queue()
        self.master = master
        self.process = process
        self.kwargs = kwargs
        self.running = 1
        self.name = 'Tự động'
        self.time = int(time * 1000)
        self.backend = backend
        self.cond0 = cond0
        self.cond1 = cond1
        self.tag = {6: 'Giá 3', 8: 'Giá 2', 10: 'Giá 1', 15: 'Giá 1', 17: 'Giá 2', 19: 'Giá 3'}
        self.order_count = 0
        self.status = 1
        self.total_ord = int(total_units/self.kwargs['units'])
        self.price_check = [a for a in self.backend.price_history if self.kwargs['stock'] in a][0][self.cond1 - 1]
        self.worker(self.total_ord)
        self.loop_call()
        thread = threading.Thread(target=self.price_change)
        thread.start()

    def loop_call(self):
        if self.queue.qsize():
            self.kwargs['price'] = [a for a in self.backend.price_history if self.kwargs['stock'] in a][0][self.cond1 - 1]
            data = self.queue.get()

            try:
                market_units = int([a for a in self.backend.price_history if self.kwargs['stock'] in a][0][self.cond1])
            except:
                market_units = 0

            try:
                temp = [a for a in self.backend.order_history
                        if (self.kwargs['stock'] in a)
                        and (a[7] == 'Khớp 1 phần' or a[7] == 'Đang chờ khớp')
                        and (self.kwargs['price'] == a[6])
                        and (self.kwargs['order'] == a[3])
                        ]
                indiv_units = sum(int(a[5]) for a in temp)
            except:
                indiv_units = 0

            if self.cond0 == '>=':
                if market_units + indiv_units >= self.kwargs['mimax']:
                    try:
                        response = self.backend.order(**self.kwargs)
                        if response[1] == '1':
                            try:
                                self.backend.get_order_info()
                            except:
                                self.backend.get_order_info_night()
                            self.order_count += 1
                        else:
                            self.queue.put(data)
                        temp = 'Mua' if self.kwargs.get('order') == 'B' else 'Bán'
                        self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), '%s %s %s lệnh %d:  Response: %s'
                                                        % (temp, self.kwargs.get('stock', ''), self.tag[self.cond1], data, response)])
                    except:
                        pass
                else:
                    temp = 'Mua' if self.kwargs.get('order') == 'B' else 'Bán'
                    self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), '%s %s %s lệnh %d:  Response: Khối lượng giao dịch trên sàn thấp hơn giá trị mong muốn'
                                                    % (temp, self.kwargs.get('stock', ''), self.tag[self.cond1], data)])
                    self.queue.put(data)
            else:
                if market_units + indiv_units <= self.kwargs['mimax']:
                    try:
                        response = self.backend.order(**self.kwargs)
                        if response[1] == '1':
                            try:
                                self.backend.get_order_info()
                            except:
                                self.backend.get_order_info_night()
                            self.order_count += 1
                        else:
                            self.queue.put(data)

                        temp = 'Mua' if self.kwargs.get('order') == 'B' else 'Bán'
                        self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), '%s %s %s lệnh %d:  Response: %s'
                                                        % (temp, self.kwargs.get('stock', ''), self.tag[self.cond1], data, response)])
                    except:
                        pass
                else:
                    temp = 'Mua' if self.kwargs.get('order') == 'B' else 'Bán'
                    self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), '%s %s %s lệnh %d:  Response: Khối lượng giao dịch trên sàn vượt quá giá trị mong muốn'
                                                    % (temp, self.kwargs.get('stock', ''), self.tag[self.cond1], data)])
                    self.queue.put(data)
        else:
            self.running = 0
            if self.order_count == self.total_ord:
                self.status = 2
            else:
                self.status = 0
            try:
                self.master.after_cancel(self.loop)
            except:
                pass
            self.master.destroy()
            return 0
        self.loop = self.master.after(self.time, self.loop_call)

    def worker(self, times):
        order_type = 'mua' if self.kwargs['order'] == 'B' else 'bán'
        self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), 'Bạn đã đặt %d lệnh %s %s giá %s'
                                        % (times, order_type, self.kwargs['stock'], self.price_check)])
        for time in range(times):
            self.queue.put(time + 1)

    def end(self):
        self.running = 0
        if self.order_count == self.total_ord:
            self.status = 2
        else:
            self.status = 0

        try:
            self.master.after_cancel(self.loop)
            self.master.destroy()

            if self.kwargs['order'] == 'B':
                order_type = 'mua'
            else:
                order_type = 'bán'
            self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), 'Bạn đã huỷ %d lệnh %s %s giá %s'
                                            % (self.total_ord - self.order_count, order_type, self.kwargs['stock'],
                                               self.kwargs['price'])])
        except:
            pass

    def reset(self, total_ord):
        try:
            self.master.after_cancel(self.loop)
        except:
            pass
        with self.queue.mutex:
            self.queue.queue.clear()
        self.worker(total_ord)

    def price_change(self):
        while self.running:
            self.kwargs['price'] = [a for a in self.backend.price_history if self.kwargs['stock'] in a][0][self.cond1 - 1]
            if self.kwargs['price'] != self.price_check:
                self.price_check = self.kwargs['price']
                self.reset(self.total_ord - self.order_count)
                self.loop_call()
            if not self.running:
                return 0