
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

class StepPipeline(Pipeline):
        def __init__(self):
            super().__init__()
            self._step_data: list = []
            # index of the earliest stage that needs re-running
            self._dirty_index = 0

        def add_stage(self, stage: Stage):
            super().add_stage(stage)
            # when this stage’s config changes, mark it dirty
            stage.register_on_change(lambda idx=len(self.stages) - 1: self._mark_dirty(idx))

        def _mark_dirty(self, idx: int):
            # if no prior run, full run anyway
            if not self._step_data:
                return
            # rerun from the earliest changed stage
            self._dirty_index = idx if self._dirty_index == 0 else min(self._dirty_index, idx)

        def run(self, input_data):
            # if first run or first stage is dirty → full run
            if not self._step_data or self._dirty_index == 0:
                self._step_data = [input_data]
                start = 0
            else:
                start = self._dirty_index

            for i in range(start, len(self.stages)):
                out = self.stages[i].process(self._step_data[i])
                if i + 1 < len(self._step_data):
                    self._step_data[i + 1] = out
                else:
                    self._step_data.append(out)

            # all stages now clean
            self._dirty_index = len(self.stages)
            return self._step_data[-1]