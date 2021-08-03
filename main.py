from Process import *


if __name__ == '__main__':
    root = Tk()
    client = ThreadedClient(root)
    root.mainloop()
