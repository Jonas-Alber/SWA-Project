# removed unused enum import


from enum import Enum, auto
import threading


class StageConfigElement:
    def __init__(self, text, data_type=str, data=""):
        self.text = text
        self.data_type = data_type
        self.data = data
        
class StageState(Enum):
    UNIITIALIZED = auto()
    WAITING = auto()
    RUNNING = auto()
    FINISHED = auto()
    ERROR = auto()
class Stage:
    def __init__(self, name):
        self.name = name
        self.stagestate = StageState.UNIITIALIZED
        self._on_state_change = None  # Callback for state changes
        self._stage_visible = True  # Stage visibility in the pipeline

    def setStage(self, state: StageState):
        
        if not isinstance(state, StageState):
            raise TypeError("stage must be an instance of StageState")
        self.stagestate = state
        if hasattr(self, '_on_state_change') and self._on_state_change is not None:
            self._on_state_change(self.stagestate)
        
    def execute(self, data):
        try:
            self.setStage(StageState.RUNNING)
            result = self.process(data)
            self.setStage(StageState.FINISHED)
            return result
        except Exception as e:
            self.setStage(StageState.ERROR)
            print(f"Error in stage {self.name}: {e}")
            return None

    def process(self, data):
        raise NotImplementedError("Subclasses should implement this method")
    
    def getConfigElements(self)->list[StageConfigElement]:
        return [
            StageConfigElement(text="Visible", data_type=bool, data=self._stage_visible)
        ]
    
    def setConfigElements(self, config_elements:list[StageConfigElement]):
        for elem in config_elements:
            if elem.text == "Visible":
                if not isinstance(elem.data, bool):
                    raise TypeError("Visible must be a boolean")
                self._stage_visible = elem.data
        self.notify_change()

    def registerStateChangeCallback(self, callback:callable):
        self._on_state_change = callback
        
    # extend Stage to support change callbacks
    def register_on_change(self, callback):
        self._on_change = callback

    def notify_change(self):
        if hasattr(self, '_on_change'):
            self._on_change()
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
            if not isinstance(stage, Stage):
                raise TypeError("All stages must be instances of Stage")
            stage.setStage(StageState.WAITING)
        for stage in self.stages:
            data = stage.execute(data)
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
            if hasattr(stage, "register_on_change") and callable(stage.register_on_change):
                idx = len(self.stages) - 1
                stage.register_on_change(lambda idx=idx: self._mark_dirty(idx))

        def _mark_dirty(self, idx: int):
            # if no prior run, full run anyway
            if not self._step_data:
                return
            # rerun from the earliest changed stage
            self._dirty_index = idx if self._dirty_index == 0 else min(self._dirty_index, idx)
            print("New Start Index is: ",self._dirty_index)
            # rerun pipeline with the original input data
            #self.run(self._step_data[0])
            
        def runAsync(self, input_data):

            def _run():
                print("Running pipeline asynchronously with input data:", input_data)
                self.run(input_data)

                thread = threading.Thread(target=_run, daemon=True)
                thread.start()
                return thread
            
        def run(self, input_data):
            # clear any prior step data and force full rerun
            self._step_data = []
            self._dirty_index = 0
            return self.update(input_data)

        def update(self, input_data=None):
            # on first call or if caller passes new input_data, reset step_data
            if input_data is not None:
                self._step_data = [input_data]
                # mark entire pipeline dirty
                self._dirty_index = 0

            # if no stage is dirty, do nothing
            if self._dirty_index >= len(self.stages):
                return self._step_data[-1]

            start = self._dirty_index
            print("Start Index is: ",start)

            # reset dirty‐onwards stages back to WAITING
            for i in range(start, len(self.stages)):
                self.stages[i].setStage(StageState.WAITING)

            # execute only from the first dirty stage
            for i in range(start, len(self.stages)):
                out = self.stages[i].execute(self._step_data[i])
                if i + 1 < len(self._step_data):
                    self._step_data[i + 1] = out
                else:
                    self._step_data.append(out)

            # mark all clean
            self._dirty_index = len(self.stages)
            return self._step_data[-1]