"""
Smart Life Concierge Agent - Main Orchestrator
A multi-agent system for meal planning, shopping, and travel assistance.
Refactored to use standard Google GenAI SDK (v1.52.0) with Tool Calling.
"""

from google import genai
from google.genai import types
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Callable

# Initialize the Gemini Client globally
# The client object is required for all model interactions.
# It uses the GOOGLE_API_KEY environment variable automatically.
try:
    CLIENT = genai.Client()
except Exception as e:
    print(f"Error initializing Gemini Client: {e}")
    # CLIENT will be None if the key is missing or invalid.

# ============================================================================
# CUSTOM TOOLS (Functions for the model to call)
# ============================================================================

def save_plan_to_file(filename: str, content: str) -> str:
    """
    Saves the generated plan to a file.

    Args:
        filename: Name of the file to save
        content: Content to write to file

    Returns:
        Success message with file path
    """
    try:
        os.makedirs("output", exist_ok=True)
        filepath = os.path.join("output", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"status": "Success", "message": f"Successfully saved to {filepath}"})
    except Exception as e:
        return json.dumps({"status": "Error", "message": f"Error saving file: {str(e)}"})


def get_user_preferences(preference_type: str) -> Dict[str, Any]:
    """
    Retrieves stored user preferences from memory.

    Args:
        preference_type: Type of preferences (dietary, travel, budget)

    Returns:
        Dictionary of user preferences
    """
    # For demo purposes, returning sample preferences
    preferences = {
        "dietary": {
            "restrictions": ["vegetarian"],
            "favorite_cuisines": ["Italian", "Indian", "Mexican"],
            "disliked_foods": ["mushrooms", "olives"],
            "calorie_target": 2000,
            "meal_frequency": 3
        },
        "travel": {
            "budget_level": "moderate",
            "preferred_activities": ["museums", "hiking", "local food"],
            "accommodation_preference": "boutique hotels",
            "travel_pace": "relaxed"
        },
        "budget": {
            "weekly_grocery_budget": 150,
            "dining_out_budget": 100,
            "travel_daily_budget": 200
        }
    }
    return preferences.get(preference_type, {})


def web_search_tool(query: str) -> str:
    """
    Simulates web search for recipes, travel info, and deals.

    Args:
        query: Search query string

    Returns:
        Search results as formatted string
    """
    # For demo, returning structured sample data
    if "recipe" in query.lower():
        result = """
        Found 5 recipes:
        1. Easy Vegetarian Pasta Primavera (30 min, $12 for 4 servings)
        2. Quick Indian Dal Tadka (25 min, $8 for 4 servings)
        3. Mexican Black Bean Tacos (20 min, $10 for 4 servings)
        4. Mediterranean Chickpea Salad (15 min, $9 for 4 servings)
        5. Thai Vegetable Stir-fry (25 min, $11 for 4 servings)
        """
    elif "travel" in query.lower():
        result = """
        Travel recommendations:
        - Kyoto, Japan: Rich culture, temples, excellent food scene
        - Barcelona, Spain: Architecture, beaches, vibrant nightlife
        - Portland, Oregon: Nature, breweries, food trucks
        - Edinburgh, Scotland: History, hiking, festivals
        """
    elif "grocery" in query.lower() or "price" in query.lower():
        result = """
        Current grocery prices:
        - Fresh vegetables: $3-5/lb
        - Pasta: $2-3/box
        - Beans (canned): $1-2/can
        - Rice: $10-15/5lb bag
        - Spices: $3-8 each
        """
    else:
        result = f"Search results for: {query}. (No specific data found for this query in the mock system.)"

    return json.dumps({"search_query": query, "results": result})


# ============================================================================
# AGENT INSTRUCTIONS (Prompts for the specialized tasks)
# ============================================================================

# The system now delegates tasks by passing the correct instruction string (prompt)
# to the main orchestration function.

MEAL_PLANNER_INSTRUCTION = """
You are an expert meal planner and nutritionist. Your job is to create 
detailed weekly meal plans that:
1. Respect all dietary restrictions and preferences (use get_user_preferences)
2. Include variety and nutritional balance.
3. Stay within budget constraints.
4. Use web_search_tool to find recipe ideas and prices.

Format the output as a structured weekly plan with sections for each day and meal.
"""

