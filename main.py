import os
from dotenv import load_dotenv

load_dotenv()

from prompt_improver import prompt_improver_agent
from google.adk import Event

def main():
    raw_prompt = "write me some code for a website"
    print(f"Original Prompt: '{raw_prompt}'\n")
    print("Running Prompt Improvement Agent...\n")
    
    # We pass the raw prompt as the initial event message
    result = prompt_improver_agent(Event(message=raw_prompt))
    
    print(result.message)

if __name__ == "__main__":
    main()
