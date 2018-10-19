#!/usr/bin/env python3

# Import the Halite SDK, which will let you interact with the game.

import hlt
from hlt import constants

import random
import logging


# This game object contains the initial game state.
game = hlt.Game()
# Respond with your name.
game.ready("Lahr_1")

while True:

    game.update_frame()
    me = game.me
    game_map = game.game_map

    command_queue = []
    ship_status = {}

    for ship in me.get_ships():

        if game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 or ship.is_full:
            command_queue.append(
                ship.move(random.choice(["n", "s", "e", "w"])))
        else:
            command_queue.append(ship.stay_still())

        logging.info("Ship {} has {} halite.".format(ship.id, ship.halite_amount))


        if ship.id not in ship_status:
            ship_status[ship.id] = "exploring"

        if ship_status[ship.id] == "returning":
            if ship.position == me.shipyard.position:  # if on shipyard start exploring
                ship_status[ship.id] = "exploring"
            else:   # return to dropoff

                dropoffs = me.get_dropoffs()
                dist_short = 10000
                dropoff_short = dropoffs[0]
                for dropoff in dropoffs:
                    dist = game_map.calculate_distance(ship.position, dropoff.position)
                    if dist < dist_short:
                        dist = dist_short
                        dropoff_short = dropoff
                logging.info("Ship {} has {} min dist.".format(ship.id, dist_short))

                if dist_short > 100:   # if minimal distance to high make dropoff
                    command_queue.append(ship.make_dropoff())
                    continue
                else:   # to to next dropoff
                    move = game_map.naive_navigate(ship, me.shipyard.position)
                    command_queue.append(ship.move(move))
                    continue
        elif ship.halite_amount >= constants.MAX_HALITE / 4:
            ship_status[ship.id] = "returning"


    if game.turn_number <= 1 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(game.me.shipyard.spawn())

    game.end_turn(command_queue)
