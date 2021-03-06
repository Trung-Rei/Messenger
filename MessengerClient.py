from tkinter import *
from tkinter import scrolledtext
from tkinter import messagebox
from tkinter import filedialog
import socket
import threading
import os

class SignUp:
    """
    this class handles sign up function
    """

    def __init__(self, s_send):
        self.s_send = s_send
        self.gui = Tk()
        self.gui.title('Sign Up')
        self.gui.resizable(False, False)

        # initilize the gui
        l_username = Label(self.gui, text = 'UserName')
        l_username.grid(row = 0, column = 0, sticky = W)
        self.e_username = Entry(self.gui, width = 30)
        self.e_username.grid(row = 0, column = 1, sticky = W)
        
        l_password = Label(self.gui, text = 'Password')
        l_password.grid(row = 1, column = 0, sticky = W)
        self.e_password = Entry(self.gui, width = 30, show = '*')
        self.e_password.grid(row = 1, column = 1, sticky = W)
        
        butt_login = Button(self.gui, text = 'Sign Up', command = self.signup)
        butt_login.grid(row = 2, column = 1, sticky = W)

        self.gui.protocol('WM_DELETE_WINDOW', self.close_window)

    def run(self):
        self.s_send.send(b'SIGNUP')
        self.gui.mainloop()

    def signup(self):
        if self.signupFunc():
            self.gui.destroy()
            return
        messagebox.showerror('Error', 'Username has already been taken!')

    def signupFunc(self):
        """
        return True if successfully sign up
        """

        username = self.e_username.get()
        password = self.e_password.get()
        self.s_send.send(username.encode() + b'\n' + password.encode())
        if self.s_send.recv(1024) == b'OK':
            return True
        return False

    def close_window(self):
        self.s_send.send(b'QUIT')
        self.gui.destroy()

class LogIn:
    """this class handles log in function"""

    def __init__(self, s_send):
        self.s_send = s_send
        self.username = ''
        self.gui = Tk()
        self.gui.title('Log In')
        self.gui.resizable(False, False)

        # initilize the gui
        l_username = Label(self.gui, text = 'UserName')
        l_username.grid(row = 0, column = 0, sticky = W)
        self.e_username = Entry(self.gui, width = 30)
        self.e_username.grid(row = 0, column = 1, sticky = W, columnspan = 2)
        
        l_password = Label(self.gui, text = 'Password')
        l_password.grid(row = 1, column = 0, sticky = W)
        self.e_password = Entry(self.gui, width = 30, show = '*')
        self.e_password.grid(row = 1, column = 1, sticky = W, columnspan = 2)
        
        butt_login = Button(self.gui, text = 'Log In', command = self.login)
        butt_login.grid(row = 2, column = 1, sticky = W)

        butt_signup = Button(self.gui, text = 'Sign Up', command = self.signup)
        butt_signup.grid(row = 2, column = 2, sticky = W)

        self.gui.protocol('WM_DELETE_WINDOW', self.close_window)

    def run(self):
        """return the username that has been logged in,
        return empty string if user exit"""

        self.s_send.send(b'LOGIN')
        self.gui.mainloop()
        return self.username

    def login(self):
        self.username = self.loginFunc()
        if self.username != '':
            self.gui.destroy()
            return
        messagebox.showerror('Error', 'Incorrect username or password\
            \nor user has already logged in!')

    def loginFunc(self):
        """return username if log in successful, else return empty string"""

        username = self.e_username.get()
        password = self.e_password.get()
        self.s_send.send(username.encode() + b'\n' + password.encode())
        if self.s_send.recv(1024) == b'OK':
            return username
        return ''

    def signup(self):
        """do the sign up function"""

        sign_up = SignUp(self.s_send)
        sign_up.run()

    def close_window(self):
        self.s_send.send(b'QUIT')
        self.gui.destroy()