SHOPPING_AGENT_INSTRUCTION = """
You are a smart shopping assistant. Based on the provided meal plan, you must create:
1. An organized shopping list by store section (produce, dairy, pantry, etc.)
2. Consolidated quantities for all ingredients.
3. Price estimates (use web_search_tool for current prices).
4. Money-saving suggestions.

Format the output as a structured shopping list with categories and totals.
"""

TRAVEL_PLANNER_INSTRUCTION = """
You are an expert travel planner specializing in personalized itineraries. 
Create a detailed travel itinerary that:
1. Matches the user's interests and travel style (use get_user_preferences).
2. Stays within budget.
3. Uses web_search_tool for research.
4. Includes day-by-day schedules, accommodation, restaurant suggestions, and a budget breakdown.

Format the output as a comprehensive travel guide.
"""

# ============================================================================
# MAIN ORCHESTRATION LOGIC (Replaces the deprecated Agent class)
# ============================================================================

def process_agent_request(
    prompt: str,
    system_instruction: str,
    tools: List[Callable]
) -> types.GenerateContentResponse:
    """
    Sends a request to the Gemini model with a specific instruction and tools.
    Handles the execution of function calls required by the model (Tool Calling).
    
    This function replaces the functionality of the deprecated LoopAgent/Agent.
    """
    
    # 1. First model call: Get the initial response (which may include a function call)
    response = CLIENT.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools
        )
    )

    # 2. Check for tool calls and execute them
    if not response.function_calls:
        return response

    # 3. Handle tool calls (max 3 iterations for robust plan generation)
    function_calls = response.function_calls
    call_history = [response]
    
    for _ in range(3):
        tool_outputs = []
        for call in function_calls:
            # Look up the actual Python function by name
            tool_func = next((t for t in tools if t.__name__ == call.name), None)

            if tool_func:
                print(f"    ➡️ Calling Tool: {call.name}({dict(call.args)})")
                try:
                    # Execute the tool and get the result
                    result = tool_func(**dict(call.args))
                    
                    tool_outputs.append(types.Part.from_function_response(
                        name=call.name, 
                        response={"result": result}
                    ))
                except Exception as e:
                    tool_outputs.append(types.Part.from_function_response(
                        name=call.name, 
                        response={"error": str(e)}
                    ))
            else:
                print(f"    ⚠️ Tool not found: {call.name}")
        
        # Add tool call and output to the history
        call_history.extend(tool_outputs)
        
        # 4. Second model call (and subsequent retries): Send tool outputs back to the model
        response = CLIENT.models.generate_content(
            model='gemini-2.5-flash',
            contents=call_history,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=tools
            )
        )
        call_history.append(response)
        
        # If the model gives a final text response, we are done
        if response.text:
            return response
        
        # If the model requests another function call, loop again
        function_calls = response.function_calls
        if not function_calls:
            break

    # Return the last response, even if it's incomplete after max iterations
    return response


# ============================================================================
# CONCIERGE ORCHESTRATOR (Routes the request)
# ============================================================================

