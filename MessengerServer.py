import socket
import threading

client = {}

def main():
    host = ''
    port = 6666

    s = socket.socket()
    s.bind((host, port))

    s.listen(5)

    print("Server Started.")
    while True:
        c, addr = s.accept()
        print("client connected ip: ", str(addr))
        t = threading.Thread(target=clientHandler, args=(c,))
        t.start()
         
    s.close()

def clientHandler(conn):
    s = socket.socket()
    s.bind(('', 0))
    s.listen(1)
    addr = s.getsockname()
    response = conn.getsockname()[0] + ' ' + str(addr[1])
    conn.send(response.encode())
    s_recv, addr = s.accept()

    client[s_recv] = 1

    while True:
        msg = conn.recv(1024).decode()
        if msg == 'QUIT':
            break
        conn.send(b'OK')
        response = msg.split(' ', 1)[1]
        distribute_msg('UNKNOWN', response)

    client.pop(s_recv)
    s_recv.close()
    s.close()
    conn.close()

def distribute_msg(user, msg):
    for c in client:
        response = '@' + user + ': ' + msg
        c.send(response.encode())

if __name__ == "__main__":
    main()
