import json
import threading
from typing import List, Set

import numpy as np
import pygame
from playsound import playsound

pygame.init()


PATH = __file__[:-14] + "files/"
IMAGE_NAMES = ["empty", "cell1", "cell2", "cell3", "cell4",
               "cell5", "cell6", "cell7", "cell8", "clicked_mine", "smile", "shocked", "cool", "dead", "settings", "mine"]

SPR_LIST = [pygame.image.load(PATH + "%s.png" % name)
            for name in IMAGE_NAMES]

FLAG_SPR = pygame.image.load(PATH + "flag.png")
CELL_SPR = pygame.image.load(PATH + "cell.png")
CLICKEDMINE_SPR = pygame.image.load(PATH + "clicked_mine.png")
NOMINE_SPR = pygame.image.load(PATH + "nomine.png")
GAME_STATE_IMAGES = [pygame.image.load(PATH + "%s.png" % name) for name in ("win", "game_over")]

BG_COLOR = (192, 192, 192)

INPUT_SOURCE: str = "server"

RESTART_SPR: int = 10
SETTINGS_SPR = 14

FLAGGED_CELLS: int = 0

with open(PATH[:-6] + "settings.json", "r") as stngs:
    DEFAULT_SETTINGS = json.loads(stngs.read())


class Cell():

    def __init__(self, value: int = 0, hidden: bool = True) -> None:
        self.__hidden: bool = hidden
        self.__flagged: bool = False
        self.__content: int = value
        self.x_pos: int = None
        self.y_pos: int = None
        self.debug = False  # Used for debugging

    @property
    def hidden(self) -> bool:
        return self.__hidden

    @hidden.setter
    def hidden(self, __value):
        if self.flagged:
            raise Exception("Can't dehide a flagged cell")
        elif self.content == -1:
            if GAME.settings["play_sounds"]:
                threading.Thread(target=playsound, args=(PATH + "game-over.mp3",)).start()
            for list in GAME.grid.contents:
                for cell in list:
                    if not cell.flagged:
                        cell.__hidden = False
        else:
            self.__hidden = __value

    @property
    def flagged(self) -> bool:
        return self.__flagged

    @flagged.setter
    def flagged(self, __value: bool) -> None:
        if self.hidden:
            self.__flagged = __value
        else:
            raise Exception("Can't flag a revealed cell")

    @property
    def content(self) -> int:
        return self.__content

    @content.setter
    def content(self, __value) -> None:
        self.__content = __value

    def drawCell(self, x: int, y: int) -> None:
        """This method draws a cell onto the display

        Args:
            x (int): X coordinate to draw to.
            y (int): Y coordinate to draw to.
        """
        self.rect = pygame.Rect(GAME.settings["lrb_border_size"] + x * GAME.settings["cell_size"],
                                GAME.settings["top_border_size"] + y * GAME.settings["cell_size"], GAME.settings["cell_size"], GAME.settings["cell_size"])

        if self.debug:
            GAME.gameDisplay.blit(FLAG_SPR, self.rect)
        elif self.hidden:
            if self.flagged:
                GAME.gameDisplay.blit(FLAG_SPR, self.rect)
            else:
                GAME.gameDisplay.blit(CELL_SPR, self.rect)
        else:
            GAME.gameDisplay.blit(
                SPR_LIST[self.content], self.rect)

    def revealCell(self):
        """This method has the reveal algo.
        """

        global RESTART_SPR

        try:
            self.hidden = False    
            if self.content == -1:
                GAME.restart_button.content = 13
                RESTART_SPR = 13
                self.content = 9
                GAME.condition = -1
                return

            cells_to_check: Set[Cell] = {self}
            while len(cells_to_check) > 0:
                cell = cells_to_check.pop()
                if cell.saturated():
                    for y in range(-1, 2):
                        for x in range(-1, 2):
                            if 0 <= cell.x_pos + x < GAME.settings["width"] and 0 <= cell.y_pos + y < GAME.settings["height"]:
                                adj_cell = GAME.grid.contents[cell.y_pos +
                                                                            y][cell.x_pos + x]
                                if not adj_cell.flagged:
                                    adj_cell.hidden = False
                                    if not adj_cell.checked():
                                        if cell.content == 0 or adj_cell.content == 0:
                                            cells_to_check.add(adj_cell)

        except Exception as e:
            print(e)

    def saturated(self) -> bool:
        """This method checks if there are as much flags around a cell as the number on it.

        Returns:
            bool: True if as much flags or more, False if less or the cell is a mine.
        """
        adj_flags = 0
        if GAME.grid.contents[self.y_pos][self.x_pos].content not in {0, 1, 2, 3, 4, 5, 6, 7, 8}:
            return False
        else:
            for a in range(-1, 2):
                for b in range(-1, 2):
                    if 0 <= self.x_pos + a < GAME.settings["width"] and 0 <= self.y_pos + b < GAME.settings["height"]:
                        if GAME.grid.contents[self.y_pos + b][self.x_pos + a].flagged:
                            adj_flags += 1

            if GAME.grid.contents[self.y_pos][self.x_pos].content <= adj_flags:
                return True
            else:
                return False


    def checked(self) -> bool:
        for y in range(-1, 2):
            for x in range(-1, 2):
                if 0 <= self.x_pos + x < GAME.settings["width"] and 0 <= self.y_pos + y < GAME.settings["height"]:
                    adj_cell = GAME.grid.contents[self.y_pos +
                                                                y][self.x_pos + x]
                    if adj_cell.hidden:
                        return False
        
        return True


