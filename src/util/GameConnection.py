import json
import logging
import sys
import threading
import time
from subprocess import Popen as new

import subprocess

import keyboard
from websocket_server import WebsocketServer


class GameConnection(threading.Thread):
    def __init__(self, host = 'localhost', port = 9001):
        super().__init__()

        self.condition_object = threading.Condition()

        self.server: WebsocketServer = WebsocketServer(host = host, port = port, loglevel = logging.INFO)
        self.server.set_fn_new_client(self.new_client)
        self.server.set_fn_message_received(self.game_response)
        self.server.set_fn_client_left(self.game_window_closed)

        self.response = None

        self.client = None
        self.game_process: subprocess.Popen[str] = None
        self.ai_process: subprocess.Popen[str] = None

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
        if self.game_process:
            self.game_process.terminate()
            self.game_process.wait()

        if self.ai_process:
            self.ai_process.terminate()
            self.ai_process.wait()

        self.client = None

    def start_game(self, game_path = '../science_birds/win-new/ScienceBirds.exe'):
        self.game_process = new(game_path, shell = False)

    def startAi(self, ai_process = '../ai/Naive-Agent-standalone-Streamlined.jar'):

        if self.ai_process:
            self.ai_process.terminate()
            self.ai_process.wait()

        message = [0, 'aimodus', 'true']
        self.send(message)
        self.wait_for_response()
        self.ai_process = new(ai_process)

    def stopAI(self):

        message = [0, 'aimodus', 'true']
        self.send(message)
        self.wait_for_response()

        if self.ai_process:
            self.ai_process.terminate()
            self.ai_process.wait()

    def stop(self):
        self.server.shutdown_gracefully()
        if self.game_process:
            self.game_process.terminate()
        if self.ai_process:
            self.ai_process.terminate()

    def new_client(self, client, server: WebsocketServer):
        print(f"New game window connected {client}")
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

    def wait_till_all_level_played(self):
        while True:
            if self.response is not None and 'data' in self.response[1] and self.response[1]['data'] == "True":
                break

            print("Wait for level played")
            message = [0, 'alllevelsplayed']
            self.send(message)
            self.wait_for_response()
            time.sleep(1)

    def change_level(self, index = 0):
        message = [0, 'selectlevel', {'levelIndex': index}]
        self.send(message)
        self.wait_for_response()

    def get_data(self):
        message = [0, 'getdata']
        self.send(message)
        self.wait_for_response()
        return self.response[1]['data']


if __name__ == '__main__':
    game_connection = GameConnection()

    try:
        game_connection.start()

        # print("Start game")
        # game_connection.start_game()
        game_connection.wait_for_game_window()

        print("Change Level")
        game_connection.change_level(index = 3)

        print("Start AI")
        game_connection.startAi()

        print("Change Level")
        game_connection.get_data()

        print("Wait for keyboard: p")
        keyboard.wait("p")
        game_connection.stop()
    except KeyboardInterrupt:
        game_connection.stop()
