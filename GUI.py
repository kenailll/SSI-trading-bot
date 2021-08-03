import threading
from tkinter import ttk
from tkinter import *
from LoopOverFunc import *
from Proxies import Proxies
import json


class GuiPart:
    def __init__(self, master, process, endpoint, backend):
        self.master = master
        self.process = process
        self.end = endpoint
        self.backend = backend
        self.login_scr = None
        self.login = 0
        self.proxies_check = IntVar()
        self.parent_tab = ttk.Notebook(self.master)
        self.price_tab = ttk.Frame(self.parent_tab)
        self.parent_tab.add(self.price_tab, text='Price')
        self.price_tree = ttk.Treeview(self.price_tab)
        self.order_tab = ttk.Frame(self.parent_tab)
        self.parent_tab.add(self.order_tab, text='Order')
        self.order_tree = ttk.Treeview(self.order_tab)
        self.auto_tab = ttk.Frame(self.parent_tab)
        self.parent_tab.add(self.auto_tab, text='Auto tracking')
        self.auto_tree = ttk.Treeview(self.auto_tab)
        self.parent_tab.pack(expand=1, side=TOP, fill=BOTH)
        self.details_tree = ttk.Treeview(self.master)

    def main_screen(self, info):
        self.master.deiconify()
        self.master.title('SSI iBoard Bot 1.01 - %s - %s - %s' % (info[0], self.backend.user, info[1]))
        #details frame
        self.details_tree['show'] = 'headings'
        self.details_tree['columns'] = [0, 1]
        self.details_tree.heading(0, text='Thời gian')
        self.details_tree.heading(1, text='Thông báo')

        self.details_tree.column(0, width=120)
        self.details_tree.pack(expand=1, side=TOP, fill=BOTH)
        #price tab
        self.price_tree['show'] = 'headings'
        self.price_tree['columns'] = [i for i in range(24)]
        self.price_tree.column(0, width=40, anchor=CENTER)
        self.price_tree.column(1, width=40, anchor=CENTER)
        self.price_tree.column(2, width=35, anchor=CENTER)
        self.price_tree.column(3, width=35, anchor=CENTER)
        self.price_tree.column(4, width=35, anchor=CENTER)
        for i in range(5, 12):
            self.price_tree.column(i, width=60, anchor=CENTER)
        self.price_tree.column(12, width=40, anchor=CENTER)
        for i in range(13, 24):
            self.price_tree.column(i, width=60, anchor=CENTER)
        price_headers = ['Mã CK', 'Sàn', 'TC', 'Trần', 'Sàn', 'Giá mua 3', 'KL mua 3', 'Giá mua 2', 'KL mua 2',
                         'Giá mua 1',
                         'KL mua 1', 'Giá khớp', '+/-', 'KL Khớp', 'Giá bán 1', 'KL bán 1', 'Giá bán 2', 'KL bán 2',
                         'Giá bán 3', 'KL bán 3', 'NĐT NN Mua', 'NĐT NN Bán', 'KLGD', 'TB']
        for i in range(24):
            self.price_tree.heading(i, text=price_headers[i])
        self.price_tree.pack(expand=1, side=TOP, fill=BOTH)

        #order tab
        self.order_tree['show'] = 'headings'
        self.order_tree['columns'] = [i for i in range(8)]
        for i in range(8):
            self.order_tree.column(i, width=40, anchor=CENTER)

        order_headers = ['STT', 'ID', 'Thời gian', 'Bên', 'Mã CK', 'KL đặt', 'Giá đặt', 'Trạng thái']
        for i in range(8):
            self.order_tree.heading(i, text=order_headers[i])
        self.order_tree.pack(expand=1, side=TOP, fill=BOTH)

        def cancel_all():
            self.process.process_queue.put([self.backend.cancel_all])
            self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), 'Đã huỷ tất cả lệnh'])

        Button(self.order_tab, text=r'Huỷ tất cả', command=cancel_all).pack()

        #auto tab
        self.auto_tree['show'] = 'headings'
        self.auto_tree['columns'] = [i for i in range(9)]
        for i in range(9):
            self.auto_tree.column(i, width=40, anchor=CENTER)
        auto_headers = ['STT', 'Số tài khoản', 'Loại lệnh', 'Bên', 'Mã CK', 'KL đặt', 'Giá', 'Số lệnh', 'Trạng thái']
        for i in range(9):
            self.auto_tree.heading(i, text=auto_headers[i])
        self.auto_tree.pack(expand=1, side=TOP, fill=BOTH)

        self.master.protocol('WM_DELETE_WINDOW', self.end)

    def stock_click(self, event):
        item = self.price_tree.selection()
        try:
            self.bs_order(self.backend.user + '1', self.price_tree.item(item)['values'][0], self.price_tree.item(item)['values'][1])
        except:
            pass

    def order_click(self, event):
        item = self.order_tree.selection()
        try:
            self.process.process_queue.put([self.cancel_order, [self.order_tree.item(item)['values'][4], self.order_tree.item(item)['values'][1]]])
        except:
            pass

    def auto_ord_click(self, event):
        item = self.auto_tree.selection()
        try:
            if self.auto_tree.item(item)['values'][8] == 'Đang đặt lệnh':
                self.cancel_auto_order(self.auto_tree.item(item)['values'][0])
        except:
            pass

    def update_price(self, data):
        self.price_tree.delete(*self.price_tree.get_children())
        for item in data:
            self.price_tree.insert('', 'end', value=item)
            self.price_tree.bind('<Double-1>', self.stock_click)

    def update_order(self, data):
        self.order_tree.delete(*self.order_tree.get_children())
        for item in data:
            self.order_tree.insert('', 'end', value=item)
            self.order_tree.bind('<Double-1>', self.order_click)

    def update_auto(self, data):
        self.auto_tree.delete(*self.auto_tree.get_children())
        for item in data:
            self.auto_tree.insert('', 'end', value=item)
            self.auto_tree.bind('<Double-1>', self.auto_ord_click)

    def update_details(self, data):
        self.details_tree.insert(parent='', index=0, value=data)

    def login_screen(self, login_data):
        self.master.withdraw()
        self.login_scr = Toplevel(self.master)
        self.login_scr.geometry('450x270')
        self.login_scr.title('Account Login')
        self.login_scr.grid_columnconfigure((0, 2), weight=1)

        Label(self.login_scr, text='Nhập thông tin').grid(row=0, column=0, columnspan=2)
        Label(self.login_scr, text='').grid(row=1, column=0)

        def user_changed(event):
            clear()
            etr_pass.insert(0, login_data[str(etr_user.get())][0])
            etr_pin.insert(0, login_data[str(etr_user.get())][1])

        Label(self.login_scr, text='Username').grid(row=2, column=0)
        etr_user = ttk.Combobox(self.login_scr, value=list(login_data.keys()))
        etr_user.bind('<<ComboboxSelected>>', user_changed)
        try:
            etr_user.insert(0, list(login_data.keys())[0])
        except:
            pass
        etr_user.grid(row=2, column=1)

        Label(self.login_scr, text='Password * ').grid(row=3, column=0)
        etr_pass = Entry(self.login_scr, show='*')
        try:
            etr_pass.insert(0, login_data[str(etr_user.get())][0])
        except:
            pass
        etr_pass.grid(row=3, column=1)

        Label(self.login_scr, text='PIN * ').grid(row=4, column=0)
        etr_pin = Entry(self.login_scr, show='*')
        try:
            etr_pin.insert(0, login_data[str(etr_user.get())][1])
        except:
            pass
        etr_pin.grid(row=4, column=1)
        login_stt_var = StringVar()
        login_stt_var.set('')
        Label(self.login_scr, textvariable=login_stt_var).grid(row=5, column=0, columnspan=2)

        def clear():
            etr_pass.delete(0, 'end')
            etr_pin.delete(0, 'end')

        def login_form():
            if self.backend.headers == '':
                self.backend.get_headers()
            response = self.backend.login(username=str(etr_user.get()), password=str(etr_pass.get()), pin=str(etr_pin.get()))
            if response == '':
                self.process.process_queue.put([self.save_login])
                self.login_scr.destroy()
                self.login = 1
                self.main_screen(self.backend.info)
            else:
                login_stt_var.set(response)
                clear()

        Label(self.login_scr, text='')
        Button(self.login_scr, text=r'Nhập lại', command=clear).grid(row=6, column=0, sticky='nes')
        Button(self.login_scr, text=r'Đăng nhập', command=login_form).grid(row=6, column=1, sticky='ns')

        px = Proxies()
        proxies_tree = ttk.Treeview(self.login_scr)
        proxies_tree['show'] = 'headings'
        proxies_tree['columns'] = [0]
        proxies_tree.heading(0, text='Proxies')
        proxies_tree.grid(row=1, column=2, rowspan=6, sticky='n')

        def proxy_select(event):
            item = proxies_tree.selection()
            proxy = proxies_tree.item(item)['values'][0]
            if proxy != 'No proxies':
                self.backend.proxy_set(px.get_proxies(proxy))

        proxies_tree.insert('', 'end', value='"No proxies"')
        for item in px.proxies:
            proxies_tree.insert('', 'end', value=item)
        proxies_tree.bind('<<TreeviewSelect>>', proxy_select)

        self.login_scr.protocol('WM_DELETE_WINDOW', self.end)

    def bs_order(self, user, stock, market):
        bs_scr = Toplevel(self.master)
        bs_scr.title(r'Đặt lệnh')
        parent_tab = ttk.Notebook(bs_scr)
        manual_tab = ttk.Frame(parent_tab)

        variable = IntVar()
        def ord_type_units():
            if not variable.get():
                entry_min1.delete(0, 'end')
                entry_min1.insert(0, [a for a in self.backend.price_history if stock in a][0][10])
                entry_min2.delete(0, 'end')
                entry_min2.insert(0, [a for a in self.backend.price_history if stock in a][0][8])
                entry_min3.delete(0, 'end')
                entry_min3.insert(0, [a for a in self.backend.price_history if stock in a][0][6])
            else:
                entry_min1.delete(0, 'end')
                entry_min1.insert(0, [a for a in self.backend.price_history if stock in a][0][15])
                entry_min2.delete(0, 'end')
                entry_min2.insert(0, [a for a in self.backend.price_history if stock in a][0][17])
                entry_min3.delete(0, 'end')
                entry_min3.insert(0, [a for a in self.backend.price_history if stock in a][0][19])

        #manual tab
        parent_tab.add(manual_tab, text='Bằng tay')

        Label(manual_tab, text='Số tài khoản').grid(row=0, column=0)
        etr_user_num = Entry(manual_tab)
        etr_user_num.insert(0, user)
        etr_user_num.grid(row=0, column=1)

        Label(manual_tab, text='Loại lệnh').grid(row=1, column=0)
        etr_order_b = Radiobutton(manual_tab, text='Mua', variable=variable, value=0, command=ord_type_units)
        etr_order_b.grid(row=1, column=1)
        etr_order_s = Radiobutton(manual_tab, text='Bán', variable=variable, value=1, command=ord_type_units)
        etr_order_s.grid(row=1, column=2)

        Label(manual_tab, text='Mã chứng khoán').grid(row=2, column=0)
        etr_stock = Entry(manual_tab)
        etr_stock.insert(0, stock)
        etr_stock.grid(row=2, column=1)

        Label(manual_tab, text='Tổng khối lượng').grid(row=3, column=0)
        etr_total_units = Entry(manual_tab)
        etr_total_units.grid(row=3, column=1)

        Label(manual_tab, text='KL mỗi lệnh').grid(row=3, column=2)
        etr_units = Entry(manual_tab)
        etr_units.grid(row=3, column=3)

        Label(manual_tab, text='Giá').grid(row=4, column=0)
        etr_price = Entry(manual_tab)
        etr_price.grid(row=4, column=1)

        Label(manual_tab, text='Thời gian (giây)').grid(row=5, column=0)
        etr_time = Entry(manual_tab)
        etr_time.grid(row=5, column=1)

        def ord_form():
            if not variable.get():
                ord_type = 'B'
            else:
                ord_type = 'S'
            manual_scr = self.temp_order()
            manual_order = LoopOverFunc(master=manual_scr, process=self.process, time=float(etr_time.get()), backend=self.backend,
                                        total_units=int(etr_total_units.get()), user_num=str(etr_user_num.get()),
                                        stock=str(etr_stock.get()), units=int(etr_units.get()), price=str(etr_price.get()),
                                        market_name=market, order=ord_type)
            self.process.auto_order.append(manual_order)
            bs_scr.destroy()

        Button(manual_tab, text=r'Đặt', command=ord_form).grid(row=7, column=1)

        #auto tab
        auto_tab = ttk.Frame(parent_tab)
        parent_tab.add(auto_tab, text='Tự động')

        Label(auto_tab, text='Số tài khoản').grid(row=0, column=0)
        entry_user_num = Entry(auto_tab, width=10)
        entry_user_num.insert(0, user)
        entry_user_num.grid(row=0, column=1)

        Label(auto_tab, text='Mã chứng khoán').grid(row=1, column=0)
        entry_stock = Entry(auto_tab, width=10)
        entry_stock.insert(0, stock)
        entry_stock.grid(row=1, column=1)

        Label(auto_tab, text='Tổng KL1').grid(row=2, column=0)
        entry_total_units_1 = Entry(auto_tab, width=10)
        entry_total_units_1.insert(0, 100)
        entry_total_units_1.grid(row=2, column=1)
        Label(auto_tab, text='Tổng KL2').grid(row=3, column=0)
        entry_total_units_2 = Entry(auto_tab, width=10)
        entry_total_units_2.insert(0, 300)
        entry_total_units_2.grid(row=3, column=1)
        Label(auto_tab, text='Tổng KL3').grid(row=4, column=0)
        entry_total_units_3 = Entry(auto_tab, width=10)
        entry_total_units_3.insert(0, 1000)
        entry_total_units_3.grid(row=4, column=1)

        Label(auto_tab, text='KL mỗi lệnh').grid(row=2, column=2)
        entry_kl1 = Entry(auto_tab, width=10)
        entry_kl1.insert(0, 100)
        entry_kl1.grid(row=2, column=3)
        Label(auto_tab, text='KL mỗi lệnh').grid(row=3, column=2)
        entry_kl2 = Entry(auto_tab, width=10)
        entry_kl2.insert(0, 100)
        entry_kl2.grid(row=3, column=3)
        Label(auto_tab, text='KL mỗi lệnh').grid(row=4, column=2)
        entry_kl3 = Entry(auto_tab, width=10)
        entry_kl3.insert(0, 100)
        entry_kl3.grid(row=4, column=3)

        Label(auto_tab, text='ĐK').grid(row=2, column=4)
        entry_mimax1 = ttk.Combobox(auto_tab, value=['>=', '<='], width=3)
        entry_mimax1.insert(0, '>=')
        entry_mimax1.grid(row=2, column=5)
        entry_min1 = Entry(auto_tab, width=10)
        entry_min1.grid(row=2, column=6)
        Label(auto_tab, text='ĐK').grid(row=3, column=4)
        entry_mimax2 = ttk.Combobox(auto_tab, value=['>=', '<='], width=3)
        entry_mimax2.insert(0, '>=')
        entry_mimax2.grid(row=3, column=5)
        entry_min2 = Entry(auto_tab, width=10)
        entry_min2.grid(row=3, column=6)
        Label(auto_tab, text='ĐK').grid(row=4, column=4)
        entry_mimax3 = ttk.Combobox(auto_tab, value=['>=', '<='], width=3)
        entry_mimax3.insert(0, '>=')
        entry_mimax3.grid(row=4, column=5)
        entry_min3 = Entry(auto_tab, width=10)
        entry_min3.grid(row=4, column=6)
        self.process.process_queue.put([ord_type_units])

        Label(auto_tab, text='Thời gian (giây)').grid(row=2, column=7)
        entry_time1 = Entry(auto_tab, width=4)
        entry_time1.insert(0, 30)
        entry_time1.grid(row=2, column=8)
        Label(auto_tab, text='Thời gian (giây)').grid(row=3, column=7)
        entry_time2 = Entry(auto_tab, width=4)
        entry_time2.insert(0, 30)
        entry_time2.grid(row=3, column=8)
        Label(auto_tab, text='Thời gian (giây)').grid(row=4, column=7)
        entry_time3 = Entry(auto_tab, width=4)
        entry_time3.insert(0, 30)
        entry_time3.grid(row=4, column=8)

        Label(auto_tab, text='Loại lệnh').grid(row=5, column=0)
        entry_order_b = Radiobutton(auto_tab, text='Mua', variable=variable, value=0, command=ord_type_units)
        entry_order_b.grid(row=5, column=1)
        entry_order_s = Radiobutton(auto_tab, text='Bán', variable=variable, value=1, command=ord_type_units)
        entry_order_s.grid(row=5, column=2)

        var1 = IntVar()
        Label(auto_tab, text='Huỷ theo thị trường').grid(row=5, column=3)
        entry_cancel = Checkbutton(auto_tab, variable=var1, onvalue=1, offvalue=0)
        entry_cancel.grid(row=5, column=4)

        def auto1():
            if not variable.get():
                ord_type = 'B'
                cond1 = 10
                cond2 = 8
                cond3 = 6
            else:
                ord_type = 'S'
                cond1 = 15
                cond2 = 17
                cond3 = 19

            if var1.get():
                if int(int(entry_kl1.get())/100):
                    auto_scr_1 = self.temp_order()
                    auto_order_1 = LoopWithCond(master=auto_scr_1, process=self.process, time=float(entry_time1.get()),
                                                backend=self.backend, cond0=str(entry_mimax1.get()), cond1=cond1,
                                                total_units=int(entry_total_units_1.get()), user_num=str(entry_user_num.get()),
                                                stock=str(entry_stock.get()), market_name=market, units=int(entry_kl1.get()),
                                                order=ord_type, mimax=int(entry_min1.get()))
                    self.process.auto_order.append(auto_order_1)

                if int(int(entry_kl2.get())/100):
                    auto_scr_2 = self.temp_order()
                    auto_order_2 = LoopWithCond(master=auto_scr_2, process=self.process, time=float(entry_time2.get()),
                                                backend=self.backend, cond0=str(entry_mimax2.get()), cond1=cond2,
                                                total_units=int(entry_total_units_2.get()), user_num=str(entry_user_num.get()),
                                                stock=str(entry_stock.get()), market_name=market, units=int(entry_kl2.get()),
                                                order=ord_type, mimax=int(entry_min2.get()))
                    self.process.auto_order.append(auto_order_2)

                if int(int(entry_kl3.get())/100):
                    auto_scr_3 = self.temp_order()
                    auto_order_3 = LoopWithCond(master=auto_scr_3, process=self.process, time=float(entry_time3.get()),
                                                backend=self.backend, cond0=str(entry_mimax3.get()), cond1=cond3,
                                                total_units=int(entry_total_units_3.get()), user_num=str(entry_user_num.get()),
                                                stock=str(entry_stock.get()), market_name=market, units=int(entry_kl3.get()),
                                                order=ord_type, mimax=int(entry_min3.get()))
                    self.process.auto_order.append(auto_order_3)
            else:
                if int(int(entry_kl1.get()) / 100):
                    auto_scr_1 = self.temp_order()
                    auto_order_1 = LoopWithCond2(master=auto_scr_1, process=self.process, time=float(entry_time1.get()),
                                                backend=self.backend, cond0=str(entry_mimax1.get()), cond1=cond1,
                                                total_units=int(entry_total_units_1.get()),
                                                user_num=str(entry_user_num.get()),
                                                stock=str(entry_stock.get()), market_name=market,
                                                units=int(entry_kl1.get()),
                                                order=ord_type, mimax=int(entry_min1.get()))
                    self.process.auto_order.append(auto_order_1)

                if int(int(entry_kl2.get()) / 100):
                    auto_scr_2 = self.temp_order()
                    auto_order_2 = LoopWithCond2(master=auto_scr_2, process=self.process, time=float(entry_time2.get()),
                                                backend=self.backend, cond0=str(entry_mimax2.get()), cond1=cond2,
                                                total_units=int(entry_total_units_2.get()),
                                                user_num=str(entry_user_num.get()),
                                                stock=str(entry_stock.get()), market_name=market,
                                                units=int(entry_kl2.get()),
                                                order=ord_type, mimax=int(entry_min2.get()))
                    self.process.auto_order.append(auto_order_2)

                if int(int(entry_kl3.get()) / 100):
                    auto_scr_3 = self.temp_order()
                    auto_order_3 = LoopWithCond2(master=auto_scr_3, process=self.process, time=float(entry_time3.get()),
                                                backend=self.backend, cond0=str(entry_mimax3.get()), cond1=cond3,
                                                total_units=int(entry_total_units_3.get()),
                                                user_num=str(entry_user_num.get()),
                                                stock=str(entry_stock.get()), market_name=market,
                                                units=int(entry_kl3.get()),
                                                order=ord_type, mimax=int(entry_min3.get()))
                    self.process.auto_order.append(auto_order_3)

            bs_scr.destroy()

        def thread_auto():
            self.process.process_queue.put([auto1])

        Button(auto_tab, text=r'Đặt', command=thread_auto).grid(row=6, column=5)
        parent_tab.pack(expand=1, fill='both')
        bs_scr.protocol('WM_DELETE_WINDOW', bs_scr.destroy)

    def temp_order(self):
        temp_scr = Toplevel(self.master)
        temp_scr.withdraw()
        return temp_scr

    def cancel_order(self, stock, order_id, user_num):
        if self.backend.day_night:
            cancel = self.backend.cancel_order(id=order_id, usr_num=user_num)
        else:
            cancel = self.backend.cancel_order_night(id=order_id, usr_num=user_num)
        self.process.details_queue.put([t.strftime('%d/%m/%Y %H:%M:%S'), 'Huỷ lệnh %s id %d: Response: %s' % (stock, order_id, cancel)])
        return 0

    def cancel_auto_order(self, order):
        self.process.auto_order[int(order)-1].end()
        return 0

    def get_saved_login(self):
        with open('save.json', 'r') as f:
            return json.load(f)

    def save_login(self):
        with open('save.json', 'r+') as f:
            try:
                data = json.load(f)
            except:
                data = {}
            data[self.backend.user] = [self.backend.pwd, self.backend.pin]
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=4)
