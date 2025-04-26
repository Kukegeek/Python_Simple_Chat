from client import Client

def main():
    c1 = Client("127.0.0.1", 5500)
    message = ""
    while True:
        line = input("Destino (puerto) | lista | quit: ")
        if line == 'quit':
            break
        if line == 'lista':
            c1.send('lista')
            continue
        puerto, msg = line.split(' ', 1)
        c1.send(f"{puerto} {msg}")

if __name__ == '__main__':
    main()
