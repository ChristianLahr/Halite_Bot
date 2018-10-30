#!/usr/bin/env python3


""" TO DO
- ship colisions   ship.position.directional_offset(test_direction) == occupied
- generate ships if shipyard is not occupied and outside ship class and fill ship_constants with id    game_map[me.shipyard].is_occupied
- generate dropoffs
- shipyard == dropoff? getdropof includes shipyard?
- in return to exploration radius: move to next position in exloration radius
- map_cell.mark_unsafe(ship) after every time I know the next position

"""
import hlt
from hlt import constants

import random
import logging
import numpy as np
import itertools


# This game object contains the initial game state.
game = hlt.Game()
# Respond with your name.
game.ready("Lahr_1")


class Shipping():

    def __init__(self, ship_, ship_constants, me_, exploration_radius_, exploration_area_, exploration_area_edges_):
        self.ship=ship_
        self.exploration_radius = exploration_radius_
        self.exploration_area = exploration_area_
        self.exploration_area_edges = exploration_area_edges_
        self.ship_status = ship_constants['ship_status']
        self.me = me_

        self.halite_threshold_to_move = 700
        self.halite_threshold_to_stay = 20
        self.halite_threshold_to_return = 900
        self.create_dropoff_distance = 5

    def next_cmd(self):
        if self.ship.position == self.me.shipyard.position and self.ship.halite_amount == 0: # move away from shipyard
            self.ship_status = 'return_to_explore'
            cmd, next_position = self.return_to_explore()
        elif self.ship.halite_amount > self.halite_threshold_to_return or self.ship_status == 'return_to_base': # if full return to base
            #print('########### return')
            cmd, next_position = self.return_to_base_or_drop()
        elif self.ship_status == 'return_to_base' and self.ship.halite_amount > 0:
            cmd, next_position = self.return_to_base_or_drop()
        elif self.ship_status == 'dropped': # dropped last round so know return to exploration radius
            cmd, next_position = self.return_to_explore()
            self.ship_status = 'return_to_explore'
        elif self.ship_status == 'explore' and not self.is_inside_exploration_radius():
            cmd, next_position = self.return_to_explore()
        elif self.ship_status == 'explore':  # just exploring
            cmd, next_position = self.explore()
        else:
            print('warning: no valid ship status so explore')
            cmd, next_position = self.explore()


        return cmd, next_position


    def is_inside_exploration_radius(self):
        return game_map.calculate_distance(self.ship.position, self.get_next_dropoff_position()) < self.exploration_radius


    def return_to_base_or_drop(self):

        next_position = self.ship.position

        if self.ship.position == self.me.shipyard.position and self.ship.halite_amount > 0:   # do dropoff
            cmd = self.ship.make_dropoff()
            self.ship_status = 'dropped'
            logging.info("Ship {} dropping halite.".format(ship.id))

        else:   # move towards dropoff
            next_dropoff_position = self.me.shipyard.position
            next_direction = game_map.naive_navigate(self.ship, next_dropoff_position)
            cmd = self.ship.move(next_direction)
            next_position = self.ship.position.directional_offset(self.direction_to_tuple(next_direction))
            logging.info("Ship {} moves toward dropoff.".format(ship.id))

        # go on returning
        self.ship_status = 'return_to_base'
        return cmd, next_position



    def return_to_explore(self):

        next_positions_distances = []
        for position in self.exploration_area:
            distance = game_map.calculate_distance(self.ship.position, position)
            next_positions_distances[(distance, position)]
        min_dist = np.array([dist_pos[0] for dist_pos in next_positions_distances])
        next_positions_minimal_distance = [dist_pos[1] for dist_pos in next_positions_distances if dist_pos[0] == min_dist]
        random_next_best_position = random.choice( next_positions_minimal_distance )
        cmd = self.ship.move(game_map.naive_navigate(self.ship, random_next_best_position))
        if next_position in self.exploration_area:
            self.ship_status = 'explore'
        else: self.ship_status = 'return_to_explore'
    logging.info("Ship {} returns to exploration area.".format(ship.id))
    return cmd, random_next_best_position


