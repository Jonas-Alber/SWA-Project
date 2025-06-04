
class Stage:
    def __init__(self, name):
        self.name = name

    def process(self, data):
        raise NotImplementedError("Subclasses should implement this method")
class Pipeline:
    def __init__(self):
        self.stages:list[Stage] = []

    def add_stage(self, stage:Stage):
        #if(not isinstance(stage, Stage)):‚
        #    raise TypeError("stage must be an instance of Stage")
        self.stages.append(stage)

    def run(self, input_data):
        data = input_data
        for stage in self.stages:
            data = stage.process(data)
        return data
    
