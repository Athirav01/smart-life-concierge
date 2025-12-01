"""
Smart Life Concierge Agent - Main Orchestrator
A multi-agent system for meal planning, shopping, and travel assistance.
"""

from google import genai
from google.genai import types
from google.genai.agents import Agent, LoopAgent
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any


# ============================================================================
# CUSTOM TOOLS
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
        return f"Successfully saved to {filepath}"
    except Exception as e:
        return f"Error saving file: {str(e)}"


def get_user_preferences(preference_type: str) -> Dict[str, Any]:
    """
    Retrieves stored user preferences from memory.
    
    Args:
        preference_type: Type of preferences (dietary, travel, budget)
    
    Returns:
        Dictionary of user preferences
    """
    # In a real implementation, this would read from a database or file
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
    # In production, this would use actual web search API
    # For demo, returning structured sample data
    if "recipe" in query.lower():
        return """
        Found 5 recipes:
        1. Easy Vegetarian Pasta Primavera (30 min, $12 for 4 servings)
        2. Quick Indian Dal Tadka (25 min, $8 for 4 servings)
        3. Mexican Black Bean Tacos (20 min, $10 for 4 servings)
        4. Mediterranean Chickpea Salad (15 min, $9 for 4 servings)
        5. Thai Vegetable Stir-fry (25 min, $11 for 4 servings)
        """
    elif "travel" in query.lower():
        return """
        Travel recommendations:
        - Kyoto, Japan: Rich culture, temples, excellent food scene
        - Barcelona, Spain: Architecture, beaches, vibrant nightlife
        - Portland, Oregon: Nature, breweries, food trucks
        - Edinburgh, Scotland: History, hiking, festivals
        """
    elif "grocery" in query.lower() or "price" in query.lower():
        return """
        Current grocery prices:
        - Fresh vegetables: $3-5/lb
        - Pasta: $2-3/box
        - Beans (canned): $1-2/can
        - Rice: $10-15/5lb bag
        - Spices: $3-8 each
        """
    return f"Search results for: {query}"


# ============================================================================
# VALIDATION AGENTS
# ============================================================================

class MealPlanValidator(Agent):
    """
    Validates that a meal plan meets quality standards.
    Checks for nutritional balance, variety, and budget compliance.
    """
    
    def __init__(self):
        super().__init__(
            name="meal_plan_validator",
            model="gemini-2.0-flash-exp",
            description="Validates meal plans for quality and completeness",
            instruction="""
            You are a meal plan validator. Check that the meal plan:
            1. Contains all requested days and meals
            2. Provides variety (no repeated meals in same week)
            3. Includes nutritional information
            4. Stays within budget constraints
            5. Respects dietary restrictions
            
            If validation passes, escalate with EventActions(escalate=True).
            If validation fails, do nothing (return empty result) to trigger retry.
            """
        )
    
    def run(self, meal_plan: str) -> Dict[str, Any]:
        """Validates meal plan structure and content"""
        # Check for minimum required elements
        required_elements = ["Day", "Breakfast", "Lunch", "Dinner", "Calories"]
        
        if all(elem in meal_plan for elem in required_elements):
            return {"valid": True, "escalate": True}
        return {}


class ShoppingListValidator(Agent):
    """
    Validates that shopping lists are complete and organized.
    """
    
    def __init__(self):
        super().__init__(
            name="shopping_list_validator",
            model="gemini-2.0-flash-exp",
            description="Validates shopping lists for completeness",
            instruction="""
            You are a shopping list validator. Check that the list:
            1. Is organized by category (produce, pantry, etc.)
            2. Includes quantities for each item
            3. Has estimated prices
            4. Totals within budget
            
            If validation passes, escalate with EventActions(escalate=True).
            If validation fails, return empty result to trigger retry.
            """
        )


# ============================================================================
# SPECIALIZED SUB-AGENTS
# ============================================================================

def create_meal_planner_agent() -> LoopAgent:
    """
    Creates the meal planning agent with retry logic.
    This agent generates weekly meal plans based on preferences.
    """
    meal_planner = Agent(
        name="meal_planner",
        model="gemini-2.0-flash-exp",
        description="Expert nutritionist and meal planning specialist",
        instruction="""
        You are an expert meal planner and nutritionist. Your job is to create 
        detailed weekly meal plans that:
        
        1. Respect all dietary restrictions and preferences
        2. Provide nutritional balance (protein, carbs, fats, vitamins)
        3. Include variety across the week (no repetitive meals)
        4. Stay within budget constraints
        5. Include prep time and difficulty level
        6. Suggest make-ahead options for busy days
        
        For each meal, provide:
        - Meal name
        - Ingredients list with quantities
        - Estimated calories and macros
        - Preparation time
        - Brief cooking instructions
        
        Format the output as a structured weekly plan with sections for each day.
        """,
        tools=[web_search_tool, get_user_preferences]
    )
    
    # Wrap in LoopAgent for retry capability with validation
    return LoopAgent(
        name="robust_meal_planner",
        agents=[meal_planner, MealPlanValidator()],
        max_iterations=3
    )


