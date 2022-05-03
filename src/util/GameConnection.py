import json
import logging
import os
import threading
import time
from subprocess import Popen as new
import platform

import keyboard
from websocket_server import WebsocketServer


class GameConnection(threading.Thread):
    def __init__(self, host = 'localhost', port = 9000):
        super().__init__()

        self.condition_object = threading.Condition()

        self.server: WebsocketServer = WebsocketServer(host = host, port = port, loglevel = logging.INFO)
        self.server.set_fn_new_client(self.new_client)
        self.server.set_fn_message_received(self.game_response)
        self.server.set_fn_client_left(self.game_window_closed)

        self.response = None

        self.client = None
        self.game_process = None

    def run(self):
        self.server.run_forever()

    def wait_for_response(self):
        # Wait for game response
        if self.response is None:
            print("Wait for message")
            self.condition_object.acquire()
            self.condition_object.wait()
            self.condition_object.release()
            print("Message received")
        else:
            self.response = None

    def game_response(self, client, server, message: str):
        print(f"Game Response: {message}")
        self.response = json.loads(message)
        self.condition_object.acquire()
        self.condition_object.notify()
        self.condition_object.release()

    def game_window_closed(self, client, server):
        print(f"Game Window Closed")
        self.stop_game()
        self.client = None

    def new_client(self, client, server: WebsocketServer):
        print("New game window connected")
        self.client = client
        self.condition_object.acquire()
        self.condition_object.notify()
        self.condition_object.release()

    def send(self, msg):
        self.response = None
        self.server.send_message(self.client, json.dumps(msg))

    def wait_for_game_window(self):
        counter = 0
        self.condition_object.acquire()
        while self.client is None:
            print(f"Waiting for client window: {counter}")
            self.condition_object.wait()

        print("Load level scene")
        message = [0, 'loadscene', {'scene': 'LevelSelectMenu'}]
        self.send(message)
        self.wait_for_response()

        while True:
            if self.response is not None and 'data' in self.response[1] and self.response[1]['data'] == "True":
                break

            print(f"In loop: {self.response}")
            print("Is level loaded")
            message = [0, 'levelsloaded']
            self.send(message)
            self.wait_for_response()
            time.sleep(0.2)

    def change_level(self, index = 0):
        message = [0, 'selectlevel', {'levelIndex': index}]
        self.send(message)
        self.wait_for_response()

    def start_game(self, game_path = '../science_birds/win-new/ScienceBirds.exe'):
        os_name = platform.system()
        if os_name == 'Windows':
            self.game_process = new(game_path, shell = False)
        elif os_name == 'Darwin':
            os.system(f"open {game_path}")

    def stop(self):
        self.server.shutdown_gracefully()
        self.stop_game()

    def stop_game(self):
        os_name = platform.system()
        if os_name == 'Windows':
            if self.game_process:
                self.game_process.terminate()
        elif os_name == 'Darwin':
            os.system("pkill ScienceBirds")

    def getData(self):
        message = [0, 'getdata']
        self.send(message)
        self.wait_for_response()
        return self.response[1]['data']


if __name__ == '__main__':
    game_connection = GameConnection()
    game_connection.start()

    print("Start game")
    game_connection.start_game()

    print("Start wait")
    game_connection.wait_for_game_window()
    # time.sleep(2.4)

    print("Change Level")
    game_connection.change_level(index = 3)

    time.sleep(5)

    print("Change Level")
    game_connection.getData()

    print("Wait for keyboard: p")
    keyboard.wait("p")
    game_connection.stop()
