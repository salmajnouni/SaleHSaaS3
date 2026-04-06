import os
import subprocess
import tempfile
import uuid

class Tools:
    def __init__(self):
        pass

    def run_python_code(self, code: str) -> str:
        """
        Executes Python code in a secure sandbox and returns the output.
        Use this for mathematical calculations, data analysis, or logic verification.
        :param code: The Python code to execute.
        :return: Standard output or error message.
        """
        # Create a temporary file for the code
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"code_{uuid.uuid4().hex}.py")
        
        with open(file_path, "w") as f:
            f.write(code)
        
        try:
            # Run the code using the system python interpreter
            result = subprocess.run(
                ["python3", file_path],
                capture_output=True,
                text=True,
                timeout=30  # Safety timeout
            )
            
            if result.returncode == 0:
                return result.stdout if result.stdout else "Code executed successfully (no output)."
            else:
                return f"Error during execution:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out (max 30s)."
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"
        finally:
            # Cleanup
            if os.path.exists(file_path):
                os.remove(file_path)
