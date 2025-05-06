---
config:
  layout: dagre
---
flowchart LR
 subgraph Datenquelle["Datenquelle"]
        direction TD
        F["Factory"]
        D("Datenerfassung")
  end
    F --> D
    Start["Start"] --> Datenquelle
    Datenquelle --> V("Vorverarbeitung")
    V --> A("Anreicherung")
    A --> N("Analyse")
    N --> S("Speicherung/Ausgabe")
    S --> Stop["Stop"]