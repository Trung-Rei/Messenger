import socket
import threading
import os

rooms = {}
users = {}
online_users = {}

def main():
    host = ''
    port = 6666

    s = socket.socket()
    s.bind((host, port))

    s.listen(10)

    rooms['all'] = {}
    loadUsers(users)

    print("Server Started.")
    while True:
        c, addr = s.accept()
        print("client connected ip: ", str(addr))
        t = threading.Thread(target=clientHandler, args=(c,))
        t.start()

    s.close()

def loadUsers(u):
    with open('users.dat', 'r') as f:
        for line in f:
            user = line.strip('\n').split(' ', 1)
            users[user[0]] = user[1]

def clientHandler(conn):
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

    distribute_noti('@' + username + ' log in')

    conn.recv(1024)
    s = socket.socket()
    s.bind(('', 0))
    s.listen(1)
    addr = s.getsockname()
    response = conn.getsockname()[0] + ' ' + str(addr[1])
    conn.send(response.encode())
    s_recv, addr = s.accept()
    rooms['all'][username] = s_recv

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

        parse = msg.split(' ', 2)
        if parse[1] == 'MSG':
            distribute_msg(msg)

    rooms['all'].pop(username)
    s_recv.send(b'QUIT')
    online_users.pop(username)
    s_recv.close()
    s.close()
    conn.close()

    distribute_noti('@' + username + ' log off')

    if len(rooms['all']) == 0:
        for r, d, f in os.walk('uploads'):
            for i in f:
                room = i.split('+', 1)[0]
                if room == 'all':
                    os.remove('uploads/' + i)
            break

def distribute_msg(msg):
    room = msg.split(' ', 1)[0]
    r = rooms[room]
    for c in r:
        r[c].send(msg.encode())
        r[c].recv(1024)

def distribute_noti(msg):
    r = rooms['all']
    for c in r:
        response = 'all NOTI ' + msg
        r[c].send(response.encode())
        r[c].recv(1024)

def pri_chat(s_send, s_recv, username):
    uname = s_send.recv(1024).decode()

    if uname == 'DEL\n':
        s_send.send(b'OK')

        roomName = s_send.recv(1024).decode()
        s_send.send(b'OK')
        
        r = rooms[roomName]
        for c in r:
            r[c].send(b'PRIVCHAT')
            r[c].recv(1024)
            r[c].send(b'QUIT')
            r[c].recv(1024)
            r[c].send(roomName.encode())
            r[c].recv(1024)
        rooms.pop(roomName)
        
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

        roomName = username + '\n' + uname
        rooms[roomName] = {}
        rooms[roomName][username] = s_recv
        rooms[roomName][uname] = rooms['all'][uname]

        r = rooms[roomName]
        for c in r:
            r[c].send(b'PRIVCHAT')
            r[c].recv(1024)
            r[c].send(roomName.encode() + b' @' + username.encode() + b' + @' + uname.encode())
            r[c].recv(1024)

def upload(s_send, username):
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

def checkLogin(uname, pword):
    if uname not in users:
        return False
    if users[uname] != pword:
        return False
    if uname in online_users:
        return False
    
    online_users[uname] = True
    return True

def checkSignup(uname, pword):
    if uname in users:
        return False

    users[uname] = pword
    with open('users.dat', 'a') as f:
        f.write(uname + ' ' + pword + '\n')
    return True

if __name__ == "__main__":
    main()
