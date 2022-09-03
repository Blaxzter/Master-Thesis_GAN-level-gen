

class MultiLayerStackDecoder:

    def __init__(self):
        pass

    def preprocess_layer(self, layer):
        pass

    def decode(self):
        # Move each possible blocks like a convolution over the block mush
        # for every position store the overlap 1 = full overlap 0 = no overlap
        # sort by overlap with mush
        # Select top element, filter elements that overlap, repeat
        # If no element are over the coverage is high enough return with selected
        # Otherwise go with next block
        pass
