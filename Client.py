import socket
import getpass

HEADER = 64
PORT = '(No Port Saved)'
FORMAT = 'utf-8'
SERVER = '(No IP Saved)'
while True:
    try:
        with open("server.txt", 'r') as f:
            SERVER = f.readline().replace('\n', '').replace("-IP", '').replace("(", '').replace(")", '').strip()
            PORT = f.readline().replace('\n', '').replace("-Port", '').replace("(", '').replace(")", '').strip()
    except FileNotFoundError:
        print("Creating file <server.txt>...")
        with open("server.txt", 'w') as f:
            f.write("(ENTER IP HERE) -IP\n")
            f.write("(ENTER PORT HERE) -Port")
        print("File created, please open <server.txt> and enter values in between brackets")
        input("Press enter to continue...")

    try:
        PORT = int(PORT)
    except ValueError:
        answer = input('Please change PORT to an integer, try again? (y/n): ')
        if answer.lower() == 'n':
            raise SystemExit

    ADDR = (SERVER, PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print("\nConnecting...")
        client.connect(ADDR)
        break
    except TimeoutError:
        answer = input("Could not Connect to Server, Would you like to try again (y/n): ")
        if answer.lower() == 'n':
            raise SystemExit


def receive():
    msg_length = client.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = client.recv(msg_length).decode(FORMAT)
        return msg


def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)


print(receive() + ":" + str(PORT))  # Prints the Server connect message

while True:
    try:
        received = receive()
        try:
            if "<SEPARATOR>" in received:
                received = received.split("<SEPARATOR>")
                with open(received[0], 'wb') as f:
                    file_data = client.recv(int(received[1]))
                    f.write(file_data)
                    print(f"\n-File ({received[0]}) has been saved-")

            elif received[-2:] == ': ':
                if '(hidden): ' in received.lower():
                    try:
                        send(getpass.getpass(prompt=received, stream=None))
                    except AttributeError:
                        send(input(received))
                else:
                    print(received, end='')
                    send(input(""))
            else:
                print(received)

            if "[SERVER] You have disconnected" in received:
                break

        except TypeError:
            break
    except ConnectionResetError:
        print('-Could not send message to server-')
        break
