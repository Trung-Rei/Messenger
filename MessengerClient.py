from tkinter import *
from tkinter import scrolledtext
from tkinter import messagebox
import socket
import threading

class LogIn:
    def __init__(self, login_func):
        self.func = login_func
        self.gui = None
        self.e_username = None
        self.e_password = None
        self.isLoggedIn = False

    def run(self):
        self.gui = Tk()
        self.gui.title('Log In')
        self.gui.resizable(False, False)

        l_username = Label(self.gui, text = 'UserName')
        l_username.grid(row = 0, column = 0, sticky = W)
        self.e_username = Entry(self.gui, width = 30)
        self.e_username.grid(row = 0, column = 1, sticky = W)
        
        l_password = Label(self.gui, text = 'Password')
        l_password.grid(row = 1, column = 0, sticky = W)
        self.e_password = Entry(self.gui, width = 30)
        self.e_password.grid(row = 1, column = 1, sticky = W)
        
        butt_login = Button(self.gui, text = 'Log In', command = self.login)
        butt_login.grid(row = 2, column = 1, sticky = W)

        self.gui.mainloop()
        return self.isLoggedIn

    def login(self):
        username = self.e_username.get()
        password = self.e_password.get()
        if self.func(username, password):
            self.isLoggedIn = True
            self.gui.destroy()
            return
        messagebox.showerror('Error', 'Incorrect username or password!')

class Messenger:
    def __init__(self, conn):
        self.s_send = conn
        self.s_recv = socket.socket()
        addr = self.s_send.recv(1024).decode()
        addr = addr.split(' ')
        self.s_recv.connect((addr[0], int(addr[1])))

        self.gui = None
        self.st_recv = None
        self.st_send = None

    def run(self):
        self.gui = Tk()
        self.gui.title('Chat')
        self.gui.resizable(False, False)

        self.st_recv = scrolledtext.ScrolledText(self.gui,
            wrap = WORD,
            width = 30,
            height = 20,
            font = ('consolas', 12))
        self.st_recv.grid(row = 0, column = 0)
        self.st_recv.configure(state = 'disabled')
        self.st_recv.tag_config('user', foreground = 'red')
        self.st_recv.tag_config('msg', foreground = 'blue')

        self.st_send = scrolledtext.ScrolledText(self.gui,
            wrap = WORD,
            width = 30,
            height = 3,
            font = ('consolas', 12))
        self.st_send.grid(row = 1, column = 0)
        self.st_send.focus()

        butt_send = Button(self.gui, text = 'Send', command = self.send_message_thread)
        butt_send.grid(row = 3, column = 0)

        t = threading.Thread(target=self.recv_message, args=())
        t.start()

        self.gui.protocol('WM_DELETE_WINDOW', self.close_window)

        self.gui.mainloop()

    def send_message_thread(self):
        t = threading.Thread(target=self.send_message, args=())
        t.start()

    def send_message(self):
        text = self.st_send.get('1.0', END)
        self.st_send.delete('1.0', END)
        if text == '\n':
            return
        self.s_send.send(b'TEXT ' + text.encode())
        self.s_send.recv(1024)

    def recv_message(self):
        while True:
            msg = self.s_recv.recv(1024).decode()
            self.s_recv.send(b'OK')
            msg = msg.split(' ', 1)
            
            self.st_recv.configure(state = 'normal')
            self.st_recv.insert(INSERT, msg[0] + ' ', 'user')
            self.st_recv.insert(INSERT, msg[1], 'msg')
            self.st_recv.configure(state = 'disabled')

            self.st_recv.see('end')

    def close_window(self):
        self.s_send.send(b'QUIT')
        self.gui.destroy()

class RoomList:
    def __init__(self, rooms):
        self.rooms = rooms

    def addRoom(self):
        pass

def main():
    host = '127.0.0.1'
    port = 6666

    s_send = socket.socket()
    s_send.connect((host, port))
    
    log_in = LogIn(login)
    if not log_in.run():
        return

    rooms = {}
    rlist = RoomList(rooms)
    # rooms['all'] = Messenger(s_send, rlist.addRoom)
    # rooms['all'].run()
    # 

    m = Messenger(s_send)
    m.run()

def login(username, password):
    if username == 'admin' and password == 'admin':
        return True
    return False

if __name__ == "__main__":
    main()