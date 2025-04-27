class Pipeline:
    def __init__(self):
        self.stages = []

    def add_stage(self, stage):
        self.stages.append(stage)

    def run(self, input_data):
        data = input_data
        for stage in self.stages:
            data = stage.process(data)
        return data