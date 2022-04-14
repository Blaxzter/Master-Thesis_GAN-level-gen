import sys
sys.path.append('./src')
from datetime import datetime
import time
import numpy as np
sys.path.append('..')
from threading import Thread
import random
import json
import socket
from math import cos, sin, degrees, pi
from client.agent_client import AgentClient, GameState, RequestCodes
from trajectory_planner.trajectory_planner import SimpleTrajectoryPlanner
from computer_vision.GroundTruthReader import GroundTruthReader,NotVaildStateError
from computer_vision.game_object import GameObjectType
from utils.point2D import Point2D
from pathlib import Path
import scipy.misc
from PIL import Image

class ScreenshotAgent(Thread):
    """agent which takes screenshot of each level and save them to file at ./screenshots"""
    def __init__(self):
        #Wrapper of the communicating messages

        with open('./src/client/server_client_config.json', 'r') as config:
            sc_json_config = json.load(config)

        self.ar = AgentClient(**sc_json_config[0])

        with open('./src/client/server_observer_client_config.json', 'r') as observer_config:
            observer_sc_json_config = json.load(observer_config)

        try:
            self.ar.connect_to_server()
        except socket.error as e:
            print("Error in client-server communication: " + str(e))

        self.current_level = -1
        self.failed_counter = 0
        self.solved = []
        self.tp = SimpleTrajectoryPlanner()
        self.id = 28888
        self.first_shot = True
        self.prev_target = None

        self.directory = "./screenshots"
        Path(self.directory).mkdir(parents=True, exist_ok=True)

    def update_no_of_levels(self):
        # check the number of levels in the game
        n_levels = self.ar.get_number_of_levels()

        # if number of levels has changed make adjustments to the solved array
        if n_levels > len(self.solved):
            for n in range(len(self.solved), n_levels):
                self.solved.append(0)

        if n_levels < len(self.solved):
            self.solved = self.solved[:n_levels]

        print('No of Levels: ' + str(n_levels))

        return n_levels

    def run(self):
        sim_speed = 50
        self.ar.configure(self.id)
        self.ar.set_game_simulation_speed(sim_speed)
        n_levels = self.update_no_of_levels()


        for l in range(n_levels):
            self.ar.load_level(l)
            state = self.ar.get_game_state()
            while (state != GameState.PLAYING):
                state = self.ar.get_game_state()
            self.ar.fully_zoom_out()
            time.sleep(0.2)
            img = self.ar.do_screenshot()
            file_name = str(l) + '-1' +".png"
            file_path = self.directory + "/" + file_name

            im = Image.fromarray(img)
            im.save(file_path)


            img = self.ar.do_screenshot()
            file_name = str(l) + '-2' +".png"
            file_path = self.directory + "/" + file_name

            im = Image.fromarray(img)
            im.save(file_path)


            img = self.ar.do_screenshot()
            file_name = str(l) + '-3' +".png"
            file_path = self.directory + "/" + file_name

            im = Image.fromarray(img)
            im.save(file_path)

if __name__ == "__main__":
    na = ClientNaiveAgent()
    na.run()
