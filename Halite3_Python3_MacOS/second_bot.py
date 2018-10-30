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

# This game object contains the initial game state.
game = hlt.Game()
# Respond with your name.
game.ready("Lahr_11111")


class Shipping():
    def __init__(self, ship, exploration_radius, ship_constants, me):
        self.ship=ship
        self.exploration_radius = exploration_radius
        self.ship_status = ship_constants['ship_status']
        self.me = me

        self.halite_threshold_to_move = 700
        self.halite_threshold_to_stay = 100
        self.halite_threshold_to_return = 900

    def next_move_cmd(self):
        if ship.position == self.me.shipyard.position and ship.halite_amount == 0: # move away from shipyard
            self.ship_status = 'return_to_explore'
            cmd, next_position = self.return_to_explore()
        elif self.ship_status == 'return_to_base' and self.ship.halite_amount > 0:
            cmd, next_position = self.return_to_base_or_drop()
        elif self.ship_status == 'dropped': # dropped last round so know return to exploration radius
            cmd, next_position = self.return_to_explore()
            self.ship_status = 'return_to_explore'
        elif self.ship_status == 'return_to_explore' and self.is_inside_exploration_radius():
            cmd, next_position = self.return_to_explore()
        elif self.ship_status == 'return_to_explore' and not self.is_inside_exploration_radius(): # start explore
            cmd, next_position = self.explore()
            self.ship_status = 'explore'
        elif self.ship.halite_amount > self.halite_threshold_to_return: # if full return to base
            cmd, next_position = self.return_to_base_or_drop()
            self.ship_status = 'return_to_base'
        elif self.is_inside_exploration_radius(): # moved into eploration radius by exploring so go out again
            cmd, next_position = self.return_to_explore()
            self.ship_status = 'return_to_explore'
        elif self.ship_status == 'explore':  # just exploring
            cmd, next_position = self.explore()
        else:
            print('warning: no valid ship status so explore')
            cmd, next_position = self.explore()


        return cmd, next_position


    def is_inside_exploration_radius(self):
        return game_map.calculate_distance(self.ship.position, self.get_next_dropoff_position()) < self.exploration_radius

    def return_to_base_or_drop(self):

        next_position = ship.position

        if ship.position == self.me.shipyard.position and ship.halite_amount > 0:   # do dropoff
            cmd = ship.make_dropoff()
            self.ship_status = 'dropped'
        else:   # move towards dropoff
            next_direction = game_map.naive_navigate(self.ship, self.get_next_dropoff_position())

            # if next position has to much halite go to random other direction with halite < halite_threshold_to_stay
            if game_map[self.ship.position.directional_offset(next_direction)].halite_amount > self.halite_threshold_to_stay:
                possible_next_positions_all = self.ship.position.get_surrounding_cardinals(self.ship.position)
                possible_next_directions_to_less_halite = [game_map.naive_navigate(self.ship, k) for k in possible_next_positions_all if game_map[k].halite_amount < self.halite_threshold_to_stay]
                next_direction = random.choice( possible_next_directions_to_less_halite )
                cmd = ship.move(next_direction)
                next_position = ship.position + next_direction
            else:
                cmd = ship.move(next_direction)
                next_position = ship.position + next_direction
        return cmd, next_position


    def return_to_explore(self):

        next_position = ship.position

        """
        # opposit direction of dropoff
        direction_of_dropoff = game_map.naive_navigate(self.ship, self.get_next_dropoff_position())
        print('#####', direction_of_dropoff)
        if direction_of_dropoff == (0, 0): # if ship is on dropoff is needs a direction
            print('##### position')
            direction_of_dropoff = game_map.naive_navigate(self.ship, self.ship.position.directional_offset((-1,0)))
            print('##### hier 1', direction_of_dropoff)
            print('##### hier 3', direction_of_dropoff.invert())
        next_direction = direction_of_dropoff.invert()
        print('##### hier 2', next_direction)
        cmd = ship.move(next_direction)
        """

        # random direction that is not the one to the next dropoff
        next_direction = random.choice( [k for k in ["n", "s", "e", "w"] if k not in [game_map.naive_navigate(self.ship, self.get_next_dropoff_position())] ] )
        cmd = ship.move(next_direction)
        next_position = self.ship.position.directional_offset(self.direction_to_tuple(next_direction))
        #print('actual position', self.ship.position)
        #print('next_position', next_position)
        return cmd, next_position


    def direction_to_tuple(self, direction_str):
        if direction_str =='n':
            return hlt.positionals.Direction.Noth
        elif direction_str == 'e':
            return hlt.positionals.Direction.East
        elif direction_str == 's':
            return hlt.positionals.Direction.South
        elif direction_str == 'w':
            return hlt.positionals.Direction.West
        else:
            print(direction_str)
            print('error in direction_to_tuple')
            return hlt.positionals.Direction.Noth


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

        next_position = ship.position

        # if actual pos hast much halit stay
        stay = game_map[self.ship.position].halite_amount >= self.halite_threshold_to_stay
        if stay:
            return self.ship.stay_still()
        else: # move to good position

            # could also decide to set status to 'go_far' if next_position_radius1_max_halite is less than another threshold like 250 such that the ship moves faster to rentable hilite positions

            # enough halite in radius 1 to move there
            next_position, n_halite = self.get_radius1_halite_max()
            cmd = self.ship.move(game_map.naive_navigate(self.ship, next_position))
            next_position
            return cmd, next_position


    def get_radius1_halite_max(self):

        possible_next_positions = self.ship.position.get_surrounding_cardinals(self.ship.position) # ist die aktuelle position auch schon dabei?
        n_halite_max = game_map[self.ship.position].halite_amount
        next_position_max_halite = self.ship.position
        for position in possible_next_positions:
            n_halite = game_map[position].halite_amount
            if n_halite > n_halite_max:
                n_halite_max = n_halite
                next_position_max_halite = position
        return next_position_max_halite, n_halite


    def get_next_ship_command(self):
        return self.next_move_cmd()


### move ship
#move = game_map.naive_navigate(ship, me.shipyard.position)
#command_queue.append(ship.move(move))

### logging
#logging.info("Ship {} has {} halite.".format(ship.id, ship.halite_amount))


### create dropoffs
#if dist_short > 100:   # if minimal distance to high make dropoff
#    command_queue.append(ship.make_dropoff())
#else:   # go to next dropoff


while True:

    game.update_frame()
    me = game.me
    game_map = game.game_map

    command_queue = []

    future_positions = []

    turn_number_up_to_create_ships = 3
    exploration_radius = 1   # global variable, but should be variable for every dropoff!!!

    ship_constants = {'id': {'ship_status': 'explore'
                             }}


    ### get ship commands
    for ship in me.get_ships():

        if ship.id not in ship_constants:
            ship_constants[ship.id] = {'ship_status': 'exploring'}

        shipping = Shipping(ship, exploration_radius, ship_constants[ship.id], me)
        cmd, next_position = shipping.get_next_ship_command()
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