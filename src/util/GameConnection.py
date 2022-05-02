import json
import logging
import threading
import time
from subprocess import Popen as new

import keyboard
from websocket_server import WebsocketServer


class GameConnection(threading.Thread):
    def __init__(self, host = 'localhost', port = 9000):
        super().__init__()
        self.server = WebsocketServer(host = host, port = port, loglevel = logging.INFO)
        self.server.set_fn_new_client(self.new_client)
        self.server.set_fn_message_received(self.game_response)
        self.server.set_fn_client_left(self.game_window_closed)

        self.response = None

        self.client = None
        self.game_process = None
        self.condition_object: threading.Condition = None

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
        self.response = message
        self.condition_object.acquire()
        self.condition_object.notify()
        self.condition_object.release()

    def game_window_closed(self, client, server):
        print(f"Game Window Closed")
        self.game_process.terminate()
        self.game_process.wait()
        self.client = None

    def start_game(self, game_path = '../science_birds/rewin/ScienceBirds.exe'):
        self.game_process = new(game_path, shell = False)

    def new_client(self, client, server: WebsocketServer):
        print("New game window connected")
        self.client = client
        self.condition_object.acquire()
        self.condition_object.notify()
        self.condition_object.release()

    def wait_for_game_window(self):
        counter = 0
        self.condition_object = threading.Condition()
        self.condition_object.acquire()
        while self.client is None:
            print(f"Waiting for client window: {counter}")
            self.condition_object.wait()

        message = [0, 'loadscene', {'scene': 'LevelSelectMenu'}]
        self.server.send_message(self.client, json.dumps(message))
        self.wait_for_response()


    def change_level(self, index = 0):
        message = [0, 'selectlevel', {'levelIndex': index}]
        self.server.send_message(self.client, json.dumps(message))
        self.wait_for_response()

    def stop(self):
        self.game_process.terminate()
        self.game_process.wait()


if __name__ == '__main__':
    game_connection = GameConnection()
    game_connection.start()

    print("Start game")
    game_connection.start_game()

    print("Start wait")
    game_connection.wait_for_game_window()
    time.sleep(2.4)

    print("Change Level")
    game_connection.change_level(index = 1)

    keyboard.wait("p")
