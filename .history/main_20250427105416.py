def main():
    from pipeline.pipeline import Pipeline
    from pipeline.stages.stage_a import StageA
    from pipeline.stages.stage_b import StageB

    # Initialize the pipeline
    pipeline = Pipeline()

    # Add stages to the pipeline
    pipeline.add_stage(StageA())
    pipeline.add_stage(StageB())

    # Execute the pipeline with some input data
    input_data = "Initial data"
    output_data = pipeline.run(input_data)

    print("Final output:", output_data)


if __name__ == "__main__":
    main()