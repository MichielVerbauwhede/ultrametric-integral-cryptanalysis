from abc import ABC, abstractmethod

class Function(ABC):
    """
    Abstraction of a function.
    Can be called.
    """

    def __init__(self, input_size, output_size):
        self.input_size = input_size
        self.output_size = output_size

    @abstractmethod
    def __call__(self, v):
        return 0