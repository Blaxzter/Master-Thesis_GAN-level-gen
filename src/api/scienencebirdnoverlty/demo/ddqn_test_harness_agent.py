'''
MIT License

Copyright (c) 2018-2020 Ekaterina Nikonova,
Research School of Computer Science, Australian National University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This version of the agent is based on the work presented in: https://arxiv.org/abs/1910.01806

When using this work please cite:

'''

from __future__ import division

import numpy as np
import random
import tensorflow as tf
import tensorflow.contrib.slim as slim
import imageio
import math
import socket
import json
import scipy.misc
import shutil
import os
from PIL import ImageFile
from threading import Thread
import time
try:
    from client.agent_client import AgentClient, GameState, RequestCodes
    from trajectory_planner.trajectory_planner import SimpleTrajectoryPlanner
    from computer_vision.GroundTruthReader import GroundTruthReader,NotVaildStateError
    from computer_vision.game_object import GameObjectType
    from utils.point2D import Point2D
    from computer_vision.GroundTruthTest import GroundTruthTest

except ModuleNotFoundError:
    from src.client.agent_client import AgentClient, GameState, RequestCodes
    from src.trajectory_planner.trajectory_planner import SimpleTrajectoryPlanner
    from src.computer_vision.GroundTruthReader import GroundTruthReader,NotVaildStateError
    from src.computer_vision.game_object import GameObjectType
    from src.computer_vision.GroundTruthTest import GroundTruthTest

# Actions x y in domain of
ImageFile.LOAD_TRUNCATED_IMAGES = True



# Both scores are reset after finishing


# DRL PARAMETERS
START_EPSILON = 0.13 # Start exploring with this probability
END_EPSILON = 0.1  # Finish exploring on this probability
DECAY_STEPS = 4000000  # How many steps epsilon should be decayed from s to end
BATCH_SIZE = 64
UPDATE_FREQUENCY = 4  # Update target q network towards online dqn
DISCOUNT = .99  # Discount for target Q values
TOTAL_STEPS = 10000000  # Upper bound on number of steps (not episodes)
MODEL_PATH = "./RL/Models/ddqn_model_testharness_multi_eval"  # Where to save the model
ORIG_MODEL_PATH ="./RL/Models/ddqn_model_testharness_multi_eval"
#ORIG_MODEL_PATH = "./RL/Models/ddqn_model_testharness_multi"
SAVED_MODEL_PATH = "./RL/Models/ddqn_model_testharness_multi_eval" # Where to back up models
SUMMARY_PATH = "./ddqn_summaries/{ddqn_model_testharness_multi_eval_"
OUT_SIZE = 512  # Size of conv4 that will be splitted to a and v
UPDATE_RATE = 0.001  # Update target q network towards online with this rate
EXP_BUFFER_MAX_SIZE = 1000000

OFFSET = 0
TOTAL_ACTIONS = 50 # 0=10, 50=60

class StateMaker():
    def __init__(self):
        # Crops 480x840x3 picture to 310x770x3 and
        # then resizes it to 84x84x3
        # also normalizes the pixel values to -1,1 range
        # Important: pass png without alpha channel
        with tf.variable_scope("state_processor"):
            self.input_state = tf.placeholder(shape=[480, 840, 3], dtype=tf.float32)
            self.output = tf.image.per_image_standardization(self.input_state)
            self.output = tf.image.crop_to_bounding_box(self.output, 80, 20, 310, 770)
            self.output = tf.image.resize_images(
                self.output, [84, 84], method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)
            self.output = tf.squeeze(self.output)

    def make(self, sess, state):
        return sess.run(self.output, {self.input_state: state})

    





class SummaryStorage():
    def __init__(self, scope="summary", dir=None):
        self.scope = scope
        self.summary_writer = None
        with tf.variable_scope(scope):
            if dir:
                summary_dir = os.path.join(dir, "summaries_{}".format(scope))
                if not os.path.exists(summary_dir):
                    os.makedirs(summary_dir)
                self.summary_writer = tf.summary.FileWriter(summary_dir)

