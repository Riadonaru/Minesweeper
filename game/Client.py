import json
import socket
from turtle import st

import Minesweeper

# HOST = "10.100.102.24"  # The server's hostname or IP address
HOST = '127.0.0.1'
PORT = 65432  # The port used by the server

SUCCESS = b'0'
ERROR = b'-2'
WIN = b'9'
LOSE = b'10'

def client(game: Minesweeper.Game):
    """This method handles all of the input commands, and outputs an int as follows:
        Reveal: -1 - 8 are valid values for cell contents, -2 for error 9 for win & 10 for lose.
        Flag: Either 1 if cell is flagged, 2 if unflagged, -2 for error, 9 for win & 10 for lose.
        Setting: 0 if set successfully, -2 if an error occured.
        Reset: 0 if reset successfull, -2 if an error occured

    Args:
        game (Minesweeper.Game): The game which commands we handle
    """

    global INPUT_SOURCE, SETTINGS_SPR
    
    s: socket.socket = None
    myId: int = None
    try:
        while game.runing:
            INPUT_SOURCE = game.settings["input_source"]

            if INPUT_SOURCE == "client":
                data = input()
            elif INPUT_SOURCE == "server":
                if s is None or myId is None:
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect((HOST, PORT))
                        s.sendall(b'minesweeper')
                        data = str(s.recv(2048), "ascii")
                        print(data)
                        myId = int(data.split()[-1])
                    except:
                        print("Error trying to connect to the server")
                        s.close()
                data = str(s.recv(2048), "ascii")
            
            data = data.split(maxsplit=1)

            if not data:
                break
            
            match data[0]:

                case "say":
                    print(data[1])
                    if INPUT_SOURCE == "server":
                        s.sendall(b'aquired by client')

                case"client":
                    if int(data[1]) == myId:
                        s.sendall(bytes('Successfully Connected to Client %s' % (myId), 'ascii'))

                case "reveal":
                    try:
                        data = data[1].split()
                        x = int(data[0])
                        y = int(data[1])
                        game.reveal(x, y)
                        s.sendall(bytes(game.grid.contents[x][y].content, "ascii"))
                    except:
                        s.sendall(ERROR)


                case "setting":
                    try:
                        data = data[1].split()
                        match str(type(game.settings[data[0]])):
                            
                            case "<class 'bool'>":
                                if data[1] == "True":
                                    game.settings[data[0]] = True
                                elif data[1] == "False":
                                    game.settings[data[0]] = False
                                else:
                                    s.sendall(bytes(data[1] + " is not a valid entry!", 'ascii'))
                            
                            case "<class 'int'>":
                                game.settings[data[0]] = int(data[1])

                            case "<class 'str'>":
                                game.settings[data[0]] = str(data[1])
                        
                        game.setSettings()
                        s.sendall(SUCCESS)

                    except:
                        s.sendall(ERROR)

                case "flag":
                    try:
                        data = data[1].split()
                        if game.flag(int(data[0]), int(data[1])):
                            s.sendall(b'1')
                        else:
                            s.sendall(b'2')
                    except:
                        s.sendall(ERROR)

                case "reset":
                    game.restart()

                case "secret":
                    SETTINGS_SPR = 12
                    game.settings_button.content = SETTINGS_SPR

                case _:
                    print(data[0] + ": Command not found")

    except Exception as e:
        print(e)
    finally:
        if s is not None:
            s.close()
