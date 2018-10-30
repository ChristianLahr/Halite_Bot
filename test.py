def return_to_base_or_drop(self):

    next_position = self.ship.position

    if self.ship.position == self.me.shipyard.position and self.ship.halite_amount > 0:   # do dropoff
        cmd = self.ship.make_dropoff()
        self.ship_status = 'dropped'

    else:   # move towards dropoff
        next_dropoff_position = self.me.shipyard.position
        next_direction = game_map.naive_navigate(self.ship, next_dropoff_position)
        cmd = self.ship.move(next_direction)
        next_position = self.ship.position.directional_offset(self.direction_to_tuple(next_direction))
    return cmd, next_position