def direction_to_tuple(self, direction_str):
    if direction_str =='n' or direction_str == (1, 0):
        return hlt.positionals.Direction.North
    elif direction_str == 'e' or direction_str == (0, 1):
        return hlt.positionals.Direction.East
    elif direction_str == 's' or direction_str == (-1, 0):
        return hlt.positionals.Direction.South
    elif direction_str == 'w' or direction_str == (0, -1):
        return hlt.positionals.Direction.West
    else:
        #print(direction_str)
        #print('error in direction_to_tuple')
        return hlt.positionals.Direction.North


def opposit_direction(self, direction):
    if direction =='n':
        return 's'
    elif direction == 'e':
        return 'w'
    elif direction == 's':
        return 'n'
    elif direction == 'w':
        return 'e'
    else:
        print(direction)
        print('error in opposit direction')
        return 'n'

def get_next_dropoff_position(self):
    dropoffs = self.me.get_dropoffs()
    next_dropoff_positions = [dropoff.position for dropoff in dropoffs]
    next_dropoff_positions.append(me.shipyard.position)
    dist_min = 100000
    next_dropoff_position = next_dropoff_positions[ np.array([game_map.calculate_distance(self.ship.position, position) for position in next_dropoff_positions]).argmin() ]
    return next_dropoff_position


def explore(self):

    next_position = self.ship.position

    # if actual pos hast much halit stay
    stay = game_map[self.ship.position].halite_amount >= self.halite_threshold_to_stay
    if stay:
        game_map[self.ship.position].mark_unsafe(self.ship)
        return self.ship.stay_still(), self.ship.position

    elif self.exploration_radius > self.create_dropoff_distance and self.ship.position in self.exploration_area_edges:
        ### create dropoffs
        cmd = ship.make_dropoff()
        next_position = self.ship.position
        return cmd, next_position

    else: # move to good position
        # could also decide to set status to 'go_far' if next_position_radius1_max_halite is less than another threshold like 250 such that the ship moves faster to rentable hilite positions

        ### mode: min max coverage radius
        if self.ship.position in self.exploration_area:  # inside exploration_area?
            # enough halite in radius 1 of ship to move there
            next_position, n_halite = self.get_radius1_halite_max()
            cmd = self.ship.move(game_map.naive_navigate(self.ship, next_position))
            next_position
        else:   # retrun to exploration area
            cmd, next_position = self.return_to_explore()
            # hier ohne Status. Ist es bei anderen Fällen auch sinnvoll? Also einfach immer explore und falls nicht in area dann gehe richtung area...

        return cmd, next_position


def get_radius1_halite_max(self):

    possible_next_positions = self.ship.position.get_surrounding_cardinals() # ist die aktuelle position auch schon dabei?
    n_halite_max = game_map[self.ship.position].halite_amount
    next_position_max_halite = self.ship.position
    for position in possible_next_positions:
        n_halite = game_map[position].halite_amount
        if n_halite > n_halite_max:
            n_halite_max = n_halite
            next_position_max_halite = position
    return next_position_max_halite, n_halite






"""
#### move to exloration radius by north and else
        if self.is_inside_exploration_radius():
            next_position = self.ship.position.directional_offset(self.direction_to_tuple('n'))
            if game_map[next_position].is_occupied: # check if north is free!!!!!!!!!!!!!!!!!!!
                cmd = self.ship.stay_still()
                next_position = self.ship.position
            else:
                cmd = self.ship.move(game_map.naive_navigate(self.ship, ))
                next_position
            return cmd, next_position
        else:
"""




### logging
#logging.info("Ship {} has {} halite.".format(ship.id, ship.halite_amount))




def check_halite_radius_coverage(self, exploration_radius_positions):
    positions = exploration_radius_positions
    coverage = np.array([game_map[position].halite_amount for position in positions])
    max_coverage = coverage.max()
    n_covered = len([cov > self.halite_threshold_to_stay for cov in coverage])
    if max_coverage < self.halite_threshold_to_stay:
        return False
    else:
        return True


