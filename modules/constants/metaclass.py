class ConstantMeta(type):
    """
    meta class for class that manages constants.
    prohibit overwriting class variables and adding new class variables.
    """

    # prohibit overwriting class variables
    _initialized = False

    def __setattr__(cls, name, value):
        if cls._initialized:
            if name in cls.__dict__:
                raise ValueError(f"{name} is a read-only property")
            else:
                raise AttributeError("Cannot add new attribute to Constants class")
        super().__setattr__(name, value)

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls._initialized = True
