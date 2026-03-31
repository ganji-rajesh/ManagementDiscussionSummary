"""
prompts.py

Centralizes prompt engineering templates for the application.
Separating prompts from application logic ensures cleaner code and easier iteration.
"""

# The core identity and instruction set loaded when activating a Chat session.
SYSTEM_ANALYST_INSTRUCTION = """
You are an expert financial analyst and assistant. You have been provided with excerpts 
from a company's Annual Report. 

Your objectives:
1. Answer the user's queries clearly and concisely, relying ONLY on the provided Context.
2. If the Context does not contain the answer, explicitly state: "Based on the provided excerpts, I cannot answer this."
3. ALWAYS cite the provided sources when stating facts, summarizing, or pulling numbers.
   Format your citations like: [Source Name].

Focus on accuracy over verbosity.
"""

# Used when the user clicks the "Generate Overview" button
OVERVIEW_PROMPT = """
Please provide a comprehensive summary and overview of the currently active financial documents.
Highlight the primary themes, key numerical figures (e.g., revenue, net income), and major risks discussed.

Ensure that your summary structurally incorporates citations from the provided active sources.
"""

def build_contextual_prompt(user_query: str, active_context: str) -> str:
    """
    Assembles the final string that will be sent to the LLM, framing the user's query 
    with the actively selected document sources.
    
    Args:
        user_query (str): The question asked by the user in the UI.
        active_context (str): The concatenated text representations of selected sources.
        
    Returns:
        str: The fully assembled prompt.
    """
    if not active_context.strip():
        # Edge case: No sources are active
        return f"User query: {user_query}\n\n[Warning: No document context is currently active. Please remind the user to select sources.]"
        
    template = f"""
Here is the active document context:
<Context>
{active_context}
</Context>

Based ONLY on the <Context> above, please respond to the following query:
<UserQuery>
{user_query}
</UserQuery>
"""
    return template.strip()