# go through online vars, update the offline vars with online var * update rate + (1-update rate) * offline var
def updateTargetTF(variables, update_rate):
    parameters = []
    for i, variable in enumerate(variables[0:len(variables) // 2]):
        parameters.append(variables[i+len(variables)//2].assign( (variable.value()*update_rate) + ((1-update_rate) * variables[i+len(variables)//2].value()) ))
    return parameters


def updateTarget(parameters, sess):
    for p in parameters:
        sess.run(p)

class DDQN():
    # Model of our `age`nt, follows the original DQN + dueling + double
    # defined in the Nature paper and other Google DeepMind papers
    # Note: out_size here is the size of the last conv layer output
    #
    # More on DQN look at Nature DeepMind paper
    def __init__(self, out_size):
        self.imageIn = tf.placeholder(shape=[None, 84, 84, 3], dtype=tf.float32, name="X")
        self.imageIn = tf.reshape(self.imageIn, shape=[-1, 84, 84, 3])
        self.conv1 = slim.conv2d( inputs=self.imageIn,
                                  num_outputs=32,
                                  kernel_size=[8, 8],
                                  stride=[4, 4],
                                  padding='VALID',
                                  biases_initializer=None)
        self.conv2 = slim.conv2d(inputs=self.conv1,
                                 num_outputs=64,
                                 kernel_size=[4, 4],
                                 stride=[2, 2],
                                 padding='VALID',
                                 biases_initializer=None)
        self.conv3 = slim.conv2d(inputs=self.conv2,
                                 num_outputs=64,
                                 kernel_size=[3, 3],
                                 stride=[1, 1],
                                 padding='VALID',
                                 biases_initializer=None)
        self.conv4 = slim.conv2d(inputs=self.conv3,
                                 num_outputs=out_size,
                                 kernel_size=[7, 7],
                                 stride=[1, 1],
                                 padding='VALID',
                                 biases_initializer=None)

        # Dueling DQN implementation
        # Split the output of the last convolution layer to advantage and value
        #
        # More on dueling DQN here: "Dueling Network Architectures for Deep RL" https://arxiv.org/pdf/1511.06581.pdf
        self.advantages_raw, self.values_raw = tf.split(self.conv4, 2, 3) #split 512 to 2 streams
        self.advantages_flatten      = slim.flatten(self.advantages_raw) # 256x1
        self.values_flatten          = slim.flatten(self.values_raw) # 256x1

        # Initialize the weights with xavier
        # More info on why xavier here: proceedings.mlr.press/v9/glorot10a/glorot10a.pdf
        xavier = tf.contrib.layers.xavier_initializer()
        self.advantages_weights = tf.Variable(xavier([256, TOTAL_ACTIONS]) ) # 256x90 usefulness of actions
        self.values_weights     = tf.Variable(xavier([256, 1])) # 256x1 usefulness of state
        self.advantages         = tf.matmul(self.advantages_flatten, self.advantages_weights)
        self.values             = tf.matmul(self.values_flatten, self.values_weights)

        # Formula taken from original paper:
        # Q(s,a,delta,alpha,beta) = V(s,delta,beta) + ( A(s,a,delta,alpha)- (1/|A|)*sum_i(A(s,a_i,delta,alpha)) )
        # Q(s,a,delta,alpha,beta) = V(s,delta,beta) + ( A(s,a,delta,alpha)- (1/|A|)*sum_i(A(s,a_i,delta,alpha)) )
        self.q_values = self.values + tf.subtract(self.advantages, tf.reduce_mean(self.advantages, axis=1, keep_dims=True))
        self.best_q = tf.argmax(self.q_values, 1) # get the best one

        # Calculate the loss between target(offline) and online NN, taken from original DQN
        self.target_q = tf.placeholder(shape=[None], dtype=tf.float32)
        self.actions = tf.placeholder(shape=[None], dtype=tf.int32)
        self.actions_onehot = tf.one_hot(self.actions, TOTAL_ACTIONS, dtype=tf.float32) # get 1's in choosen action
        self.predicted_q = tf.reduce_sum(tf.multiply(self.q_values, self.actions_onehot), axis=1)
        # RMSOptimization
        self.loss = tf.reduce_mean(tf.square(self.target_q - self.predicted_q))
        self.adam = tf.train.AdamOptimizer(learning_rate=0.0001)
        self.optimized = self.adam.minimize(self.loss)

        # Store summaries
        self.summaries = tf.summary.merge([
            tf.summary.scalar("loss", self.loss),
            tf.summary.histogram("q values", self.q_values),
            tf.summary.histogram("predictions", self.best_q)
        ])

class ClientRLAgent(Thread):
    def __init__(self):
        # Wrapper of the communicating messages
        with open('./src/client/server_client_config.json', 'r') as config:
            sc_json_config = json.load(config)
        self.ar = AgentClient(**sc_json_config[0])
        try:
            self.ar.connect_to_server()
        except socket.error as e:
            print("Error in client-server communication: " + str(e))
        self.level_count = 0
        self.failed_counter = 0
        self.solved = []
        self.tp = SimpleTrajectoryPlanner()
        self.sling_center = None
        self.sling_mbr = None
        self.id = 28888
        self.first_shot = True
        self.prev_target = None

        self.model = np.loadtxt("model", delimiter=",")
        self.target_class = list(map(lambda x: x.replace("\n", ""), open('target_class').readlines()))

    def get_slingshot_center(self):
        try:
            ground_truth = self.ar.get_ground_truth_without_screenshot()
            ground_truth_reader = GroundTruthReader(ground_truth, self.model, self.target_class)
            sling = ground_truth_reader.find_slingshot_mbr()[0]
            sling.width, sling.height = sling.height, sling.width
            self.sling_center = self.tp.get_reference_point(sling)
            self.sling_mbr = sling

        except NotVaildStateError:
            self.ar.fully_zoom_out()
            ground_truth = self.ar.get_ground_truth_without_screenshot()
            ground_truth_reader = GroundTruthReader(ground_truth, self.model, self.target_class)
            sling = ground_truth_reader.find_slingshot_mbr()[0]
            sling.width, sling.height = sling.height, sling.width
            self.sling_center = self.tp.get_reference_point(sling)
            self.sling_mbr = sling

    def update_no_of_levels(self):
        # check the number of levels in the game
        n_levels = self.ar.get_number_of_levels()

        # if number of levels has changed make adjustments to the solved array
        if n_levels > len(self.solved):
            for n in range(len(self.solved), n_levels):
                self.solved.append(0)

        if n_levels < len(self.solved):
            self.solved = self.solved[:n_levels]

        # self.logger.info('No of Levels: ' + str(n_levels))

        return n_levels

    def check_my_score(self):
        """
         * Run the Client (Naive Agent)
        *"""
        scores = self.ar.get_all_level_scores()
        #print(" My score: ")
        level = 1
        for i in scores:
            self.logger.info(" level ", level, "  ", i)
            if i > 0:
                self.solved[level - 1] = 1
            level += 1
        return scores

class ExperienceReplay():
    def __init__(self, memory_size=10000000):
        self.memory = []
        self.memory_size = memory_size

    # Adds observations to memory
    def remember(self, observation):
        if(len(self.memory) > 18000):
            del self.memory[0:1000]
        self.memory.extend(observation)

    # Randomly samples memory
    def sample(self, sample_size):
        return np.reshape(random.sample(self.memory, sample_size), [sample_size, 5]) # s,a,r,s',d

class MultiDQN():

    def __init__(self):
        # TRAINING/ EVALUATION SWITCH Parameters
        self.IS_IN_TRAINING_MODE = True  # indicates if the agent is in training mode, switching it off will stop agent from training
        self.EXPLORATION_EPSILON_BEFORE_EVAL = 0.13  # just needed to preserve exploration after evaluation is done
        self.EVAL_LEVELS_NUMBER = 51  # total number of eval levels
        self.TRAIN_LEVELS_NUMBER = 1501  # total number of train levels
        self.TRAINING_SCORES = np.zeros([self.TRAIN_LEVELS_NUMBER,
                                    3])  # 300 training levels, for each level we have: level score, Won or Not?, Num of birds used
        self.EVAL_SCORES = np.zeros([self.EVAL_LEVELS_NUMBER,
                                3])  # 50 evaluation levels, for each level we have: level score, Won or Not?, Num of birds used
        # TRAINING_SET_TIMES = 0 # num of times all train levels were played
        # EVAL_SET_TIMES = -1 # num of times all eval levels were played

    def reset_agent(self, sess, saver, memory, my_multiid):
        print("Reseting agent")
        if (len(os.listdir(ORIG_MODEL_PATH + "_" + str(my_multiid))) > 0):
            print('Loading Model...')
            checkpoint = tf.train.get_checkpoint_state(ORIG_MODEL_PATH + "_" + str(my_multiid))
            saver.restore(sess, checkpoint.model_checkpoint_path)
        memory.memory = []
        self.IS_IN_TRAINING_MODE = True  # indicates if the agent is in training mode, switching it off will stop agent from training
        self.EXPLORATION_EPSILON_BEFORE_EVAL = 0.13  # just needed to preserve exploration after evaluation is done

    def run(self, my_multiid):
        try:

            rl_client = ClientRLAgent()
            memory = ExperienceReplay()
            # Properties
            tf.reset_default_graph()
            online_QN = DDQN(OUT_SIZE)
            target_QN = DDQN(OUT_SIZE)
            init = tf.global_variables_initializer()
            saver = tf.train.Saver()
            trainable_variables = tf.trainable_variables()
            targetParams = updateTargetTF(trainable_variables, UPDATE_RATE)

            # Where we save our checkpoints and graphs
            summary_dir = os.path.abspath(SUMMARY_PATH + "_" + str(my_multiid) + "}")
            summary_writer = SummaryStorage(scope="summary", dir=summary_dir)

            epsilon = START_EPSILON
            decay_step = (START_EPSILON - END_EPSILON) / DECAY_STEPS
            state_maker = StateMaker()

            highest_total_score_TRAIN = 0
            highest_total_score_EVAL = 0

            if not os.path.exists(MODEL_PATH + "_" + str(my_multiid)):
                os.makedirs(MODEL_PATH + "_" + str(my_multiid))

            with tf.Session() as sess:
                sess.run(init)

                if os.path.exists(ORIG_MODEL_PATH + "_" + str(my_multiid)):
                    if (len(os.listdir(ORIG_MODEL_PATH + "_" + str(my_multiid))) > 0):
                        print('Loading Model...')
                        checkpoint = tf.train.get_checkpoint_state(ORIG_MODEL_PATH + "_" + str(my_multiid))
                        saver.restore(sess, checkpoint.model_checkpoint_path)

                # Run loop
                info = rl_client.ar.configure(rl_client.id)
                rl_client.ar.set_game_simulation_speed(100)
                rl_client.solved = [0 for x in range(rl_client.ar.get_number_of_levels())]
                scores = rl_client.ar.get_all_level_scores()

                max_scores = np.zeros([len(rl_client.solved)])

                rl_client.ar.load_next_available_level()
                rl_client.level_count += 1

                s = 'None'
                s_previous = 'None'
                r_previous = 0
                a_previous = 0
                r_average = 0
                r_total = 0
                r = 0
                all_levels_played_count = 0
                d = False

                first_time_in_level_in_episode = True

                for env_step in range(1, TOTAL_STEPS):
                    game_state = rl_client.ar.get_game_state()
                    r = rl_client.ar.get_current_score()
                    print("REWARD: " + str(r))

                    if game_state == GameState.REQUESTNOVELTYLIKELIHOOD:
                        # Require report novelty likelihood and then playing can be resumed
                        # dummy likelihoods:
                        print("REQUESTNOVELTYLIKELIHOOD")
                        novelty_likelihood = 0.9
                        non_novelty_likelihood = 0.1
                        novel_obj_ids = {1, -2, -398879789}
                        novelty_level = 0
                        novelty_description = ""
                        rl_client.ar.report_novelty_likelihood(novelty_likelihood, non_novelty_likelihood, novel_obj_ids,
                                                          novelty_level, novelty_description)
                    elif game_state == GameState.NEWTRIAL:
                        print("NEWTRIAL")
                        # Make a fresh agent to continue with a new trial (evaluation)
                        self.reset_agent(sess, saver, memory, my_multiid)
                        s = 'None'
                        s_previous = 'None'
                        r_previous = 0
                        a_previous = 0
                        r_average = 0
                        r_total = 0
                        r = 0
                        all_levels_played_count = 0
                        d = False

                        first_time_in_level_in_episode = True
                        (time_limit, interaction_limit, n_levels, attempts_per_level, mode, seq_or_set,
                         allowNoveltyInfo) = rl_client.ar.ready_for_new_set()
                    elif game_state == GameState.NEWTESTSET:
                        # DO something to clone a test only agent that does not learn
                        print("NEWTESTSET")
                        self.reset_agent(sess, saver, memory, my_multiid)
                        s = 'None'
                        s_previous = 'None'
                        r_previous = 0
                        a_previous = 0
                        r_average = 0
                        r_total = 0
                        r = 0
                        all_levels_played_count = 0
                        d = False

                        first_time_in_level_in_episode = True
                        self.IS_IN_TRAINING_MODE = False
                        (time_limit, interaction_limit, n_levels, attempts_per_level, mode, seq_or_set,
                         allowNoveltyInfo) = rl_client.ar.ready_for_new_set()
                        # rl_client.ar.ready_for_new_set()
                    elif game_state == GameState.NEWTRAININGSET:
                        # DO something to resume the training agent
                        print("NEWTRAININGSET")
                        self.reset_agent(sess, saver, memory, my_multiid)
                        s = 'None'
                        s_previous = 'None'
                        r_previous = 0
                        a_previous = 0
                        r_average = 0
                        r_total = 0
                        r = 0
                        all_levels_played_count = 0
                        d = False

                        first_time_in_level_in_episode = True
                        self.IS_IN_TRAINING_MODE = True
                        (time_limit, interaction_limit, n_levels, attempts_per_level, mode, seq_or_set,
                         allowNoveltyInfo) = rl_client.ar.ready_for_new_set()
                        # rl_client.ar.ready_for_new_set()
                    elif game_state == GameState.RESUMETRAINING:
                        print("RESUMETRAINING")
                        self.reset_agent(sess, saver, memory, my_multiid)
                        s = 'None'
                        s_previous = 'None'
                        r_previous = 0
                        a_previous = 0
                        r_average = 0
                        r_total = 0
                        r = 0
                        all_levels_played_count = 0
                        d = False

                        first_time_in_level_in_episode = True
                        self.IS_IN_TRAINING_MODE = True
                        (time_limit, interaction_limit, n_levels, attempts_per_level, mode, seq_or_set,
                         allowNoveltyInfo) = rl_client.ar.ready_for_new_set()
                    elif game_state == GameState.EVALUATION_TERMINATED:
                        print("EVALUATION_TERMINATED")
                        # store info and disconnect the agent as the evaluation is finished
                        print("Done evaluating")
                        exit(1)
                        pass

                    if (self.IS_IN_TRAINING_MODE == True and (
                            game_state == GameState.NEWTRAININGSET or game_state == GameState.RESUMETRAINING)):
                        # Training
                        #EVAL_SET_TIMES += 1
                        if (highest_total_score_EVAL < self.EVAL_SCORES[:, 0].sum(0)):
                            highest_total_score_EVAL = self.EVAL_SCORES[:, 0].sum(0)
                        print("Training mode... interactions so far: " + str(
                            env_step) + " current total score of evaluation set: " + str(self.EVAL_SCORES[:, 0].sum(0)) +
                              " highest ever total score: " + str(highest_total_score_EVAL) + " agent id: " +str(my_multiid))

                        # Start exploring
                        epsilon = self.EXPLORATION_EPSILON_BEFORE_EVAL

                        # Write training results to tensorboard
                        episode_summary = tf.Summary()
                        episode_summary.value.add(simple_value=self.EVAL_SCORES[:, 0].sum(0), tag="eval_total_reward")
                        episode_summary.value.add(simple_value=self.EVAL_SCORES[:, 1].sum(0), tag="eval_total_solved")
                        episode_summary.value.add(simple_value=highest_total_score_EVAL,
                                                  tag="eval_highest_ever_total_score")
                        summary_writer.summary_writer.add_summary(episode_summary, OFFSET + env_step)
                        summary_writer.summary_writer.flush()

                        s = "None"
                        s_previous = "None"
                        r_previous = 0
                        a_previous = 0
                        r_total = 0
                        self.EVAL_SCORES = np.zeros([self.EVAL_LEVELS_NUMBER, 3])

                        # rl_client.ar.restart_level()

                    if (self.IS_IN_TRAINING_MODE == False and game_state == GameState.NEWTESTSET):
                        # EVALUATION
                        #TRAINING_SET_TIMES += 1
                        if (highest_total_score_TRAIN < self.TRAINING_SCORES[:, 0].sum(0)):
                            highest_total_score_TRAIN = self.TRAINING_SCORES[:, 0].sum(0)
                        print("Evaluating Agent... interactions so far: " + str(
                            env_step) + " current total score of training set: " + str(self.TRAINING_SCORES[:, 0].sum(0)) +
                              " highest ever total score: " + str(highest_total_score_TRAIN) + " agent id: " +str(my_multiid))

                        # Stop exploring
                        self.EXPLORATION_EPSILON_BEFORE_EVAL = epsilon
                        epsilon = 0.00001

                        # Write training results to tensorboard
                        episode_summary = tf.Summary()
                        episode_summary.value.add(simple_value=self.TRAINING_SCORES[:, 0].sum(0), tag="train_total_reward")
                        episode_summary.value.add(simple_value=self.TRAINING_SCORES[:, 1].sum(0), tag="train_total_solved")
                        episode_summary.value.add(simple_value=highest_total_score_TRAIN,
                                                  tag="train_highest_ever_total_score")
                        summary_writer.summary_writer.add_summary(episode_summary, OFFSET + env_step)
                        summary_writer.summary_writer.flush()

                        s = "None"
                        s_previous = "None"
                        r_previous = 0
                        a_previous = 0
                        r_total = 0
                        self.TRAINING_SCORES = np.zeros([self.TRAIN_LEVELS_NUMBER, 3])

                    if (s != 'None' and (
                            game_state == GameState.PLAYING or game_state == GameState.WON or game_state == GameState.LOST)):
                        # save previous state
                        s_previous = s
                        r_previous = r
                        a_previous = a

                    # First check if we are in the won or lost state
                    # to adjust the reward and done flag if needed
                    if game_state == GameState.WON:
                        print("WON")
                        self.shoots_before_level_is_completed = 0
                        # save current state before reloading the level
                        # r = rl_client.ar.get_current_score()
                        s = rl_client.ar.do_screenshot()
                        s = state_maker.make(sess, s)

                        if (self.IS_IN_TRAINING_MODE == True):
                            self.TRAINING_SCORES[rl_client.level_count, :] = [rl_client.ar.get_current_score(), 1,
                                                                           OFFSET + env_step]
                        else:
                            self.EVAL_SCORES[rl_client.level_count, :] = [rl_client.ar.get_current_score(), 1,
                                                                       OFFSET + env_step]

                        rl_client.update_no_of_levels()
                        scores = rl_client.ar.get_all_level_scores()

                        rl_client.check_my_score()
                        rl_client.ar.load_next_available_level()
                        rl_client.level_count += 1

                        # Update reward and done
                        d = 1
                        r_previous *= 1
                        r_total += r_previous
                        first_time_in_level_in_episode = True


                    elif game_state == GameState.LOST:
                        print("LOST")
                        self.shoots_before_level_is_completed = 0
                        # save current state before reloading the level
                        # r = rl_client.ar.get_current_score()
                        s = rl_client.ar.do_screenshot()
                        s = state_maker.make(sess, s)

                        # check for change of number of levels in the game
                        rl_client.update_no_of_levels()
                        rl_client.check_my_score()

                        if (self.IS_IN_TRAINING_MODE == True):
                            self.TRAINING_SCORES[rl_client.level_count, :] = [rl_client.ar.get_current_score(), 0,
                                                                           OFFSET + env_step]
                        else:
                            self.EVAL_SCORES[rl_client.level_count, :] = [rl_client.ar.get_current_score(), 0,
                                                                       OFFSET + env_step]

                        # If lost, then restart the level
                        rl_client.failed_counter += 1
                        if rl_client.failed_counter >= 0:  # for testing , go directly to the next level

                            rl_client.failed_counter = 0
                            rl_client.ar.load_next_available_level()
                            rl_client.level_count += 1


                        else:
                            #print("restart")
                            rl_client.ar.restart_level()

                        # Update reward and done
                        d = 1
                        r_previous *= -1
                        first_time_in_level_in_episode = True

                    if (game_state == GameState.PLAYING):
                        # Start of the episode
                        #print("PLAYING")
                        # r = rl_client.ar.get_current_score()

                        # rl_client.get_slingshot_center()
                        # game_state = rl_client.ar.get_game_state()
                        #
                        # s, img = rl_client.ar.get_ground_truth_with_screenshot()

                        if (first_time_in_level_in_episode):
                            # If first time in level reset states so we dont
                            # carry previous states with us
                            s = 'None'
                            s_previous = 'None'
                            rl_client.ar.fully_zoom_out()  # Needed as we depend on fully zoom out values
                            rl_client.ar.fully_zoom_out()
                            rl_client.ar.fully_zoom_out()
                            rl_client.ar.fully_zoom_out()
                            rl_client.ar.fully_zoom_out()
                            rl_client.ar.fully_zoom_out()
                            rl_client.ar.fully_zoom_out()
                            first_time_in_level_in_episode = False

                        rl_client.get_slingshot_center()

                        s, img = rl_client.ar.get_ground_truth_with_screenshot()
                        # start = time.time()
                        #
                        # end = time.time()
                        # print("gt with screenshot: " + str(end - start))
                        #
                        # start = time.time()
                        # t1 = rl_client.ar.get_ground_truth_without_screenshot()
                        # end = time.time()
                        # print("gt without screenshot: " + str(end - start))
                        #
                        # start = time.time()
                        # t1, t2 = rl_client.ar.get_noisy_ground_truth_with_screenshot()
                        # end = time.time()
                        # print("noisy gt with screenshot: " + str(end - start))
                        #
                        # start = time.time()
                        # t1 = rl_client.ar.get_noisy_ground_truth_without_screenshot()
                        # end = time.time()
                        # print("noisy gt without screenshot: " + str(end - start))
                        #
                        # start = time.time()
                        # t1 = rl_client.ar.do_screenshot()
                        # end = time.time()
                        # print("screenshot only: " + str(end - start))

                        s = state_maker.make(sess, s)

                        # Greedy choice
                        if np.random.rand(1) < epsilon:
                            # Explore
                            a = np.random.randint(0, 49)
                            loss = 'None'
                            predicted_q_values = 'None'
                        else:
                            # Exploit
                            best_a = sess.run(online_QN.best_q, feed_dict={online_QN.imageIn: [s]})
                            a = best_a[0]

                        # convert 0-50 to 10-60
                        a += 10
                        # Convert simulator coordinates to pixels...
                        release_point = rl_client.tp.find_release_point(rl_client.sling_mbr, math.radians(a))
                        tap_time = int(1250)


                        # Execute a in the environment
                        if(self.shoots_before_level_is_completed > 20):
                            # 20 shots for a level... likely novelty 3 flip x, skip level
                            print("20 shots for a level... likely novelty 3 flip x, skip level")
                            rl_client.ar.load_next_available_level()
                            rl_client.level_count += 1

                        if not release_point:
                            # Add logic to deal with unreachable target
                            print("No release point is found")

                            release_point = Point2D(-int(40*math.cos(math.radians(a))), int(40*math.sin(math.radians(a))))

                        dx = int(release_point.X - rl_client.sling_center.X)
                        dy = int(release_point.Y - rl_client.sling_center.Y)
                        print("Shoot: " + str(int(rl_client.sling_center.X)) + ", " + str(int(rl_client.sling_center.Y)) + ", " + str(tap_time))
                        rl_client.ar.shoot_and_record_ground_truth(release_point.X, release_point.Y, 0, tap_time, 1)
                        self.shoots_before_level_is_completed += 1

                    elif game_state == GameState.LEVEL_SELECTION:
                        print("unexpected level selection page, go to the last current level")
                        self.shoots_before_level_is_completed = 0
                        rl_client.ar.load_next_available_level()
                        rl_client.level_count += 1
                        rl_client.novelty_existence = rl_client.ar.get_novelty_info()

                    elif game_state == GameState.MAIN_MENU:
                        print("unexpected main menu page, reload the level : ", rl_client.level_count)
                        self.shoots_before_level_is_completed = 0
                        rl_client.ar.load_next_available_level()
                        rl_client.level_count += 1
                        rl_client.novelty_existence = rl_client.ar.get_novelty_info()
                        # time.sleep(10)

                    elif game_state == GameState.EPISODE_MENU:
                        print("unexpected main menu page, reload the level : ", rl_client.level_count)
                        self.shoots_before_level_is_completed = 0
                        rl_client.ar.load_next_available_level()
                        rl_client.level_count += 1
                        rl_client.novelty_existence = rl_client.ar.get_novelty_info()

                    if (self.IS_IN_TRAINING_MODE == True and (
                            game_state == GameState.PLAYING or game_state == GameState.WON or game_state == GameState.LOST)):
                        # if (d and game_state == GameState.WON):
                        #     r_previous = 1
                        # elif (d and game_state == GameState.LOST):
                        #     r_previous = 0
                        # else:
                        #     r_previous = 0
                        r_previous = r_previous / 150000

                        if (s_previous != 'None'):
                            memory.remember(np.reshape(np.array([s_previous, a_previous, r_previous, s, d]),
                                                       [1, 5]))  # Save observation to memory

                        # Decay epsilon
                        if epsilon > END_EPSILON:
                            epsilon -= decay_step

                        if ((env_step % UPDATE_FREQUENCY) == 0) and len(memory.memory) > BATCH_SIZE:
                            train_batch = memory.sample(BATCH_SIZE)

                            # Double DQN update to target network ----------
                            # More info on update here: https://arxiv.org/pdf/1509.06461.pdf
                            # "Deep RL with Double Q-Learning"

                            # Feed next state to online qn
                            Q_online_best = sess.run(online_QN.best_q,
                                                     feed_dict={
                                                         online_QN.imageIn: np.reshape(np.vstack(train_batch[:, 3]),
                                                                                       [-1, 84, 84, 3])})

                            # Feed next state to offline qn
                            Q_offline = sess.run(target_QN.q_values,
                                                 feed_dict={target_QN.imageIn: np.reshape(np.vstack(train_batch[:, 3]),
                                                                                          [-1, 84, 84, 3])})

                            # is end? 0 : 1
                            was_end = -(train_batch[:, 4] - 1)

                            # Evaluate decision of online network using offline network. ----
                            # Double Q learning update: y = R_t+1 + discount * Q(S_t+1, argmax Q(S_t+1,a,online_params), offline_params)

                            # Get Q(S_t+1, argmax Q(S_t+1,a,online_params), offline_params),
                            # by selecting the best q values predicted by online network from offline network
                            double_Q = Q_offline[range(BATCH_SIZE), Q_online_best]

                            # Update target qs with train batch rewards + discounted target QN q values
                            target_Q = train_batch[:, 2] + (DISCOUNT * double_Q * was_end)

                            # Feed train batch, update the online network with target q
                            _, summaries = sess.run([online_QN.optimized, online_QN.summaries],
                                                    feed_dict={
                                                        online_QN.imageIn: np.reshape(np.vstack(train_batch[:, 0]),
                                                                                      [-1, 84, 84, 3]),
                                                        online_QN.target_q: target_Q,
                                                        online_QN.actions: train_batch[:, 1]})
                            summary_writer.summary_writer.add_summary(summaries, OFFSET + env_step)

                            updateTarget(targetParams, sess)  # Update the target qn to online qn with some update rate

                            # Store the summaries
                            episode_summary = tf.Summary()
                            episode_summary.value.add(simple_value=r, tag="reward")
                            episode_summary.value.add(simple_value=a, tag="action_xy")
                            episode_summary.value.add(simple_value=tap_time, tag="tap_time")
                            episode_summary.value.add(simple_value=epsilon, tag="epsilon")
                            if ((rl_client.level_count % 50) == 0):
                                # Store the summaries
                                # if(all_levels_played_count == 3):
                                episode_summary.value.add(simple_value=r_total, tag="reward_total")
                                print("Total score over levels: " + str(r_total) + " agent id: " +str(my_multiid))
                                r_total = 0
                                all_levels_played_count += 1
                            summary_writer.summary_writer.add_summary(episode_summary, OFFSET + env_step)

                            summary_writer.summary_writer.flush()

                            # Save the model every 10 steps
                            saver.save(sess, MODEL_PATH + "_" + str(my_multiid) + '/model-' + str(OFFSET + env_step) + '.ckpt')
                            #print("Saved Model")






        except Exception as e:
            print("Error: ", e)
        finally:
            time.sleep(10)