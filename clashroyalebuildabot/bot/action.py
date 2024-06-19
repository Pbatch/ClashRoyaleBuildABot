class Action:
    def __init__(self, index, tile_x, tile_y, card):
        self.index = index
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.card = card

    def __repr__(self):
        return f"{self.card.name} at ({self.tile_x}, {self.tile_y})"
