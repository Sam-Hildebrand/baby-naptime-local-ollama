# run.py
import os
import argparse
from scripter import ScriptRunner
from code_browser import CodeBrowser
from debugger import Debugger
from agent import Agent
from queue import Queue
from logger import logger
from colorama import Fore, Style

def print_banner():
    banner = """
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║             Baby Naptime - LLMs for Native Vulnerabilities           ║
    ║                                                                      ║
    ║        An open source implementation of Google's Project Naptime     ║
    ║                                                                      ║
    ║     [+] Intelligent vulnerability analysis                           ║
    ║     [+] Automated exploit generation                                 ║
    ║     [+] Memory corruption detection                                  ║
    ║     [+] Advanced debugging capabilities                              ║
    ║                                                                      ║
    ║               -- Find bugs while the baby's sleeping! --             ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

class BabyNaptime:
    def __init__(self, code_file: str, max_iterations: int = 100, 
                 llm_model: str = "gpt-oss:120b", main_function: str = "main",
                 keep_history: int = 10, ollama_url: str = None, gemini: bool = False, api_key: str = None):
        """
        Initialize the BabyNaptime vulnerability analyzer.
        
        Args:
            code_file: Path to the source code file to analyze
            max_iterations: Maximum number of analysis iterations (default: 100)
            llm_model: LLM model to use for analysis (default: gpt-oss:120b)
            main_function: Entry function to begin analysis (default: main)
            keep_history: Number of conversation history items to keep
            ollama_url: Optional Ollama server URL
            gemini: Whether to use the Gemini API
            api_key: The Gemini API key
        """
        self.code_file = code_file
        self.is_binary = False
        self.max_iterations = max_iterations
        self.llm_model = llm_model
        self.keep_history = keep_history
        self.main_function = main_function
        self.ollama_url = ollama_url
        self.gemini = gemini
        self.api_key = api_key
        self.code_browser = CodeBrowser(ollama_url=ollama_url, gemini=gemini, api_key=api_key)
        
        if not os.path.exists(code_file):
            raise FileNotFoundError(f"Source file not found: {code_file}")
            
        if not self.is_binary_file(code_file):
            logger.info(f"Reading source file: {code_file}")
            self.file_contents = open(self.code_file, 'r').read()
            self.is_binary = False
        else:
            logger.warning(f"Skipping text read for binary file: {code_file}")
            self.file_contents = "the path of binary file is" + self.code_file
            self.is_binary = True
            
    def is_binary_file(self, file_path):
        """Check if the given file is a binary file by checking for null bytes."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read(1024)
                return b'\x00' in data
        except Exception as e:
            logger.error(f"Error checking file type: {e}")
            return False
        
    def run(self):
        """Run the vulnerability analysis on the target code."""
        # Get entry function
        if not self.is_binary:
            function_body = self.code_browser.get_function_body(
                self.code_file, 
                self.main_function
            )['source']
        else:
            function_body = "the path of binary file is" + self.code_file
        
        self.agent = Agent(
            self.code_file, 
            function_body, 
            self.is_binary,
            llm_model=self.llm_model, 
            keep_history=self.keep_history,
            ollama_url=self.ollama_url,
            gemini=self.gemini,
            api_key=self.api_key
        )
        logger.info(f"{Fore.WHITE}Starting code analysis...{Style.RESET_ALL}")
        self.agent.run()
        
def main():
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="BabyNaptime - Automated vulnerability analysis tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--code_file", "-c",
        help="Path to the source code file to start the analysis",
        required=True
    )
    
    parser.add_argument(
        "--code-directory", "-d",
        help="Directory containing additional source files",
        default="."
    )
    
    parser.add_argument(
        "--max-iterations", "-m",
        type=int,
        help="Maximum number of analysis iterations",
        default=100
    )
    
    parser.add_argument(
        "--llm-model", "-l",
        help="LLM model to use for analysis",
        default="gpt-oss:120b",
        choices=["gpt-oss:20b", "gpt-oss:120b"]
    )
    
    parser.add_argument(
        "--main-function", "-f",
        help="Entry function to begin analysis",
        default="main"
    )
    
    parser.add_argument(
        "--keep-history", "-k", 
        type=int,
        help="Number of conversation history items to keep in context",
        default=14
    )
    
    parser.add_argument(
        "--ollama-url", "-u",
        help="Ollama server URL (e.g., https://ollama:11434)",
        default=None
    )
    
    parser.add_argument(
        "--gemini",
        help="Use Gemini API instead of Ollama",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Validate keep_history is > 10
    if args.keep_history <= 10:
        logger.error("Keep history must be greater than 10")
        return 1
        
    # Check if code file exists
    if not os.path.exists(args.code_file):
        logger.error(f"File not found: {args.code_file}")
        return 1
        
    # Check if code directory exists
    if not os.path.exists(args.code_directory):
        logger.error(f"Code directory not found: {args.code_directory}")
        return 1
        
    # Check if code directory is actually a directory
    if not os.path.isdir(args.code_directory):
        logger.error(f"Specified path is not a directory: {args.code_directory}")
        return 1
    
    # Log Ollama URL if provided
    if args.ollama_url:
        logger.info(f"{Fore.CYAN}Using Ollama server at: {args.ollama_url}")

    api_key = None
    if args.gemini:
        api_key_file = ".gemini_api_key"
        if os.path.exists(api_key_file):
            with open(api_key_file, "r") as f:
                api_key = f.read().strip()
        
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            print("GEMINI_API_KEY environment variable not found.")
            print("You can get an API key from Google AI Studio: https://aistudio.google.com/app/apikey")
            try:
                import getpass
                api_key = getpass.getpass("Please enter your Gemini API key: ")
            except ImportError:
                print("Warning: getpass module not available for secure input.")
                api_key = input("Please enter your Gemini API key: ")
            
            with open(api_key_file, "w") as f:
                f.write(api_key)
            print(f"API key saved to {api_key_file} for future use.")

    analyzer = BabyNaptime(
        code_file=args.code_file,
        max_iterations=args.max_iterations,
        llm_model=args.llm_model,
        main_function=args.main_function,
        keep_history=args.keep_history,
        ollama_url=args.ollama_url,
        gemini=args.gemini,
        api_key=api_key
    )
    analyzer.run()

if __name__ == "__main__":
    main()