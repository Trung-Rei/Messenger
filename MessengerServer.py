import socket
import threading

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
    rooms['all'][s_recv] = True

    while True:
        msg = conn.recv(1024).decode()
        if msg == 'QUIT':
            break
        conn.send(b'OK')
        # kiểm tra nếu là request

        parse = msg.split(' ', 2)
        if parse[1] == 'MSG':
            distribute_msg(msg)

    rooms['all'].pop(s_recv)
    s_recv.send(b'QUIT')
    online_users.pop(username)
    s_recv.close()
    s.close()
    conn.close()

    distribute_noti('@' + username + ' log off')

def distribute_msg(msg):
    room = msg.split(' ', 1)[0]
    for c in rooms[room]:
        c.send(msg.encode())
        c.recv(1024)

def distribute_noti(msg):
    for c in rooms['all']:
        response = 'all NOTI ' + msg
        c.send(response.encode())
        c.recv(1024)

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