def route_request(user_prompt: str, context: str) -> types.GenerateContentResponse:
    """
    Determines the correct agent (instruction) and tools to use, 
    then processes the request.
    """
    
    # Simple routing based on keywords
    user_prompt_lower = user_prompt.lower()
    
    if "meal plan" in user_prompt_lower or "recipe" in user_prompt_lower or "dinner" in user_prompt_lower:
        instruction = MEAL_PLANNER_INSTRUCTION
        tools = [web_search_tool, get_user_preferences, save_plan_to_file]
        task_name = "Meal Planning"
        
    elif "shopping list" in user_prompt_lower or "grocery" in user_prompt_lower:
        instruction = SHOPPING_AGENT_INSTRUCTION
        tools = [web_search_tool, get_user_preferences, save_plan_to_file]
        task_name = "Shopping List Generation"
        
    elif "travel" in user_prompt_lower or "trip" in user_prompt_lower or "itinerary" in user_prompt_lower:
        instruction = TRAVEL_PLANNER_INSTRUCTION
        tools = [web_search_tool, get_user_preferences, save_plan_to_file]
        task_name = "Travel Planning"

    else:
        # Default instruction for general inquiries
        instruction = """
        You are the Smart Life Concierge. Analyze the user's request. 
        If it matches one of your core services (Meal Planning, Shopping, Travel), 
        politely ask the user to be more specific so you can delegate the task 
        to the appropriate specialist agent.
        """
        tools = [get_user_preferences]
        task_name = "General Inquiry/Clarification"
        
    full_prompt = f"{context}\n\nCurrent request: {user_prompt}"
    
    print(f"    ⭐ Delegating to: {task_name}")
    return process_agent_request(full_prompt, instruction, tools)


# ============================================================================
# SESSION AND MEMORY MANAGEMENT (Unchanged)
# ============================================================================

class ConciergeSession:
    """
    Manages user sessions and long-term memory.
    Tracks preferences, past plans, and user feedback.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session_history = []
        self.preferences = {} # Note: get_user_preferences is currently a mock function
        self.past_plans = []
        self.created_at = datetime.now()
        
    def add_interaction(self, request: str, response: str):
        """Records an interaction in session history"""
        self.session_history.append({
            "timestamp": datetime.now().isoformat(),
            "request": request,
            "response": response
        })
    
    def get_context(self) -> str:
        """Returns context from previous interactions"""
        if not self.session_history:
            return "No previous interactions."
        
        recent = self.session_history[-3:]  # Last 3 interactions
        context = "Recent interactions (use this for context):\n"
        for interaction in recent:
            # Use 'request' only for context to avoid huge prompt dumps
            context += f"- USER: {interaction['request'][:150]}...\n"
        return context
    
    def save_session(self):
        """Persists session data to storage"""
        session_data = {
            "user_id": self.user_id,
            "history": self.session_history,
            "preferences": self.preferences,
            "past_plans": self.past_plans,
            "created_at": self.created_at.isoformat()
        }
        
        os.makedirs("sessions", exist_ok=True)
        filepath = f"sessions/{self.user_id}_session.json"
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return filepath


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main entry point for the Smart Life Concierge Agent.
    """
    
    if CLIENT is None:
        print("🔴 Failed to run main(): Gemini Client is not initialized. Please set GOOGLE_API_KEY.")
        exit(1)

    print("Initializing Smart Life Concierge Agent...")
    
    # Create a session for the user
    session = ConciergeSession(user_id="demo_user_001")
    
    print("\n" + "="*60)
    print("🏠 SMART LIFE CONCIERGE - Your AI Personal Assistant")
    print("="*60)
    print("\nI can help you with:")
    print("  🍽️  Meal Planning - Create personalized weekly meal plans")
    print("  🛒 Shopping Lists - Generate smart grocery lists")
    print("  ✈️  Travel Planning - Plan complete travel itineraries")
    print("\nType 'exit' to quit")
    print("="*60 + "\n")
    
    # Interactive loop
    while True:
        user_input = input("\nHow can I help you today? > ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("\nThank you for using Smart Life Concierge! 👋")
            session_path = session.save_session()
            print(f"Session saved to: {session_path}")
            break
        
        if not user_input:
            continue
        
        try:
            # Add context from previous interactions
            context = session.get_context()
            
            # Send to the main router
            print("\n🤔 Processing your request...")
            response = route_request(user_input, context)
            
            # Extract text from response
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            print(f"\n{response_text}\n")
            
            # Record interaction
            session.add_interaction(user_input, response_text)
            
        except Exception as e:
            print(f"\n❌ A serious error occurred: {str(e)}")
            print("Please check your API key and connection, then try again.\n")


if __name__ == "__main__":
    # Check for API key (re-check for safety)
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Please set GOOGLE_API_KEY environment variable")
        print("Example: export GOOGLE_API_KEY='your-api-key-here'")
        exit(1)
    
    main()
