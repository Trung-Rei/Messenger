import socket
import threading
import os

rooms = {} # Store current chat rooms
users = {} # Store all accounts that have been signed up
online_users = {} # store current online accounts

def main():
    host = ''
    port = 6666

    s = socket.socket()
    s.bind((host, port))

    s.listen(10)

    rooms['all'] = {} # the main room for all accounts
    loadUsers() # load data from account database

    print("Server Started.")
    while True:
        c, addr = s.accept()
        print("client connected ip: ", str(addr))
        t = threading.Thread(target=clientHandler, args=(c,))
        t.start()

    s.close()

def loadUsers():
    """
    load data from account database
    """
    with open('users.dat', 'r') as f:
        for line in f:
            user = line.strip('\n').split(' ', 1)
            users[user[0]] = user[1]

def clientHandler(conn):
    """
    handle an individual client host with multithreading
    """
    
    # handle log in and sign up
    username = ''
    conn.recv(1024)
    while True:
        response = conn.recv(1024).decode()
        if response == 'QUIT':
            conn.close()
            return
        if response == 'SIGNUP':
            while True:
                response = conn.recv(1024).decode()
                if response == 'QUIT':
                    break
                uname, pword = response.split('\n')[0], response.split('\n')[1]
                if checkSignup(uname, pword):
                    conn.send(b'OK')
                    break
                else:
                    conn.send(b'NO')
            continue
        uname, pword = response.split('\n')[0], response.split('\n')[1]
        if checkLogin(uname, pword):
            username = uname
            conn.send(b'OK')
            break
        else:
            conn.send(b'NO')

    # send notification to all clients
    distribute_noti('@' + username + ' log in')

    # create another socket for sending message to client
    conn.recv(1024)
    s = socket.socket()
    s.bind(('', 0))
    s.listen(1)
    addr = s.getsockname()
    response = conn.getsockname()[0] + ' ' + str(addr[1])
    conn.send(response.encode())
    s_recv, addr = s.accept()

    rooms['all'][username] = s_recv

    # receive requests and messages from client and handle each one
    while True:
        msg = conn.recv(1024).decode()
        conn.send(b'OK')

        if msg == 'QUIT':
            break

        if msg == 'PRIVCHAT':
            pri_chat(conn, s_recv, username)
            continue

        if msg == 'UPLOAD':
            upload(conn, username)
            continue

        if msg == 'DOWNLOAD':
            download(conn)
            continue

        parse = msg.split(' ', 2)
        if parse[1] == 'MSG':
            distribute_msg(msg)

    # clean things before finish
    rooms['all'].pop(username)
    s_recv.send(b'QUIT')
    online_users.pop(username)
    s_recv.close()
    s.close()
    conn.close()

    # send notification to all clients
    distribute_noti('@' + username + ' log off')

    # remove all files belong to general room
    if len(rooms['all']) == 0:
        for r, d, f in os.walk('uploads'):
            for i in f:
                room = i.split('+', 1)[0]
                if room == 'all':
                    os.remove('uploads/' + i)
            break

def distribute_msg(msg):
    """
    distribute messages to a specific room
    """
    
    room = msg.split(' ', 1)[0]
    r = rooms[room]
    for c in r:
        r[c].send(msg.encode())
        r[c].recv(1024)

def distribute_noti(msg):
    """
    distribute notifications to general room
    """
    
    r = rooms['all']
    for c in r:
        response = 'all NOTI ' + msg
        r[c].send(response.encode())
        r[c].recv(1024)