class Room:
    """this class handles a chat room,
    contains functions for chat features"""

    username = 'noname' # the account is logging in

    def __init__(self, s_send, roomName):
        self.s_send = s_send
        self.roomName = roomName[0] # room code to distinguish with other rooms
        self.isActive = True # True if the room is existed on server

        self.gui = Tk()
        self.gui.title(roomName[1]) # room's title
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
        self.st_recv.tag_config('notif', foreground = 'green')

        self.st_send = scrolledtext.ScrolledText(self.gui,
            wrap = WORD,
            width = 30,
            height = 3,
            font = ('consolas', 12))
        self.st_send.grid(row = 1, column = 0)
        self.st_send.focus()

        butt_send = Button(self.gui, text = 'Send', command = self.send_message)
        butt_send.grid(row = 2, column = 0)

        self.gui.protocol('WM_DELETE_WINDOW', self.close_window)

        self.e_upload = Entry(self.gui, width = 15)
        self.e_upload.grid(row = 3, column = 0)
        butt_upload = Button(self.gui, text = 'Upload', command = self.upload)
        butt_upload.grid(row = 3, column = 2)
        butt_browse = Button(self.gui, text = '...', command = self.browse)
        butt_browse.grid(row = 3, column = 1)

        self.e_download = Entry(self.gui, width = 15)
        self.e_download.grid(row = 4, column = 0)
        butt_download = Button(self.gui, text = 'Download', command = self.download)
        butt_download.grid(row = 4, column = 2)

    def run(self):
        self.gui.mainloop()

    def send_message(self):
        """send messages to server"""

        if not self.isActive:
            messagebox.showerror('Error', 'Remote user has closed this chat!')
            self.gui.destroy()
            return

        text = self.st_send.get('1.0', END)
        self.st_send.delete('1.0', END)
        text = text[:-1]
        if text == '':
            return
        response = self.username + ' ' + text
        # response: <room> MSG <user who send> <message>
        self.s_send.send(self.roomName.encode() + b' MSG ' + response.encode())
        self.s_send.recv(1024)

    def recv_message(self, msg):
        """parse messages and show them in chat box"""

        msg = msg.split(' ', 1)
        
        self.st_recv.configure(state = 'normal')
        if msg[0] == 'MSG':
            m = msg[1].split(' ', 1)
            self.st_recv.insert(END, '@' + m[0] + ': ', 'user')
            self.st_recv.insert(END, m[1], 'msg')
        elif msg[0] == 'NOTI':
            self.st_recv.insert(END, msg[1], 'notif')
        self.st_recv.insert(END, '\n')
        self.st_recv.configure(state = 'disabled')
        self.st_recv.see('end')

    def close_window(self):
        """send delete room request to server and quit room"""

        if self.isActive:
            self.s_send.send(b'PRIVCHAT')
            self.s_send.recv(1024)
            self.s_send.send(b'DEL\n')
            self.s_send.recv(1024)
            self.s_send.send(self.roomName.encode())
            self.s_send.recv(1024)

        self.gui.destroy()
    
    def upload(self):
        """handle upload request"""

        if not self.isActive:
            messagebox.showerror('Error', 'Remote user has closed this chat!')
            self.gui.destroy()
            return

        filename = self.e_upload.get()
        if filename == '':
            return

        self.s_send.send(b'UPLOAD')
        self.s_send.recv(1024)
        self.s_send.send(b'OK')

        s_up = socket.socket() # this socket for sending file
        addr = self.s_send.recv(1024).decode()
        addr = addr.split(' ')
        s_up.connect((addr[0], int(addr[1])))

        t = threading.Thread(target=self.upload_thread, args=(s_up, filename))
        t.start()

    def upload_thread(self, s_up, filename):
        """handle sending file in a separated thread"""

        filesize = os.path.getsize(filename)
        s_up.send(self.roomName.encode() + b' ' + filename.split('/')[-1].encode())
        s_up.recv(1024)
        s_up.send(str(filesize).encode())
        s_up.recv(1024)

        self.recv_message('NOTI Uploading file...')
        with open(filename, 'rb') as f:
            bytesToSend = f.read(1048576)
            s_up.send(bytesToSend)
            totalSend = len(bytesToSend)
            while bytesToSend != b'':
                bytesToSend = f.read(1048576)
                s_up.send(bytesToSend)
                totalSend += len(bytesToSend)

    def browse(self):
        """choose file for uploading"""

        filename = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("all files","*.*"),))
        self.e_upload.delete(0, END)
        self.e_upload.insert(0, filename)

    def download(self):
        """handle download request"""

        if not self.isActive:
            messagebox.showerror('Error', 'Remote user has closed this chat!')
            self.gui.destroy()
            return

        fname = self.e_download.get()
        self.s_send.send(b'DOWNLOAD')
        self.s_send.recv(1024)
        self.s_send.send(self.roomName.encode() + b' ' + fname.encode())
        response = self.s_send.recv(1024).decode()
        if response == 'NO':
            messagebox.showerror('Error', 'File not found!')
            return

        self.s_send.send(b'OK')
        s_down = socket.socket() # this socket for receiving file
        addr = self.s_send.recv(1024).decode()
        addr = addr.split(' ')
        s_down.connect((addr[0], int(addr[1])))

        t = threading.Thread(target=self.download_thread, args=(s_down,))
        t.start()

    def download_thread(self, s_down):
        """handle downloading file in a separated thread"""

        fsize = s_down.recv(1024)
        fsize = int(fsize)
        fname = filedialog.asksaveasfilename(initialdir = "/",title = "Select file",filetypes = (("all files","*.*"),))
        if fname == '':
            s_down.send(b'QUIT')
            return
        s_down.send(b'OK')

        self.recv_message('NOTI Downloading...')
        f = open(fname, 'wb')
        data = s_down.recv(1048576)
        totalRecv = len(data)
        f.write(data)
        while totalRecv < fsize:
            data = s_down.recv(1048576)
            totalRecv += len(data)
            f.write(data)
        f.close()
        self.recv_message('NOTI Download completed.')