def get_exploration_radius_positions(self, position, radius, get_edges):
    eploration_edge_len = 1 + radius * 2
    exploration_radius_positions = []
    # go to first radius point
    for k in range(self.exploration_radius):
        position = position.directional_offset(self.direction_to_tuple('n'))
    exploration_radius_positions.append(position)

    edges = []

    # collect all positions on circle
    for k in range(np.floor(eploration_edge_len)):
        position = position.directional_offset(self.direction_to_tuple('e'))
        exploration_radius_positions.append(position)
        if k == np.floor(eploration_edge_len)-1:
            if get_edges:
                edges.append(position)
    for k in range(eploration_edge_len):
        position = position.directional_offset(self.direction_to_tuple('s'))
        exploration_radius_positions.append(position)
        if k == eploration_edge_len-1:
            if get_edges:
                edges.append(position)
    for k in range(eploration_edge_len):
        position = position.directional_offset(self.direction_to_tuple('w'))
        exploration_radius_positions.append(position)
        if k == eploration_edge_len-1:
            if get_edges:
                edges.append(position)
    for k in range(np.floor(eploration_edge_len)):
        position = position.directional_offset(self.direction_to_tuple('e'))
        exploration_radius_positions.append(position)
        if k == np.floor(eploration_edge_len)-1:
            if get_edges:
                edges.append(position)


    if get_edges:
        return exploration_radius_positions, edges
    else:
        return exploration_radius_positions


def update_exploration_radius(exploration_radius):
    # need here to check area arround next dropoff or shipyard and not just shipyard
    position = me.shipyard.position
    positions_min = get_exploration_radius_positions(position, exploration_radius)
    positions_middle = get_exploration_radius_positions(position, exploration_radius + 1)
    positions_max, exploration_area_edges = get_exploration_radius_positions(position, exploration_radius + 2, get_eges=True)
    if not check_halite_radius_coverage(positions_min): # is no more covered
        are_expandation = get_exploration_radius_positions(position, exploration_radius + 3)
        exploration_area = positions_middle + positions_max + are_expandation
        exploration_radius += 1
        logging.info("Exloration radius set to {}.".format(exploration_radius))
    else: # is still covered
        exploration_area = positions_min + positions_middle + positions_max

    return exploration_radius, exploration_area, exploration_area_edges


while True:

    game.update_frame()
    me = game.me
    game_map = game.game_map

    command_queue = []

    future_positions = []

    turn_number_up_to_create_ships = 300
    if game.turn_number == 1:
        exploration_radius,  = 1   # global variable, but should be variable for every dropoff!!!
        logging.info("Exloration radius set to {}.".format(exploration_radius))

    ship_constants = {'id': {'ship_status': 'explore'
                             }}

    # mark all actual ship positions as unsave
    for ship in me.get_ships():
        game_map[ship.position].mark_unsafe(ship)


    ### get ship commands
    for ship in me.get_ships():

        if ship.id not in ship_constants:
            ship_constants[ship.id] = {'ship_status': 'return_to_explore'}

        exploration_radius, exploration_area, exploration_area_edges = update_exploration_radius(exploration_radius)

        shipping = Shipping(ship, ship_constants[ship.id], me, exploration_radius, exploration_area, exploration_area_edges)
        cmd, next_position = shipping.next_cmd()
        future_positions.append(next_position)
        if cmd != None:  # just append when there is something to append
            command_queue.append(cmd)


    ### create ships
    shipyard_is_occupied = False
    for position in future_positions:
        if me.shipyard.position == position:
            shipyard_is_occupied = True

    if game.turn_number <= turn_number_up_to_create_ships and me.halite_amount >= constants.SHIP_COST and not shipyard_is_occupied:
        command_queue.append(game.me.shipyard.spawn())
        logging.info('##### Ship spawned #####')

    game.end_turn(command_queue)