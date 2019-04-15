# -*- coding: utf-8 -*-
# !/usr/bin/env python3

import simpy
import random as rd
import pandas as pd
from pylab import *
from itertools import product


def get_angle(origin, loc, angle):
    return abs(math.degrees(math.atan2(loc[1] - origin[1], loc[0] - origin[0])) - angle)


def zombie_color_grad(min_v, max_v, count):
    return (200 - count * 9, 255 - count * 6, 255 - count * 3)


def people_color_grad(p_min, p_max, p):
    x = int(((p - p_min) / p_max) * 245 + 5)
    return (255, 255 - x, 255 - x)


class Zombie:
    def __init__(self, alfa, beta, gamma, chi, country, loc=(289, 454)):
        self.country = country
        self.alfa = alfa
        self.beta = beta
        self.gamma = gamma
        self.brains = 0
        self.chi = chi
        self.loc = loc
        self.country.log_zombie("up")
        self.x = None
        self.y = None
        self.working = True
        self.leader = (rd.random() >= 0.95)
        self.origin = self.give_origin()
        self.angle = self.pick_angle()
        self.moves = [x for x in product([-1, 0, 1], [-1, 0, 1]) if x != (0, 0)]
        self.country.env.process(self.interact())

    def pick_angle(self):
        if self.leader:
            return rd.choice([30, 60, -30, -60, -120, 120])
        else:
            return None

    def give_origin(self):
        if self.leader:
            return self.loc
        else:
            return None

    def remove(self):
        self.country.log_zombie("down")
        self.working = False

    def move(self, type):
        if self.brains <= self.chi:
            if self.leader and rd.random() <= 0.5:
                options = list(map(lambda x: tuple(self.loc + np.array(x)), self.moves))
                new_loc = min(options, key=lambda x: get_angle(self.origin, x, self.angle))
                self.x = new_loc[0] - self.loc[0]
                self.y = new_loc[1] - self.loc[1]
            elif type == 0 or self.x is None:
                self.y = rd.randrange(-1, 2, 1)
                self.x = rd.randrange(-1, 2, 1)
                new_loc = (self.loc[0] + self.x, self.loc[1] + self.y)
            else:
                new_loc = (self.loc[0] + self.x * 2, self.loc[1] + self.y * 2)
            while self.country.map_boundaries[new_loc]:
                self.x = rd.randrange(-1, 2, 1)
                self.y = rd.randrange(-1, 2, 1)
                new_loc = (self.loc[0] + self.x, self.loc[1] + self.y)
            self.country.map_zombies[self.loc] -= 1
            self.loc = new_loc
            self.brains += 1
            self.country.map_zombies[self.loc] += 1
        else:
            self.country.map_zombies[self.loc] -= 1
            self.remove()

    def interact(self):
        yield self.country.env.timeout(rd.random())
        while self.working:
            dead = 0
            if self.country.map_people[self.loc] > 0:
                prawd_kill = rd.random()
                prawd_infect = rd.random()
                if prawd_kill > self.alfa:
                    self.country.map_zombies[self.loc] -= 1
                    yield self.country.env.timeout(rd.random() * 2)
                    dead = 1
                    break

                if self.beta < prawd_infect < self.gamma:
                    Zombie(self.country.alfa_pop, self.country.beta_pop, self.country.gamma_pop, self.country.chi_pop,
                           self.country, self.loc)
                    self.country.map_people[self.loc] -= 1
                    self.country.map_zombies[self.loc] += 1
                    yield self.country.env.timeout(rd.random())
                elif prawd_infect >= self.gamma:
                    self.country.map_people[self.loc] -= 1
                    self.brains = 0
                    yield self.country.env.timeout(rd.random() * 2)
                else:
                    yield self.country.env.timeout(rd.random())
                type = 0

            else:
                type = 1
                yield self.country.env.timeout(rd.random())

            self.move(type)

        if dead == 1:
            self.remove()


class country:
    def __init__(self, alfa_pop, beta_pop, gamma_pop, chi_pop, map_values, map_colors):
        self.map_people = np.floor(np.divide(map_values, 38))
        self.map_colors = map_colors
        self.map_colors_people = self.map_colors.copy()
        self.map_colors_zombies = self.map_colors.copy()
        self.map_zombies = np.zeros(self.map_people.shape, dtype="uint8")
        self.map_boundaries = self.generate_boundaries()
        self.alfa_pop = alfa_pop
        self.beta_pop = beta_pop
        self.gamma_pop = gamma_pop
        self.chi_pop = chi_pop
        self.zombie_counter = 0
        self.env = simpy.Environment()
        self.df = pd.DataFrame(columns=('t', 'population', 'zombies'))
        self.result = []
        self.max_people = np.max(self.map_people)
        self.max_zombie = self.max_people * 2
        self.min_people = np.min(self.map_people)
        print("Country initialized")

    def generate_boundaries(self):
        map_boundaries = np.zeros(self.map_people.shape, dtype="uint8")
        where = np.where(self.map_people == 0)
        where_len = len(where[0])
        print(where)
        for x in range(where_len):
            if self.map_people[where[0][x], where[1][x]] == 0:
                map_boundaries[where[0][x], where[1][x]] = 1
            else:
                print("whops! => {}".format((where[0][x], where[1][x])))
        return map_boundaries

    def map_plots(self):
        for i in product(range(self.map_colors_zombies.shape[0] - 1), range(self.map_colors_zombies.shape[1] - 1)):
            if self.map_boundaries[i] == 0:
                if self.map_zombies[i] != 0:
                    self.map_colors_zombies[i] = zombie_color_grad(0, self.max_zombie, self.map_zombies[i])
                else:
                    self.map_colors_zombies[i] = people_color_grad(self.min_people, self.max_people, self.map_people[i])

        plt.figure(1).clear()
        plt.figure(1, figsize=(16, 9))
        plt.imshow(self.map_colors_zombies)
        plt.savefig(
            "map_{}_{}_{}.png".format(int(self.env.now), int(self.zombie_counter), int(np.sum(self.map_people))),
            dpi=400)
        # plt.show()

    def update_map(self):
        for i in product(range(self.map_people.shape[0] - 1), range(self.map_people.shape[1] - 1)):
            self.map_people[i] = int(self.map_people[i])

    def log_zombie(self, direction):
        if direction == "up":
            self.zombie_counter += 1
        elif direction == "down":
            self.zombie_counter -= 1

        # set condition when to save a plot of simulation
        if self.zombie_counter % 5000 == 0:
            self.map_plots()


    def all_dead(self):
        while True:
            no_people = np.sum(self.map_people)
            no_zombies = self.zombie_counter

            if self.env.now % 2:
                self.df = self.df.append(
                    pd.DataFrame({'t': [self.env.now], 'population': [no_people], 'zombies': [no_zombies]}))

            if self.env.now > 0 and (no_people == 0 or no_zombies == 0):
                print("C1:{} C2:{} Time:{}".format(no_people, no_zombies, self.env.now))
                self.result.append((self.env.now, no_people, no_zombies))
                self.finish_event.succeed()
            else:
                yield self.env.timeout(1)

    def run(self):
        Zombie(self.alfa_pop, self.beta_pop, self.gamma_pop, self.chi_pop, self)
        self.finish_event = self.env.event()
        self.env.process(self.all_dead())  # well, sort of dead
        print("Simulation started: {}".format(datetime.datetime.now()))
        self.env.run(until=self.finish_event)
        self.map_plots()
        print("Simulation finished: {}".format(datetime.datetime.now()))
        return self.df
