import os
import json
from llm import LLM
from pathlib import Path

class Reporter:
    """
    Security vulnerability reporter that analyzes findings and generates reports.
    
    Analyzes conversation history between security testing agent and target system
    to validate discovered vulnerabilities and generate detailed reports.
    """
    
    def __init__(self, filename, llm_model: str = "o3-mini", ollama_url: str = None, gemini: bool = False, api_key: str = None):
        """
        Initialize the reporter.
        
        Args:
            filename: Filename of the file that was tested
            llm_model (str): LLM model to use
            ollama_url (str, optional): Ollama server URL
            gemini (bool, optional): Whether to use Gemini API. Defaults to False.
            api_key (str, optional): Gemini API key. Defaults to None.
        """
        self.llm = LLM(llm_model, ollama_url=ollama_url, gemini=gemini, api_key=api_key)
        self.reports = []
        self.filename = filename
        self.ollama_url = ollama_url
        
    def generate_summary_report(self, history):
        """
        Generate a comprehensive markdown summary of the native vulnerability exploitation.
        
        Analyzes the conversation history to document how the native vulnerability
        was discovered and exploited, including technical details and final payload.
        """
        from logger import logger
        from colorama import Fore
        
        logger.info(f"{Fore.CYAN}Generating vulnerability report...")
        
        system_prompt = f"""
You are a binary exploitation report writer. Your task is to analyze the conversation history and create a detailed technical report about how a native vulnerability was exploited.

The report should include:
1. A technical description of the vulnerability (buffer overflow, format string, etc)
2. Analysis of the vulnerable code and why it was exploitable
3. Step-by-step walkthrough of how the vulnerability was discovered and analyzed
4. Details of the exploitation process including:
   - Memory layout analysis
   - Any protections that needed to be bypassed
   - Development of the exploit
5. The final working payload and proof of successful exploitation

Format the output as a proper markdown document with:
- Executive summary explaining the vulnerability
- Technical deep-dive into the vulnerable code
- Detailed exploitation methodology
- Code blocks showing key commands and payloads
- Screenshots or output demonstrating the successful exploit

Focus on the technical details that show how the native vulnerability was discovered and exploited. Include specific memory addresses, payloads, and commands used.

Report should be 1 page only. We don't want extra pages. Short, to the point.
"""
        
        system_prompt = [{"role": "system", "content": system_prompt}]
        messages = []
        for item in history:
            messages.append({"role": item["role"], "content": item["content"]})
        
        logger.info(f"{Fore.CYAN}Sending {len(messages)} messages to LLM for report generation...")
        
        try:
            summary = self.llm.action(system_prompt + messages)
            
            if not summary or len(summary.strip()) == 0:
                logger.warning(f"{Fore.YELLOW}LLM returned empty response, generating fallback report...")
                summary = self._generate_fallback_report(history)
            else:
                logger.info(f"{Fore.GREEN}Report generated successfully ({len(summary)} characters)")
                
        except Exception as e:
            logger.error(f"{Fore.RED}Error generating report with LLM: {e}")
            logger.info(f"{Fore.YELLOW}Generating fallback report...")
            summary = self._generate_fallback_report(history)
        
        base = os.path.splitext(os.path.basename(self.filename))[0]
        os.makedirs("results", exist_ok=True)
        
        report_path = f"results/{base}_summary.md"
        with open(report_path, "w") as f:
            f.write(summary)
        
        logger.info(f"{Fore.GREEN}Report saved to: {report_path}")
    
    def _generate_fallback_report(self, history):
        """Generate a simple fallback report from conversation history."""
        report = f"# Vulnerability Report: {self.filename}\n\n"
        report += "## Conversation History\n\n"
        
        for i, item in enumerate(history):
            role = item['role'].capitalize()
            content = item['content']
            report += f"### {i+1}. {role}\n\n"
            report += f"```\n{content}\n```\n\n"
        
        report += "## Summary\n\n"
        report += "The exploit was successful as indicated by the conversation history above.\n"
        
        return report