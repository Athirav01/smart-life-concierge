"""
Example usage script for Smart Life Concierge Agent
Demonstrates key features and typical workflows
"""

from concierge_agent import (
    route_request, 
    ConciergeSession,
    save_plan_to_file
)
import os
from google.genai import types  


def extract_text_from_response(response: types.GenerateContentResponse) -> str:
    """Helper to safely extract text from the response object."""
    return response.text if hasattr(response, 'text') and response.text else str(response)

def run_demo(session: ConciergeSession, request: str):
    """
    Standardized function to run a request through the new router logic.
    """
    # 1. Get context from the session
    context = session.get_context()
    
    # 2. Call the new routing function
    response = route_request(
        user_prompt=request,
        context=context
    )
    
    # 3. Process response
    response_text = extract_text_from_response(response)
    print(response_text)
    
    # 4. Save the interaction
    session.add_interaction(request, response_text)
    return response_text


# ============================================================================
# DEMO FUNCTIONS (Updated to use run_demo helper)
# ============================================================================

def demo_meal_planning():
    """
    Demonstrates meal planning workflow
    """
    print("\n" + "="*60)
    print("DEMO 1: Meal Planning")
    print("="*60)
    
    session = ConciergeSession(user_id="demo_meal_user")
    
    # Example request
    request = """
    Create a vegetarian meal plan for this week with these requirements:
    - Budget: $150 max
    - Calories: around 2000/day
    - Avoid mushrooms and olives
    - Include a mix of Italian, Indian, and Mexican cuisines
    - Quick weekday meals (under 30 min), can be longer on weekends
    """
    
    print(f"\nRequest: {request}")
    print("\nProcessing...\n")
    
    try:
        response_text = run_demo(session, request)
        
        # Save the meal plan to file
        # Note: The model might call save_plan_to_file itself, but this is a fail-safe
        save_plan_to_file("meal_plan_week1.md", response_text)
        print("\n✓ Meal plan saved to output/meal_plan_week1.md")
        
    except Exception as e:
        print(f"Error: {e}")


def demo_shopping_list():
    """
    Demonstrates shopping list generation from meal plan
    """
    print("\n" + "="*60)
    print("DEMO 2: Shopping List Generation")
    print("="*60)
    
    session = ConciergeSession(user_id="demo_shopping_user")
    
    # This request assumes a prior meal plan was generated (or relies on the model's ability to mock one)
    request = """
    Based on a simple vegetarian meal plan (Italian/Indian/Mexican mix for 4 days),
    create a detailed shopping list organized by store section.
    Include:
    - Quantities for each item
    - Estimated prices
    - Tips for finding deals
    - Total cost estimate
    
    Assume basic pantry staples are available (oil, salt, pepper, etc.)
    """
    
    print(f"\nRequest: {request}")
    print("\nProcessing...\n")
    
    try:
        response_text = run_demo(session, request)
        
        save_plan_to_file("shopping_list.md", response_text)
        print("\n✓ Shopping list saved to output/shopping_list.md")
        
    except Exception as e:
        print(f"Error: {e}")


def demo_travel_planning():
    """
    Demonstrates travel planning workflow
    """
    print("\n" + "="*60)
    print("DEMO 3: Travel Planning")
    print("="*60)
    
    session = ConciergeSession(user_id="demo_travel_user")
    
    request = """
    Plan a 5-day trip for someone who:
    - Loves food and temples
    - Enjoys hiking and nature
    - Prefers boutique hotels
    - Budget: $200/day
    - Wants a relaxed pace
    
    Suggest the best destination and create a complete itinerary.
    """
    
    print(f"\nRequest: {request}")
    print("\nProcessing...\n")
    
    try:
        response_text = run_demo(session, request)
        
        save_plan_to_file("travel_itinerary_kyoto.md", response_text)
        print("\n✓ Travel itinerary saved to output/travel_itinerary_kyoto.md")
        
    except Exception as e:
        print(f"Error: {e}")


