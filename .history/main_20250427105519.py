def main():
    from src.pipeline import Pipeline
    from src.stages.stage_a import StageA

    # Initialize the pipeline
    pipeline = Pipeline()

    # Add stages to the pipeline
    pipeline.add_stage(StageA())

    # Execute the pipeline with some input data
    input_data = "Initial data"
    output_data = pipeline.run(input_data)

    print("Final output:", output_data)


if __name__ == "__main__":
    main()