class Grid():

    def __init__(self) -> None:
        self.overall_tiles = GAME.settings["width"] * \
            GAME.settings["height"]
        self.num_of_mines = int(GAME.settings["width"] *
                                GAME.settings["height"] * GAME.settings["mines"] / 100)
        self.contents_created: bool = False
        self.contents: List[List[Cell]] = [[Cell() for _ in range(
            GAME.settings["width"])] for _ in range(GAME.settings["height"])]

    def createLayout(self, x: int = None, y: int = None) -> None:
        """Creates the grid layout for the game and stores it in self.contents

        Args:
            x (int, optional): The x location for a safe start. Defaults to None.
            y (int, optional): The y location for a safe start. Defaults to None.
        """
        if not self.contents[y][x].flagged:

            arr = np.array([Cell for _ in range(self.overall_tiles)])

            for i in range(self.overall_tiles):
                if i < self.num_of_mines:
                    arr[i] = Cell(-1)
                else:
                    arr[i] = Cell()

            np.random.shuffle(arr)
            self.contents: List[List[Cell]] = list(
                arr.reshape(GAME.settings["height"], GAME.settings["width"]))

            if GAME.settings["easy_start"]:
                for b in range(-1, 2):
                    for a in range(-1, 2):
                        if 0 <= x + a < GAME.settings["width"] and 0 <= y + b < GAME.settings["height"]:
                            if self.contents[y + b][x + a].content != 0:
                                self.contents[y + b][x + a].content = 0

            for y in range(GAME.settings["height"]):
                for x in range(GAME.settings["width"]):
                    self.contents[y][x].x_pos = x
                    self.contents[y][x].y_pos = y
                    self.contents[y][x].content = self.checkAdjMines(x, y)

            self.contents_created = True

    def checkAdjMines(self, x_index: int, y_index: int) -> int:
        """Returns the number of adjacent mines to the cell at the given index.

        Args:
            x_index (int): The x index of the cell.
            y_index (int): The y index of the cell.

        Returns:
            int: The number of mines adjacent to the cell.
        """
        if self.contents[y_index][x_index].content != -1:
            num_of_adj_mines = 0
            # print("\nNew\n")
            for y in range(-1, 2):
                for x in range(-1, 2):
                    if 0 <= x_index + x < GAME.settings["width"] and 0 <= y_index + y < GAME.settings["height"]:
                        if self.contents[y_index + y][x_index + x].content == -1:
                            # print("Mine at:", x_index + x, y_index + y)
                            num_of_adj_mines += 1

            return num_of_adj_mines
        else:
            return -1