def demo_context_memory():
    """
    Demonstrates session memory and context preservation
    """
    print("\n" + "="*60)
    print("DEMO 4: Context Memory")
    print("="*60)
    
    session = ConciergeSession(user_id="demo_memory_user")
    
    # First interaction - Set preference
    request1 = "I am strictly vegetarian and allergic to nuts."
    print(f"\nInteraction 1: {request1}")
    
    try:
        response1_text = run_demo(session, request1)
        print(f"Agent: {response1_text[:80]}...\n")
        
        # Second interaction - Request a task that needs the preference
        request2 = "Now, please create a 3-day meal plan for me."
        print(f"Interaction 2: {request2}")
        
        # The run_demo helper automatically includes session context for this call
        response2_text = run_demo(session, request2)
        print(f"Agent: {response2_text[:300]}...")
        
        # Save session
        session_file = session.save_session()
        print(f"\n✓ Session saved to {session_file}")
        print("Note: The agent should incorporate your dietary restrictions into the meal plan!")
        
    except Exception as e:
        print(f"Error: {e}")


def demo_multi_agent_coordination():
    """
    Demonstrates multi-agent coordination for complex workflow
    (Now implemented as a single prompt triggering multiple Tool Calls and structured output)
    """
    print("\n" + "="*60)
    print("DEMO 5: Multi-Agent Coordination")
    print("="*60)
    
    session = ConciergeSession(user_id="demo_coordination_user")
    
    request = """
    I'm hosting a dinner party this Saturday for 6 people.
    Help me plan the whole event:
    1. Plan a 3-course vegetarian menu (appetizer, main, dessert) using Mediterranean cuisine.
    2. Create a comprehensive shopping list.
    3. Suggest a wine pairing.
    4. Give me a timeline for cooking everything.
    
    Budget: $100 total. Cooking skill: Intermediate.
    """
    
    print(f"\nRequest: {request}")
    print("\nProcessing (involves research and multi-step plan generation)...\n")
    
    try:
        response_text = run_demo(session, request)
        
        save_plan_to_file("dinner_party_plan.md", response_text)
        print("\n✓ Dinner party plan saved to output/dinner_party_plan.md")
        print("\nThis demo showed the Concierge coordinating a complex task by using Tool Calling and comprehensive planning.")
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    """
    Main demo runner
    """
    print("\n" + "="*70)
    print("  SMART LIFE CONCIERGE - DEMONSTRATION SCRIPT")
    print("="*70)
    print("\nThis script demonstrates the key features of the agent:")
    print("  1. Meal Planning")
    print("  2. Shopping List Generation")
    print("  3. Travel Planning")
    print("  4. Context Memory")
    print("  5. Multi-Agent Coordination")
    print("\nNote: These demos use the refactored Tool Calling logic (in concierge_agent.py).")
    print("="*70)
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("\n⚠️  ERROR: GOOGLE_API_KEY not set")
        print("Please set your Gemini API key:")
        print("export GOOGLE_API_KEY='your-key-here'")
        return
    
    # Run demos
    demos = [
        ("1", "Meal Planning", demo_meal_planning),
        ("2", "Shopping List", demo_shopping_list),
        ("3", "Travel Planning", demo_travel_planning),
        ("4", "Context Memory", demo_context_memory),
        ("5", "Multi-Agent Coordination", demo_multi_agent_coordination),
    ]
    
    while True:
        print("\n" + "="*60)
        print("Choose a demo to run:")
        for num, name, _ in demos:
            print(f"  {num}. {name}")
        print("  0. Run all demos")
        print("  q. Quit")
        print("="*60)
        
        choice = input("\nYour choice: ").strip().lower()
        
        if choice == 'q':
            print("\nThank you for trying Smart Life Concierge! 👋")
            break
        elif choice == '0':
            for _, _, demo_func in demos:
                demo_func()
                input("\nPress Enter to continue to next demo...")
        else:
            found = False
            for num, _, demo_func in demos:
                if choice == num:
                    demo_func()
                    found = True
                    break
            if not found:
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
