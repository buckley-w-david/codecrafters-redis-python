import socket

PONG=b"+PONG\r\n"

def main():
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    conn, _ = server_socket.accept()
    with conn:
        _ = conn.recv(1024)
        conn.sendall(PONG)


if __name__ == "__main__":
    main()