def create_shopping_agent() -> Agent:
    """
    Creates the shopping list generator agent.
    Converts meal plans into organized shopping lists.
    """
    return Agent(
        name="shopping_agent",
        model="gemini-2.0-flash-exp",
        description="Smart shopping assistant that creates optimized grocery lists",
        instruction="""
        You are a smart shopping assistant. Based on meal plans, you create:
        
        1. Organized shopping lists by store section (produce, dairy, pantry, etc.)
        2. Consolidated quantities (combine ingredients used in multiple recipes)
        3. Price estimates for each item
        4. Money-saving suggestions (sales, substitutions, bulk buying)
        5. Store recommendations for best prices
        
        Check pantry staples and only include items likely to be needed.
        Prioritize seasonal produce for better prices.
        
        Format the output as a structured shopping list with categories and totals.
        """,
        tools=[web_search_tool, get_user_preferences]
    )


def create_travel_planner_agent() -> Agent:
    """
    Creates the travel planning agent.
    Researches and plans complete travel itineraries.
    """
    return Agent(
        name="travel_planner",
        model="gemini-2.0-flash-exp",
        description="Expert travel planner specializing in personalized itineraries",
        instruction="""
        You are an expert travel planner. Create detailed travel itineraries that:
        
        1. Match the user's interests and travel style
        2. Stay within budget constraints
        3. Balance activities with relaxation
        4. Include practical logistics (transportation, timing)
        5. Recommend specific restaurants, hotels, and attractions
        6. Provide local tips and cultural insights
        7. Suggest day-by-day schedules with flexibility
        
        For each itinerary, include:
        - Destination overview and why it's a good fit
        - Day-by-day schedule with activities
        - Accommodation recommendations
        - Restaurant suggestions (breakfast, lunch, dinner)
        - Transportation options
        - Budget breakdown
        - Packing suggestions
        - Local customs and tips
        
        Format as a comprehensive travel guide.
        """,
        tools=[web_search_tool, get_user_preferences]
    )


# ============================================================================
# MAIN COORDINATOR AGENT
# ============================================================================

def create_concierge_agent() -> Agent:
    """
    Creates the main concierge coordinator agent.
    This is the primary interface that routes requests to specialized agents.
    """
    
    # Initialize all sub-agents
    meal_planner = create_meal_planner_agent()
    shopping_agent = create_shopping_agent()
    travel_planner = create_travel_planner_agent()
    
    # Create main coordinator
    concierge = Agent(
        name="smart_life_concierge",
        model="gemini-2.0-flash-exp",
        description="AI personal assistant for meal planning, shopping, and travel",
        instruction="""
        You are a Smart Life Concierge - an AI personal assistant that helps users 
        manage their daily life through intelligent automation.
        
        Your capabilities:
        1. MEAL PLANNING: Create personalized weekly meal plans
        2. SHOPPING: Generate smart grocery lists with budget optimization
        3. TRAVEL: Plan complete travel itineraries with personalized recommendations
        
        Workflow:
        1. Understand the user's request and which service they need
        2. Delegate to the appropriate specialist agent
        3. Review the output for quality and completeness
        4. Present results to the user in a friendly, organized manner
        5. Offer to save plans to files or make adjustments
        
        Always:
        - Be proactive and helpful
        - Remember user preferences from previous interactions
        - Provide actionable, specific recommendations
        - Explain your reasoning when making suggestions
        - Offer options when multiple good solutions exist
        
        Start each interaction by warmly greeting the user and asking how you can help.
        """,
        sub_agents=[meal_planner, shopping_agent, travel_planner],
        tools=[save_plan_to_file, get_user_preferences, web_search_tool]
    )
    
    return concierge


# ============================================================================
# SESSION AND MEMORY MANAGEMENT
# ============================================================================

class ConciergeSession:
    """
    Manages user sessions and long-term memory.
    Tracks preferences, past plans, and user feedback.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session_history = []
        self.preferences = {}
        self.past_plans = []
        self.created_at = datetime.now()
        
    def add_interaction(self, request: str, response: str):
        """Records an interaction in session history"""
        self.session_history.append({
            "timestamp": datetime.now().isoformat(),
            "request": request,
            "response": response
        })
    
    def update_preferences(self, preference_type: str, data: Dict):
        """Updates user preferences based on feedback"""
        self.preferences[preference_type] = data
    
    def get_context(self) -> str:
        """Returns context from previous interactions"""
        if not self.session_history:
            return "No previous interactions"
        
        recent = self.session_history[-3:]  # Last 3 interactions
        context = "Recent interactions:\n"
        for interaction in recent:
            context += f"- {interaction['request'][:100]}...\n"
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
    Sets up the agent and handles user interactions.
    """
    
    # Initialize the concierge agent
    print("Initializing Smart Life Concierge Agent...")
    concierge = create_concierge_agent()
    
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
            session.save_session()
            print(f"Session saved to: sessions/{session.user_id}_session.json")
            break
        
        if not user_input:
            continue
        
        try:
            # Add context from previous interactions
            context = session.get_context()
            full_prompt = f"{context}\n\nCurrent request: {user_input}"
            
            # Send to agent
            print("\n🤔 Processing your request...")
            response = concierge.generate_content(full_prompt)
            
            # Extract text from response
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            print(f"\n{response_text}\n")
            
            # Record interaction
            session.add_interaction(user_input, response_text)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again with a different request.\n")


if __name__ == "__main__":
    # Set up API key (user needs to provide their own)
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Please set GOOGLE_API_KEY environment variable")
        print("Example: export GOOGLE_API_KEY='your-api-key-here'")
        exit(1)
    
    main()
