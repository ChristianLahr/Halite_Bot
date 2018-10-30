#!/usr/bin/env python3


""" TO DO
- ship colisions   ship.position.directional_offset(test_direction) == occupied
- generate dropoffs
- shipyard == dropoff? getdropof includes shipyard?
- in return to exploration radius: move to next position in exloration radius
- map_cell.mark_unsafe(ship) after every time I know the next position

- geld sparen um dropoff zu bauen (variable auf true setzten und solange keine schigge bauen

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

    def __init__(self, THRESHOLDS_):

        self.ship_status = 'return_to_explore'

        #self.halite_threshold_to_move = 700
        self.halite_threshold_to_stay = THRESHOLDS_['halite_threshold_to_stay']
        self.halite_threshold_to_return = THRESHOLDS_['halite_threshold_to_return']
        self.create_dropoff_distance = THRESHOLDS_['create_dropoff_distance']


    def update_for_next_trun(self, ship_, me_, game_map_, ships_that_can_reach_shipyard_, exploration_radius_, exploration_area_, radiuses_):

        self.ship=ship_
        self.me = me_
        self.game_map = game_map_

        self.ships_that_can_reach_shipyard = ships_that_can_reach_shipyard_
        self.exploration_radius = exploration_radius_
        self.radiuses_hist = radiuses_
        self.exploration_area = exploration_area_

        self.is_inside_exploration_area = self.ship.position in self.exploration_area
        self.ship_full = self.ship.halite_amount > self.halite_threshold_to_return
        self.on_shipyard = self.ship.position == self.me.shipyard.position
        self.ship_empty = self.ship.halite_amount == 0
        self.ship_position_empty = self.game_map[self.ship.position].halite_amount == 0

        self.rte = self.ship_status == 'return_to_explore'
        self.rtb = self.ship_status == 'return_to_base_or_drop'
        self.e = self.ship_status == 'explore'


    def next_cmd(self):

        if self.ship_empty:
            if self.on_shipyard:# move away from shipyard
                cmd, next_position = self.return_to_explore()
                #print('state 1')
            elif not self.ship_position_empty: # return to explore when ship and position empty
                cmd = self.ship.stay_still()
                next_position = self.ship.position
                #print('state 2')
            elif self.ship_position_empty: # load halite if empty and position has halite
                if self.is_inside_exploration_area:
                    cmd, next_position = self.explore()
                    #print('state 3')
                else:
                    cmd, next_position = self.return_to_explore()
                    #print('state 3,5')

        elif self.rtb or self.ship_full: # if full return to base
            self.ship_status = 'return_to_base_or_drop'
            cmd, next_position = self.return_to_base_or_drop()
            #print('state 5')
        elif self.rte: # load halite if empty and position has halite
            cmd, next_position = self.return_to_explore()
            #print('state 4', self.ship.id, game.turn_number)
        elif self.e and not self.is_inside_exploration_area:
            cmd, next_position = self.return_to_explore()
            #print('state 8')
        elif self.e:  # just exploring
            cmd, next_position = self.explore()
            #print('state 9')
        else:
            print('Warning: no valid ship status so explore')
            print('status:', self.ship_status)
            print('halite:', self.ship.halite_amount)
            cmd, next_position = self.explore()


        return cmd, next_position


    def return_to_base_or_drop(self):

        next_position = self.ship.position

        if self.ship.position == self.me.shipyard.position and self.ship.halite_amount > 0:   # do dropoff
            cmd = self.ship.make_dropoff()
            logging.info("Ship {} dropping halite.".format(ship.id))

        else:   # move towards dropoff
            next_dropoff_position, all_dropoff_positions = self.get_next_dropoff_position(self.ship)
            min_dist_dropoff = all_dropoff_positions[np.array([game_map.calculate_distance(self.ship.position, pos) for pos in all_dropoff_positions]).argmin()]
            shipyard_available_for_next_move = min_dist_dropoff in [position for position in self.ship.position.get_surrounding_cardinals()]
            if False: #self.ship in self.ships_that_can_reach_shipyard: #shipyard_available_for_next_move: # avoid Torschusspanik
                next_direction = self.game_map.get_unsafe_moves(self.ship.position, self.me.shipyard.position)
                next_position = self.me.shipyard.position
                cmd = self.ship.move(self.direction_to_tuple(next_direction[0]))
            else:
                next_direction = self.game_map.naive_navigate(self.ship, min_dist_dropoff)
                cmd = self.ship.move(next_direction)
                next_position = self.ship.position.directional_offset(next_direction)
                logging.info("Ship {} moves toward dropoff.".format(ship.id))

        # go on returning
        self.ship_status = 'return_to_base_or_drop'
        return cmd, next_position



    def return_to_explore(self):

        if self.is_inside_exploration_area: # realy need to return?
            return self.explore()
        else: # go into direction of the position of exloration area that is nearest and not occupied
            next_positions_distances = {}
            for k, position in enumerate([pos for pos in self.exploration_area if not game_map[pos].is_occupied]):
                distance = self.game_map.calculate_distance(self.ship.position, position)
                #next_positions_distances['(' + position.x + ', ' + position.Y + ')'] = distance
                next_positions_distances[k] = {'pos': position, 'dist': distance}
            min_dist = np.array([next_positions_distances[k]['dist'] for k in next_positions_distances]).min()
            next_positions_minimal_distance = [next_positions_distances[k]['pos'] for k in next_positions_distances if next_positions_distances[k]['dist'] == min_dist]
            next_position = random.choice( next_positions_minimal_distance )
            cmd = self.ship.move(self.game_map.naive_navigate(self.ship, next_position))
            if next_position in self.exploration_area:
                self.ship_status = 'explore'
            else: self.ship_status = 'return_to_explore'
            logging.info("Ship {} returns to exploration area.".format(ship.id))
            return cmd, ship.position.directional_offset(self.game_map.naive_navigate(self.ship, next_position))


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
            print('[error]: opposit_direction')
            return 'n'

    def get_next_dropoff_position(self, ship_tmp):
        dropoffs = self.me.get_dropoffs()
        next_dropoff_positions = [dropoff.position for dropoff in dropoffs]
        next_dropoff_positions.append(self.me.shipyard.position)
        next_dropoff_position = next_dropoff_positions[ np.array([self.game_map.calculate_distance(ship_tmp.position, position) for position in next_dropoff_positions]).argmin() ]
        return next_dropoff_position, next_dropoff_positions


    def explore(self):

        if self.ship_full:
            self.ship_status = 'return_to_base_or_drop'
            return self.return_to_base_or_drop()
        if not self.is_inside_exploration_area: # realy need to return?
            self.ship_status = 'return_to_explore'
            return self.return_to_explore()
        else:
            self.ship_status = 'explore'
            # if actual pos hast much halit stay
            halite_amount_posi_enough_to_stay = self.game_map[self.ship.position].halite_amount >= self.halite_threshold_to_stay
            halite_amount_ship_enough_to_return = self.game_map[self.ship.position].halite_amount >= self.halite_threshold_to_return
            stay = halite_amount_posi_enough_to_stay and not halite_amount_ship_enough_to_return

            # dropoff with lowest distance for this ship
            next_dropoff_position, all_dropoff_positions = self.get_next_dropoff_position(self.ship)
            min_dist_dropoff = np.array([game_map.calculate_distance(self.ship.position, pos) for pos in all_dropoff_positions]).min()

            if stay:
                return self.ship.stay_still(), self.ship.position

            else:

                ### create dropoff
                # find ship the farthest away
                condition_A = self.exploration_radius > self.create_dropoff_distance and min_dist_dropoff > self.create_dropoff_distance and me.halite_amount >= constants.DROPOFF_COST
                if condition_A: # check cond_B that need computational effort just when cond_A is fulfilled
                    distances_to_next_dropoff = {}
                    for ship_tmp in [s for s in me.get_ships() if s.halite_amount < 300]:
                        next_dropoff_position_tmp, _ = self.get_next_dropoff_position(ship_tmp)
                        distances_to_next_dropoff[ship_tmp.id] = {'dist': self.game_map.calculate_distance(ship, next_dropoff_position_tmp),
                                                                  'amount': ship_tmp.halite_amount}
                    max_distances = np.array([distances_to_next_dropoff[id]['dist'] for id in distances_to_next_dropoff]).max()
                    ships_max_distances = [(id, distances_to_next_dropoff[id]) for id in distances_to_next_dropoff if distances_to_next_dropoff[id]['dist'] == max_distances]
                    min_amount = np.array([data[1]['amount'] for data in ships_max_distances]).min()
                    ships_max_distances_min_halite_id = [data[0] for data in ships_max_distances if data[1]['amount'] == min_amount][-1]
                    condition_B =  self.ship.id == ships_max_distances_min_halite_id

                if condition_A and condition_B:

                    # schiff mit letzter ID
                    #elif self.exploration_radius > self.create_dropoff_distance and min_dist_dropoff > self.create_dropoff_distance and me.halite_amount >= constants.DROPOFF_COST and self.ship.id == [ship.id for ship in self.me.get_ships()][-1]:
                    ### create dropoffs
                    cmd = self.ship.make_dropoff()
                    next_position = self.ship.position
                    return cmd, next_position

                else: # move to good position
                    # could also decide to set status to 'go_far' if next_position_radius1_max_halite is less than another threshold like 250 such that the ship moves faster to rentable hilite positions

                    ### mode: min max coverage radius
                    if self.is_inside_exploration_area:  # inside exploration_area?

                        # enough halite in radius 1 of ship to move there
                        next_position, n_halite = self.get_radius1_halite_max()
                        if next_position in self.exploration_area:
                            cmd = self.ship.move(self.game_map.naive_navigate(self.ship, next_position))
                            next_position
                        else: # search for next covered area in exploration area

                            try:
                                exploration_area_covered = [pos for pos in exploration_area if self.game_map[pos].halite_amount > self.halite_threshold_to_stay]
                                exploration_area_covered_dist = [self.game_map.calculate_distance(ship.position, pos) for pos in exploration_area_covered]
                                exploration_area_covered_dist_min = np.array(exploration_area_covered_dist).min()
                                possible_next_positions = [pos for pos in exploration_area_covered if self.game_map.calculate_distance(ship.position, pos) == exploration_area_covered_dist_min]
                                next_position = random.choice( possible_next_positions )
                                cmd = self.ship.move(self.game_map.naive_navigate(self.ship, next_position))
                                # be careful: next position needs to be next position that can be reached and not the next position that wants to be reched and has distance > 1
                                next_position = ship.position.directional_offset(self.game_map.naive_navigate(self.ship, next_position))
                            except:
                                print('radiuses_hist', self.radiuses_hist)

                    else:   # retrun to exploration area
                        cmd, next_position = self.return_to_explore()

                return cmd, next_position


    def get_radius1_halite_max(self):

        possible_next_positions = self.ship.position.get_surrounding_cardinals() # ist die aktuelle position auch schon dabei?
        n_halite_max = self.game_map[self.ship.position].halite_amount
        next_position_max_halite = self.ship.position
        for position in possible_next_positions:
            n_halite = game_map[position].halite_amount
            if n_halite > n_halite_max:
                n_halite_max = n_halite
                next_position_max_halite = position
        return next_position_max_halite, n_halite_max






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


def direction_to_tuple(direction_str):
    if direction_str =='n' or direction_str == (1, 0):
        return hlt.positionals.Direction.North
    elif direction_str == 'e' or direction_str == (0, 1):
        return hlt.positionals.Direction.East
    elif direction_str == 's' or direction_str == (-1, 0):
        return hlt.positionals.Direction.South
    elif direction_str == 'w' or direction_str == (0, -1):
        return hlt.positionals.Direction.West
    else:
        #print('error in direction_to_tuple')
        return hlt.positionals.Direction.North


def check_halite_radius_coverage(exploration_radius_positions, halite_threshold_to_stay):
    positions = exploration_radius_positions
    coverage = np.array([game_map[position].halite_amount for position in positions])
    max_coverage = coverage.max()
    n_covered = len([cov > halite_threshold_to_stay for cov in coverage])
    if max_coverage < halite_threshold_to_stay:
        return False, n_covered
    else:
        return True, n_covered


def get_exploration_radius_positions(position, radius):
    eploration_edge_len = 1 + radius * 2
    exploration_radius_positions = []
    # go to first radius point
    for k in range(radius):
        position = position.directional_offset(direction_to_tuple('n'))
    exploration_radius_positions.append(position)

    # collect all positions on circle
    for k in range(int(np.floor(eploration_edge_len/2))):
        position = position.directional_offset(direction_to_tuple('e'))
        exploration_radius_positions.append(position)
    for k in range(eploration_edge_len-1):
        position = position.directional_offset(direction_to_tuple('s'))
        exploration_radius_positions.append(position)
    for k in range(eploration_edge_len-1):
        position = position.directional_offset(direction_to_tuple('w'))
        exploration_radius_positions.append(position)
    for k in range(eploration_edge_len-1):
        position = position.directional_offset(direction_to_tuple('n'))
        exploration_radius_positions.append(position)
    for k in range(int(np.floor(eploration_edge_len/2)-1)):
        position = position.directional_offset(direction_to_tuple('e'))
        exploration_radius_positions.append(position)

    duplicates_check = len(exploration_radius_positions) != len(set([(pos.x, pos.y) for pos in exploration_radius_positions]))
    n_area_check = len(exploration_radius_positions) != (2*eploration_edge_len+2*(eploration_edge_len-2))
    if duplicates_check or n_area_check: # check area positions
        print('warning: area check failes!!!')
        print('duplicates_check', duplicates_check)
        print('n_area_check', n_area_check, len(exploration_radius_positions), (2*eploration_edge_len+2*(eploration_edge_len-2)))
        print('radius', radius)

    #print('area:', radius, eploration_edge_len, len(exploration_radius_positions), (2*eploration_edge_len+2*(eploration_edge_len-2)))

    return exploration_radius_positions


def update_exploration_radius(exploration_radius, halite_threshold_to_stay):
    # need here to check area arround next dropoff or shipyard and not just shipyard
    position = me.shipyard.position


    positions_min = get_exploration_radius_positions(position, exploration_radius)
    if game.turn_number==1:
        positions_middle = get_exploration_radius_positions(position, exploration_radius + 1)
        positions_max = get_exploration_radius_positions(position, exploration_radius + 2)
    else:
        radius_covered, n_covered = check_halite_radius_coverage(positions_min, halite_threshold_to_stay): # is no more covered
        if not radius_covered
            if len(me.get_ships())<16:
                are_expandation = get_exploration_radius_positions(position, exploration_radius + 3)
                exploration_radius += 1
                logging.info("Exloration radius set to {}.".format(exploration_radius))
            else: # too any ships so more radius!!
                are_expandation = get_exploration_radius_positions(position, exploration_radius + 3)
                are_expandation_2 = get_exploration_radius_positions(position, exploration_radius + 4)
                exploration_radius += 2
                logging.info("Exloration radius set to {}.".format(exploration_radius))
        else: # is still covered
            None

    return exploration_radius


def get_exploration_area(halite_threshold_to_stay, me):

    """
    Area independent form exploration_radius. Just first 3 rings where halite is found for every dropoff.
    """

    exploration_area_positions = []
    dropoffs = [dropoff.position for dropoff in me.get_dropoffs()] + [me.shipyard.position]
    for drop in dropoffs:
        r =  1
        found = 0
        while found < 4 and len(exploration_area_positions) < len(me.get_ships())*2: # radius 3 and more than duble as much positions than sips
            positions = get_exploration_radius_positions(drop, r)
            l_start = len(exploration_area_positions)
            for pos in positions:
                if game_map[pos].halite_amount > halite_threshold_to_stay:
                    exploration_area_positions.append(pos)
            l_end = len(exploration_area_positions)
            if l_start < l_end:
                found += 1
            r += 1

    return exploration_area_positions, r-1


def get_ships_torschusspanik(me, listed_ships):
    """
    :return: Positions of ships that are on sourounding cardinals of shipyard and want to dropoff
    """

    positions = [ships[id]['shipping'].ship for id in ships]
    ship_tmp = [listed_ships[id]['shipping'].ship for id in listed_ships if listed_ships[id]['shipping'].ship_status == 'return_to_base_or_drop']
    ship_tmp = [ship for ship in ship_tmp if ship.position in me.shipyard.position.get_surrounding_cardinals()]

    return ship_tmp


### constants ###
THRESHOLDS = {}
THRESHOLDS['turn_number_up_to_create_ships'] = 300
THRESHOLDS['halite_threshold_to_stay'] = 20
THRESHOLDS['halite_threshold_to_return'] = 990
THRESHOLDS['create_dropoff_distance'] = 3

### player and map ###
me = game.me
game_map = game.game_map

### variables ###
ships = {}
exploration_radius  = 1   # global variable, but should be variable for every dropoff!!!
radiuses = [1]
exploration_area = get_exploration_area(THRESHOLDS['halite_threshold_to_stay'], me)


while True:

    #if game.turn_number == 61:
    #    print('#######', game_map[me.shipyard.position].is_occupied)
    #    for ship in me.get_ships():
    #        print('#####', ship.id, ships[ship.id]['shipping'].ship_status)
    #        if ships[ship.id]['shipping'].ship_status == 'return_to_base_or_drop':
    #            print(game_map.get_unsafe_moves(ship.position, me.shipyard.position))


    game.update_frame()
    me = game.me
    game_map = game.game_map

    command_queue = []
    future_positions = []


    # mark all actual ship positions as mark_unsafe
    #for ship in me.get_ships():
    #    game_map[ship.position].mark_unsafe(ship)

    ships_that_can_reach_shipyard = get_ships_torschusspanik(me, ships)

    if len(me.get_ships()) != 0:

        ### get ship commands
        for ship in me.get_ships():
            # whitin this loop nothing on game_map is changed, but just the moves/cmds are queued

            exploration_area, exploration_radius_new = get_exploration_area(THRESHOLDS['halite_threshold_to_stay'], me)
            if exploration_radius == exploration_radius_new -1:
                exploration_radius = exploration_radius_new
                radiuses.append((game.turn_number, exploration_radius_new))


            #print('######## eploration area ########')
            #print(exploration_radius, len(exploration_area))
            #print('shipyard:', me.shipyard.position)
            #for k in exploration_area:
            #    print(exploration_radius, k)
            #print('######## eploration area ########')

            if ship.id not in ships:
                ships[ship.id] = {'shipping': Shipping(THRESHOLDS)}


            #if game.turn_number == 75:
            #    if ship.id == 1:
            #        print('ship pos', ship.position)
            #        print('shipyard pos', me.shipyard.position)
            #        print(game_map.naive_navigate(ship, me.shipyard.position))
            #        print(game_map.get_unsafe_moves(ship.position, me.shipyard.position))
            #print('#######', game_map[me.shipyard.position].is_occupied)

            ships[ship.id]['shipping'].update_for_next_trun(ship,
                                                            me,
                                                            game_map,
                                                            ships_that_can_reach_shipyard,
                                                            exploration_radius,
                                                            exploration_area,
                                                            radiuses)

            cmd, next_position = ships[ship.id]['shipping'].next_cmd()

            if cmd != None:  # just append when there is something to append
                command_queue.append(cmd)

            future_positions.append(next_position)
            game_map[next_position].mark_unsafe(ship)

            if game_map.calculate_distance(ship.position, next_position) > 1:
                print('[error]: position unreachable')
                print('+++++++++++++ dist', game_map.calculate_distance(ship.position, next_position))
                print('+++++++++++++', ships[ship.id]['shipping'].ship_status)
                print('+++++++++++++', next_position)
                print('+++++++++++++', ship.position)

    #else:
    #    print('Warning: no ship available')


    ### create ships
    shipyard_is_occupied = game_map[me.shipyard].is_occupied or me.shipyard.position in future_positions
    #if game.turn_number == 1:
    #    print('future', future_positions)
    #    print('shipyard', me.shipyard.position)
    #    print(shipyard_is_occupied)
    #    print(game.turn_number <= THRESHOLDS['turn_number_up_to_create_ships'] and me.halite_amount >= constants.SHIP_COST and not shipyard_is_occupied)

    # create ships
    if game.turn_number <= 100:
        if game.turn_number <= THRESHOLDS['turn_number_up_to_create_ships'] and me.halite_amount >= constants.SHIP_COST and not shipyard_is_occupied:
            command_queue.append(game.me.shipyard.spawn())
            logging.info('##### Ship spawned #####')

    # create dropoffs and ships
    else:
        if game.turn_number <= THRESHOLDS['turn_number_up_to_create_ships'] and me.halite_amount >= constants.SHIP_COST + 4000 and not shipyard_is_occupied:
            command_queue.append(game.me.shipyard.spawn())
            logging.info('##### Ship spawned #####')


    game.end_turn(command_queue)