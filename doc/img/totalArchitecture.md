%% filepath: doc/project_overview.mmd
graph TD
    subgraph Project Execution
        direction LR
        A["main.py (Entry Point)"] --> B(src.pipeline.pipeline.Pipeline);
        B -- runs --> C(src.stages.load_csv_stage.LoadCsvStage);
        C -- reads --> D["src/data/srcData.csv"];
        C --> E(src.stages.calculate_total_sale_stage.CalculateTotalSaleStage);
        E --> F(src.stages.filter_electronics_stage.FilterElectronicsStage);
        F --> G(src.stages.save_output_stage.SaveOutputStage);
        G --> H[Output (Console/File)];
    end

    subgraph Documentation
        direction LR
        J["doc/docu.tex (LaTeX)"]
        K["doc/mermaidImageGen.py (Diagram Generator)"]
        L["doc/img/ (Output Images)"]
        K -- generates --> L;
    end

    A -- uses --> J; %% Optional: main.py might relate to documentation conceptually