from client import Client

def main():
    c = Client("10.10.1.1", 2018)
    # Ahora esto funciona sin AttributeError
    print(f"Tu puerto local es: {c.local_port}")

    msg = ""
    while msg.lower() not in ('quit', 'shutdown server'):
        msg = input(">> ")
        c.send(msg)
    c.close()

if __name__ == '__main__':
    main()