class Game():

    def __init__(self) -> None:
        self.runing = True
        self.condition = 1 # 0 for win, 1 for playing, -1 for lose.
        self.flagging = False
        self.settings = DEFAULT_SETTINGS
        self.settings_button = Cell(SETTINGS_SPR, False)
        self.restart_button = Cell(RESTART_SPR, False)
        self.settings_pos = (self.settings["width"] - 0.75, -2.75)
        self.drawThread: threading.Thread = None
        self.clientThread: threading.Thread = None
        if self.settings["width"] % 2 == 0:
            self.restart_pos = (self.settings["width"] / 2 - 0.5, -2)
        else:
            self.restart_pos = self.settings["width"] / 2


    def flag(self, x: int, y: int) -> bool:
        """This method Flags/Unflags the cell at the given coordinates.

        Args:
            x (int): The x coordinate of the cell to flag.
            y (int): The y coordinate of the cell to
        """

        global FLAGGED_CELLS, RESTART_SPR

        if self.grid.contents[y][x].flagged:
            self.grid.contents[y][x].flagged = False
            FLAGGED_CELLS -= 1
        else:
            self.grid.contents[y][x].flagged = True
            FLAGGED_CELLS += 1

        if FLAGGED_CELLS == self.grid.num_of_mines:
            b = False
            for list in self.grid.contents:
                for cell in list:
                    if cell.content == -1 and not cell.flagged:
                        b = True
                        break

                if b:
                    break

            else:
                FLAGGED_CELLS = 0
                RESTART_SPR = 12
                self.restart_button.content = 12
                for list in self.grid.contents:
                    for cell in list:
                        if cell.content != -1:
                            cell.hidden = False
                self.condition = 0

        return self.grid.contents[y][x].flagged


    def reveal(self, x: int, y: int):
        """This method reveals the cell at the given coordinates if possible.

        Args:
            x (int): The x coordinate of the cell.
            y (int): The y coordinate of the cell.
        """
        if not self.grid.contents_created:
            self.grid.createLayout(x, y)
        self.grid.contents[y][x].revealCell()


    def restart(self):
        """Resets the given Game.

        Args:
            game (Minesweeper.Game): The game which we are trying to reset
        """
        global RESTART_SPR

        RESTART_SPR = 10
        self.grid = Grid()
        self.condition = 1
        self.play()


    def setSettings(self):
        """This method writes the current settings configuration into settings.json in a readable format.
        """

        with open(PATH[:-6] + "settings.json", "w") as stngs:
            settings = json.dumps(self.settings).split(", ")
            stngs.write("{\n")
            stngs.write("    " + settings[0][1:] + ",\n")
            stngs.writelines(["    " + settings[i] + ",\n" for i in range(1, len(settings) - 1)])
            stngs.write("    " + settings[len(settings) - 1][:-1] + "\n")
            stngs.write("}")

        self.restart()
        

    def play(self):
        """Init & Create the display, the grid and starts the relevant Threads.
        """
        self.running = True
        self.disp_width = self.settings["cell_size"] * self.settings["width"] + \
            self.settings["lrb_border_size"] * 2  # Display width
        self.disp_height = self.settings["cell_size"] * self.settings["height"] + \
            self.settings["lrb_border_size"] + \
            self.settings["top_border_size"]  # Display height

        self.gameDisplay = pygame.display.set_mode(
            (self.disp_width, self.disp_height))  # Create display
        pygame.display.set_caption("Minesweeper")
        
        self.grid = Grid()
        if self.drawThread is not None and not self.drawThread.is_alive():
            self.drawThread.start()

        if  self.clientThread is not None and not self.clientThread.is_alive():
            if self.settings["allow_command_input"]:
                self.clientThread.start()
        

GAME = Game()
