"""
Example usage script for Smart Life Concierge Agent
Demonstrates key features and typical workflows
"""

from concierge_agent import (
    create_concierge_agent,
    ConciergeSession,
    save_plan_to_file
)
import os


def demo_meal_planning():
    """
    Demonstrates meal planning workflow
    """
    print("\n" + "="*60)
    print("DEMO 1: Meal Planning")
    print("="*60)
    
    concierge = create_concierge_agent()
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
        response = concierge.generate_content(request)
        print(response.text)
        
        # Save the interaction
        session.add_interaction(request, response.text)
        
        # Save the meal plan to file
        save_plan_to_file("meal_plan_week1.md", response.text)
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
    
    concierge = create_concierge_agent()
    session = ConciergeSession(user_id="demo_shopping_user")
    
    request = """
    Based on my meal plan (vegetarian, Italian/Indian/Mexican mix),
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
        response = concierge.generate_content(request)
        print(response.text)
        
        session.add_interaction(request, response.text)
        save_plan_to_file("shopping_list.md", response.text)
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
    
    concierge = create_concierge_agent()
    session = ConciergeSession(user_id="demo_travel_user")
    
    request = """
    Plan a 5-day trip for someone who:
    - Loves food and temples
    - Enjoys hiking and nature
    - Prefers boutique hotels
    - Budget: $200/day
    - Wants a relaxed pace
    
    Suggest the best destination and create a complete itinerary with:
    - Day-by-day schedule
    - Hotel recommendations
    - Restaurant suggestions
    - Activity details and timing
    - Budget breakdown
    - Local tips
    """
    
    print(f"\nRequest: {request}")
    print("\nProcessing...\n")
    
    try:
        response = concierge.generate_content(request)
        print(response.text)
        
        session.add_interaction(request, response.text)
        save_plan_to_file("travel_itinerary_kyoto.md", response.text)
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
    
    concierge = create_concierge_agent()
    session = ConciergeSession(user_id="demo_memory_user")
    
    # First interaction
    request1 = "I'm vegetarian and allergic to nuts"
    print(f"\nInteraction 1: {request1}")
    
    try:
        response1 = concierge.generate_content(request1)
        print(f"Agent: {response1.text}\n")
        session.add_interaction(request1, response1.text)
        
        # Second interaction - agent should remember preferences
        request2 = "Create a meal plan for me"
        print(f"Interaction 2: {request2}")
        
        # Add context from session
        context = session.get_context()
        full_request = f"{context}\n\nNew request: {request2}"
        
        response2 = concierge.generate_content(full_request)
        print(f"Agent: {response2.text}")
        session.add_interaction(request2, response2.text)
        
        # Save session
        session_file = session.save_session()
        print(f"\n✓ Session saved to {session_file}")
        print("Note: The agent remembered your dietary restrictions!")
        
    except Exception as e:
        print(f"Error: {e}")


def demo_multi_agent_coordination():
    """
    Demonstrates multi-agent coordination for complex workflow
    """
    print("\n" + "="*60)
    print("DEMO 5: Multi-Agent Coordination")
    print("="*60)
    
    concierge = create_concierge_agent()
    session = ConciergeSession(user_id="demo_coordination_user")
    
    request = """
    I'm hosting a dinner party this Saturday for 6 people.
    Help me:
    1. Plan a 3-course vegetarian menu (appetizer, main, dessert)
    2. Create a shopping list
    3. Suggest a wine pairing
    4. Give me a timeline for cooking everything
    
    Budget: $100 total
    Theme: Mediterranean cuisine
    Cooking skill: Intermediate
    """
    
    print(f"\nRequest: {request}")
    print("\nProcessing with multiple agents...\n")
    
    try:
        response = concierge.generate_content(request)
        print(response.text)
        
        session.add_interaction(request, response.text)
        save_plan_to_file("dinner_party_plan.md", response.text)
        print("\n✓ Dinner party plan saved to output/dinner_party_plan.md")
        print("\nThis demo showed coordination between:")
        print("  - Meal Planner Agent (menu creation)")
        print("  - Shopping Agent (shopping list)")
        print("  - Main Coordinator (timeline & wine pairing)")
        
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
    print("\nNote: These demos use simulated data for tool responses.")
    print("In production, they would use real web search and APIs.")
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
            for num, name, demo_func in demos:
                if choice == num:
                    demo_func()
                    break
            else:
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
