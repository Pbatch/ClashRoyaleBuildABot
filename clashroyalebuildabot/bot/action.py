class Action:
    def __init__(self, index, tile_x, tile_y, name, cost, type_, target, ready):
        self.index = index
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.name = name
        self.cost = cost
        self.type = type_
        self.target = target
        self.ready = ready

    def __repr__(self):
        return f'{self.name} at ({self.tile_x}, {self.tile_y})'
