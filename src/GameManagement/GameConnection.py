from loguru import logger
import json
import logging
import os
import platform
import subprocess
import threading
import time
from subprocess import Popen as new
from websocket_server import WebsocketServer
from util.Config import Config

from wsocket import WSocketApp, WebSocketError, logger, run


class GameConnection(threading.Thread):
    def __init__(self, conf: Config, host = 'localhost', port = 9001, stop_if_game_windows_close = True):
        super().__init__()

        if conf:
            self.ai_path = conf.get_ai_path()
        self.condition_object = threading.Condition()

        # self.server: WebsocketServer = WebsocketServer(host = host, port = port, loglevel = logging.INFO)
        # self.server.set_fn_new_client(self.new_client)
        # self.server.set_fn_message_received(self.game_response)
        # self.server.set_fn_client_left(self.game_window_closed)

        self.host = host
        self.port = port

        self.server = WSocketApp()
        self.server.onconnect += self.new_client
        self.server.onmessage += self.game_response
        self.server.onclose += self.game_window_closed

        self._stop_event = threading.Event()
        self.stop_if_game_windows_close = stop_if_game_windows_close

        self.response = None

        self.client = None
        self.game_process: subprocess.Popen[str] = None
        self.ai_process: subprocess.Popen[str] = None
        self.counter = 0

    def run(self):
        run(self.server, host=self.host, port=self.port)

    def wait_for_response(self):
        # Wait for game response
        if self.response is None:
            logger.debug("Wait for message")
            self.condition_object.acquire()
            self.condition_object.wait()
            self.condition_object.release()
            msg = self.response
            self.response = None
        else:
            msg = self.response
            self.response = None

        return msg



    def game_response(self, message: str, client):
        if len(message) > 200:
            logger.debug(f"Game Response: {message[:200]}")
        else:
            logger.debug(f"Game Response: {message[:200]}")
        self.response = json.loads(message)
        self.condition_object.acquire()
        self.condition_object.notify()
        self.condition_object.release()

    def game_window_closed(self, message, client):
        logger.debug(f"Game Window Closed")
        self.stop_game()

        if self.ai_process:
            self.ai_process.terminate()
            self.ai_process.wait()

        self.client = None

        if self.stop_if_game_windows_close:
            logger.debug("Stop server")
            self.server.shutdown()

    def start_game(self, game_path = '../science_birds/win-new/ScienceBirds.exe'):
        os_name = platform.system()
        if os_name == 'Windows':
            self.game_process = new(game_path, shell = False, stdout = subprocess.DEVNULL, stderr = subprocess.STDOUT)
        elif os_name == 'Darwin':
            os.system(f"open {game_path}")

    def startAi(self, start_level = -1, end_level = -1, print_ai_log = True, ai_path = None):

        if self.ai_process:
            self.ai_process.terminate()
            self.ai_process.wait()
            self.ai_process = None

        # Set the game into ai modus and define which level to be played
        message = [0, 'aimodus', f'{{"mode": true, "startLevel" : {start_level}, "endLevel": {end_level}}}']
        logger.debug(message)
        self.send(message)
        self.wait_for_response()

        if ai_path is None:
            ai_path = self.ai_path

        if print_ai_log:
            self.ai_process = new(f"java -jar {ai_path}", shell = False)
        else:
            self.ai_process = new(f"java -jar {ai_path}", shell = False, stdout = subprocess.DEVNULL, stderr = subprocess.STDOUT)

    def stopAI(self):

        message = [0, 'aimodus', 'true']
        self.send(message)
        self.wait_for_response()

        if self.ai_process:
            self.ai_process.terminate()
            self.ai_process.wait()

    def stop_components(self):
        self.stop_game()
        if self.ai_process:
            self.ai_process.terminate()
        self._stop_event.set()

    def new_client(self, client):
        logger.debug(f"New game window connected {client}")
        self.client = client
        self.condition_object.acquire()
        self.condition_object.notify()
        self.condition_object.release()

    def send(self, msg):
        self.response = None
        self.client.send(json.dumps(msg))

    def wait_for_game_window(self):
        counter = 0
        self.condition_object.acquire()
        while self.client is None:
            logger.debug(f"Waiting for client window: {counter}")
            self.condition_object.wait()

    def load_level_menu(self):
        logger.debug("Load level scene")
        message = [0, 'loadscene', {'scene': 'LevelSelectMenu'}]
        self.send(message)
        self.wait_for_response()
        response = None
        while True:
            if response is not None and 'data' in response[1] and response[1]['data'] == "True":
                break

            logger.debug(f"In loop: {response}")
            logger.debug("Level Menu is loaded")
            message = [0, 'levelsloaded']
            self.send(message)
            response = self.wait_for_response()
            time.sleep(0.2)

    def wait_till_all_level_played(self):
        response = None
        while True:
            if response is not None and 'data' in response[1] and response[1]['data'] == "True":
                break

            logger.debug("Wait for level played")
            message = [0, 'alllevelsplayed']
            self.send(message)
            response = self.wait_for_response()
            time.sleep(2)

    def change_level(self, index = 0):
        message = [0, 'selectlevel', {'levelIndex': index}]
        self.send(message)
        self.wait_for_response()

    def stop_game(self):
        os_name = platform.system()
        if os_name == 'Windows':
            if self.game_process:
                self.game_process.terminate()
        elif os_name == 'Darwin':
            os.system("pkill ScienceBirds")

    def get_data(self):
        message = [0, 'getdata']
        self.send(message)
        received_data = self.wait_for_response()
        parsed = json.loads(received_data[1]['data'])
        logger.debug(json.dumps(parsed, indent = 4, sort_keys = True))

        return received_data

    def create_img_of_level(self):
        message = [0, 'screenshot']
        self.send(message)
        received_data = self.wait_for_response()
        return received_data[1]['data']