def pri_chat(s_send, s_recv, username):
    """
    handle private chat request
    """
    
    uname = s_send.recv(1024).decode()

    if uname == 'DEL\n':
        s_send.send(b'OK')

        roomName = s_send.recv(1024).decode()
        s_send.send(b'OK')
        
        # send quit command to all client in roomName and delete room
        r = rooms[roomName]
        for c in r:
            r[c].send(b'PRIVCHAT')
            r[c].recv(1024)
            r[c].send(b'QUIT')
            r[c].recv(1024)
            r[c].send(roomName.encode())
            r[c].recv(1024)
        rooms.pop(roomName)
        
        # remove all files belong to room: roomName
        for r, d, f in os.walk('uploads'):
            for i in f:
                room = i.split('+', 1)[0]
                if room == 'all':
                    continue
                room = room.split(' ')
                room = room[0] + '\n' + room[1]
                if room == roomName:
                    os.remove('uploads/' + i)
            break
        return

    if not uname in online_users:
        s_send.send(b'NO')
    else:
        s_send.send(b'OK')

        # create room
        roomName = username + '\n' + uname
        rooms[roomName] = {}
        rooms[roomName][username] = s_recv
        rooms[roomName][uname] = rooms['all'][uname]

        # send command create room to all client in room
        r = rooms[roomName]
        for c in r:
            r[c].send(b'PRIVCHAT')
            r[c].recv(1024)
            r[c].send(roomName.encode() + b' @' + username.encode() + b' + @' + uname.encode())
            r[c].recv(1024)

def upload(s_send, username):
    """
    handle upload request
    """

    # create another socket for sending file
    s_send.recv(1024)
    s = socket.socket()
    s.bind(('', 0))
    s.listen(1)
    addr = s.getsockname()
    response = s_send.getsockname()[0] + ' ' + str(addr[1])
    s_send.send(response.encode())
    s_recv, addr = s.accept()
    t = threading.Thread(target=upload_thread, args=(s_recv, s, username))
    t.start()

def upload_thread(s_up, s, username):
    """
    handle upload in a separated thread
    """
    
    response = s_up.recv(1024).decode()
    s_up.send(b'OK')
    response = response.split(' ', 1)
    rname = response[0]
    fname = response[1]
    response = s_up.recv(1024).decode()
    s_up.send(b'OK')
    fsize = int(response)

    if rname == 'all':
        fname = 'all+' + fname
    else:
        fname = rname.split('\n')[0] + ' ' + rname.split('\n')[1] + '+' + fname
    
    f = open('uploads/' + fname, 'wb')
    data = s_up.recv(1048576)
    totalRecv = len(data)
    f.write(data)
    while totalRecv < fsize:
        data = s_up.recv(1048576)
        totalRecv += len(data)
        f.write(data)
    f.close()

    s_up.close()
    s.close()

    response = username + ' upload a file: ' + fname.split('+', 1)[1] + '\n'
    distribute_msg(rname + ' MSG ' + response)

def download(s_send):
    """
    handle download request
    """

    rname = s_send.recv(1024).decode()
    rname = rname.split(' ', 1)
    fname = rname[1]
    rname = rname[0]
    if rname != 'all':
        rname = rname.split('\n')
        rname = rname[0] + ' ' + rname[1]
    
    if os.path.isfile('uploads/' + rname + '+' + fname):
        s_send.send(b'OK')
    else:
        s_send.send(b'NO')
        return
    
    # create another socket for sending file
    s_send.recv(1024)
    s = socket.socket()
    s.bind(('', 0))
    s.listen(1)
    addr = s.getsockname()
    response = s_send.getsockname()[0] + ' ' + str(addr[1])
    s_send.send(response.encode())
    s_recv, addr = s.accept()

    t = threading.Thread(target=download_thread, args=(s_recv, s, rname + '+' + fname))
    t.start()

def download_thread(s_down, s, fname):
    """
    handle download in a separated thread
    """

    fsize = os.path.getsize('uploads/' + fname)
    s_down.send(str(fsize).encode())
    if s_down.recv(1024) == b'QUIT':
        s_down.close()
        s.close()
        return
    
    with open('uploads/' + fname, 'rb') as f:
        bytesToSend = f.read(1048576)
        s_down.send(bytesToSend)
        totalSend = len(bytesToSend)
        while bytesToSend != b'':
            bytesToSend = f.read(1048576)
            s_down.send(bytesToSend)
            totalSend += len(bytesToSend)

    s_down.close()
    s.close()

def checkLogin(uname, pword):
    """
    check log in
    """

    if uname not in users:
        return False
    if users[uname] != pword:
        return False
    if uname in online_users:
        return False
    
    online_users[uname] = True
    return True

def checkSignup(uname, pword):
    """
    check sign up
    """
    
    if uname in users:
        return False

    users[uname] = pword
    with open('users.dat', 'a') as f:
        f.write(uname + ' ' + pword + '\n')
    return True

if __name__ == "__main__":
    main()
