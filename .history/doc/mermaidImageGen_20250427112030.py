import subprocess
import os
import tempfile

def generate_mermaid_diagram(mermaid_code: str, output_file: str):
    """
    Generates a diagram from Mermaid code using the Mermaid CLI (mmdc).

    Args:
        mermaid_code: A string containing the Mermaid diagram definition.
        output_file: The path where the output image (e.g., 'diagram.png' or 'diagram.svg') should be saved.
                     The file extension determines the output format.
    """
    # Create temporary files for input
    # Using NamedTemporaryFile ensures the file is deleted automatically
    # We need delete=False on Windows, so handle deletion manually.
    try:
        with tempfile.NamedTemporaryFile(mode='w+', suffix=".mmd", delete=False) as temp_input_file:
            temp_input_path = temp_input_file.name
            temp_input_file.write(mermaid_code)
            temp_input_file.flush() # Ensure content is written

        print(f"Generating diagram to {output_file}...")
        # Construct the command for mmdc
        # Ensure output_file path is absolute or relative to the correct directory
        command = [
            "mmdc",
            "-i", temp_input_path,
            "-o", output_file,
            # Optional: Specify background color, e.g., transparent
            # "-b", "transparent" 
        ]

        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True, check=False) # Use check=False to handle errors manually

        # Check for errors
        if result.returncode != 0:
            print(f"Error generating diagram with mmdc:")
            print(f"Stderr: {result.stderr}")
            print(f"Stdout: {result.stdout}")
            return False
        else:
            print(f"Diagram successfully generated: {output_file}")
            if result.stdout: print(f"Stdout: {result.stdout}")
            if result.stderr: print(f"Stderr: {result.stderr}") # Sometimes mmdc outputs info to stderr
            return True

    except FileNotFoundError:
        print("Error: 'mmdc' command not found.")
        print("Please ensure Node.js and @mermaid-js/mermaid-cli are installed and in your system's PATH.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
    finally:
        # Clean up the temporary file if it exists
        if 'temp_input_path' in locals() and os.path.exists(temp_input_path):
            os.remove(temp_input_path)


# --- Beispielaufruf ---
if __name__ == "__main__":
    # Beispiel Mermaid Code (ersetzen Sie dies mit Ihrem Diagramm)
    pipeline_diagram = """
    graph TD
        A[CSV Input] --> B(Load Data);
        B --> C{Calculate Total Sale};
        C --> D{Filter Electronics};
        D --> E[Save Output];
    """

    # Definieren Sie den Ausgabepfad und Dateinamen
    output_png_file = "pipeline_diagram.png"
    output_svg_file = "pipeline_diagram.svg"

    # Generieren als PNG
    generate_mermaid_diagram(pipeline_diagram, output_png_file)

    # Generieren als SVG
    generate_mermaid_diagram(pipeline_diagram, output_svg_file)

    # Beispiel mit Fehler (Syntaxfehler im Mermaid Code)
    # faulty_diagram = "graph TD A -> B -> C ->" 
    # generate_mermaid_diagram(faulty_diagram, "error_diagram.png")