class MainRoom(Room):
    """
    The main chat room for all clients\n
    Contains a feature to create private chat room
    """

    def __init__(self, s_send, roomName):
        super(MainRoom, self).__init__(s_send, roomName)

        self.e_priv_chat = Entry(self.gui, width = 15)
        self.e_priv_chat.grid(row = 0, column = 1, sticky = W)
        butt_priv_chat = Button(self.gui, text = 'Chat', command = self.priv_chat)
        butt_priv_chat.grid(row = 0, column = 2, sticky = W)

    def priv_chat(self):
        """send create chat room command to server"""

        self.s_send.send(b'PRIVCHAT')
        self.s_send.recv(1024)
        peer = self.e_priv_chat.get()
        self.s_send.send(peer.encode())
        if self.s_send.recv(1024) == b'NO':
            messagebox.showerror('Error', 'User has not logged in yet!')

    def close_window(self):
        """Exit the main room with logging out"""
        self.s_send.send(b'QUIT')
        self.gui.destroy()

class RoomList:
    """
    Contains functions for creating private chat room
    """

    rooms = {}
    s_send = None

    def addRoom(self, roomName):
        t = threading.Thread(target=self.createRoom_thread, args=(roomName,))
        t.start()

    def createRoom_thread(self, roomName):
        """create and run chat room in a separated thread"""
        self.rooms[roomName[0]] = Room(self.s_send, roomName)
        self.rooms[roomName[0]].run()
        self.rooms.pop(roomName[0])

def main():
    """The main thread run the main chat room"""

    host = '127.0.0.1'
    port = 6666

    # get server host and port from settings file
    with open('settings', 'r') as f:
        host = f.readline().strip('\n')
        port = f.readline().strip('\n')
        port = int(port)

    s_send = socket.socket()
    s_send.connect((host, port))
    
    # Login
    log_in = LogIn(s_send)
    username = log_in.run()
    if username == '':
        return

    # set username to all rooms that are being created
    Room.username = username

    # create socket for receiving commands and messages from server
    s_send.send(b'CONN')
    s_recv = socket.socket()
    addr = s_send.recv(1024).decode()
    addr = addr.split(' ')
    s_recv.connect((addr[0], int(addr[1])))

    rooms = {}
    RoomList.rooms = rooms
    RoomList.s_send = s_send

    # use a separated thread for receiving via s_recv
    t = threading.Thread(target=recv_message, args=(rooms, s_recv))
    t.start()

    rooms['all'] = MainRoom(s_send, ('all', 'Chat'))
    rooms['all'].run()

def recv_message(rooms, s_recv):
    """receive commands and messages from server and handle them"""

    while True:
        msg = s_recv.recv(1024).decode()
        if msg == 'QUIT':
            break

        s_recv.send(b'OK')

        if msg == 'PRIVCHAT':
            priv_chat(s_recv)
            continue

        msg = msg.split(' ', 1)
        if msg[0] in rooms:
            rooms[msg[0]].recv_message(msg[1])

def priv_chat(s_recv):
    """handle PRIVCHAT command"""

    roomName = s_recv.recv(1024).decode()
    s_recv.send(b'OK')

    if roomName == 'QUIT':
        roomName = s_recv.recv(1024).decode()
        s_recv.send(b'OK')

        # if the room has been deleted, return
        if roomName not in RoomList.rooms:
            return
        
        RoomList.rooms[roomName].isActive = False
        return

    roomName = roomName.split(' ', 1)
    rlist = RoomList()
    rlist.addRoom(roomName)

if __name__ == "__main__":
    main()