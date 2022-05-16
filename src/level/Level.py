
class Level:

    def __init__(self):
        self.blocks = []
        self.pigs = []
        self.platform = []
        self.birds = []

    def __getitem__(self, item):
        if item == "Block":
            return self.blocks
        elif item == "Pig":
            return self.pigs
        elif item == "Platform":
            return self.platform
        elif item == "Bird":
            return self.birds

    def __str__(self):
        return f"Blocks: {len(self.blocks)} Pigs: {len(self.pigs)} Platform: {len(self.platform)} Bird: {len(self.birds)}"

    def create_img(self):
        pass