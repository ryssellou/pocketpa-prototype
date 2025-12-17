import google.generativeai as genai
from datetime import datetime
import json
import os
import time

# Configure Gemini with API key from environment variable
# Note: Set GOOGLE_API_KEY environment variable before running
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))

class PocketPAChiefOfStaff:
    """
    Main router for PocketPA - implementing the Mindstone OS architecture.
    Acts as the 'Chief of Staff' agent that routes user requests to the appropriate specialized skill.
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Updated model name
        self.load_configuration()
        
    def load_configuration(self):
        """Loads the core agent configuration and valid skills index."""
        print("📚 Loading PocketPA configuration...")
        
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        try:
            with open(os.path.join(base_path, 'AGENTS.md'), 'r', encoding='utf-8') as f:
                self.agents_config = f.read()
            
            with open(os.path.join(base_path, 'TABLE-OF-CONTENTS.md'), 'r', encoding='utf-8') as f:
                self.toc = f.read()
            
            print("✅ Configuration loaded successfully\n")
        except FileNotFoundError as e:
            print(f"❌ Error loading configuration: {e}")
            print(f"Base path: {base_path}")
            raise

    def route_request(self, user_input, conversation_context):
        """
        Semantic Router: Analyzes user intent and selects the best skill.
        """
        # Take the last few messages for context to avoid token limit issues
        recent_context = conversation_context[-3:] if len(conversation_context) > 3 else conversation_context
        
        routing_prompt = f"""
You are the Chief of Staff for PocketPA. Your job is to analyze the user's request and route it to the most appropriate skill.

SYSTEM CONFIGURATION:
{self.agents_config}

AVAILABLE SKILLS INDEX:
{self.toc}

CONVERSATION CONTEXT:
{json.dumps(recent_context, indent=2)}

USER'S LATEST REQUEST: "{user_input}"

Analyze the user's intent carefully. Consider:
- What are they trying to accomplish? (Reporting, Asking Policy, Training?)
- Which skill file matches this intent?

Respond with ONLY the skill name (e.g., "incident-report", "policy-query", "micro-training"). 
If unsure, default to "incident-report".
        """
        
        try:
            response = self.model.generate_content(routing_prompt)
            skill_name = response.text.strip().lower()
            
            # Normalize skill name
            skill_name = skill_name.replace('.md', '').replace('skills/', '').strip()
            
            print(f"🔀 Routing decision: '{skill_name}'")
            return skill_name
            
        except Exception as e:
            print(f"⚠️ Routing error: {e}")
            return "incident-report"  # Safe fallback

    def execute_skill(self, skill_name, user_input, conversation_history):
        """
        Executes the selected skill by loading its specific instructions (system prompt)
        and passing the conversation context to the LLM.
        """
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skill_path = os.path.join(base_path, 'skills', f"{skill_name}.md")
        
        # Fallback if skill doesn't exist
        if not os.path.exists(skill_path):
            print(f"⚠️ Skill file not found: {skill_path}")
            return f"I'm sorry, I don't know how to handle '{skill_name}' yet. Please try 'incident-report'."
        
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                skill_content = f.read()
        except Exception as e:
            return f"❌ Error loading skill definition: {e}"
        
        print(f"📖 Executing skill: {skill_name}")
        
        # Execution Prompt
        execution_prompt = f"""
You are PocketPA, executing the '{skill_name}' skill for care home staff.

SKILL INSTRUCTIONS (Follow these strictly):
{skill_content}

CONVERSATION HISTORY:
{json.dumps(conversation_history, indent=2)}

USER'S LATEST MESSAGE: "{user_input}"

Instructions:
1. Adhere to the 'Detailed Workflow' in the skill instructions.
2. Maintain a warm, professional, and supportive tone.
3. If gathering information, ask ONE question at a time.
4. Check for missing required fields if applicable.

Respond naturally to the user:
        """
        
        try:
            response = self.model.generate_content(execution_prompt)
            return response.text
        except Exception as e:
            return f"❌ AI Execution error: {e}"

    def chat(self, user_input, conversation_history=None):
        """
        Main entry point for the conversation.
        Updates history, routes request, executes skill, and returns response.
        """
        if conversation_history is None:
            conversation_history = []
        
        # Append user message
        conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # 1. Route
        skill = self.route_request(user_input, conversation_history)
        
        # 2. Execute
        response_text = self.execute_skill(skill, user_input, conversation_history)
        
        # Append assistant message
        conversation_history.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now().isoformat(),
            "skill_used": skill
        })
        
        return response_text, conversation_history


def demo_conversation():
    """
    Simulates a full realistic conversation to demonstrate the system capabilities.
    """
    print("=" * 80)
    print("🎯 PocketPA PROTOTYPE - Automated System Demo")
    print("=" * 80)
    print("\nStarting Chief of Staff Agent...\n")
    
    try:
        pa = PocketPAChiefOfStaff()
    except Exception as e:
        print("Failed to initialize PocketPA. Exiting.")
        return

    conversation_history = []
    
    # Scripted interaction for the demo
    # Scenario: A staff member reporting a behavioral incident
    test_messages = [
        "Hi PocketPA, I need to report an incident with Marcus.",
        "We were in the dining room about 20 minutes ago.",
        "He threw his plate on the floor because he didn't like the food.",
        "Just me and Dave were there.",
        "He was fine before, but got angry really fast when he saw the peas.",
        "He was screaming during it, but he's calm now.",
        "We just talked to him and cleaned it up. No physical restraint needed.",
        "No injuries, just a broken plate.",
        "We'll offer him a different vegetable next time.",
        "Yes, that looks correct."
    ]
    
    print(f"📝 Running through {len(test_messages)} test scenarios...\n")
    
    for i, msg in enumerate(test_messages, 1):
        print(f"\n{'-'*60}")
        print(f"💬 Turn {i}: User Input")
        print(f"{'-'*60}")
        print(f"User: {msg}\n")
        
        # Simulate processing time
        time.sleep(1) 
        
        response, conversation_history = pa.chat(msg, conversation_history)
        
        print(f"🤖 PocketPA Response:\n{response}")
    
    # Save the resulting memory
    print(f"\n{'='*80}")
    print("💾 PERSISTING MEMORY")
    print(f"{'='*80}")
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_path, "memory", "staff-contexts", "demo-staff")
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "conversation.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(conversation_history, f, indent=2)
        
    print(f"✅ Conversation history saved to: {output_file}")
    print("🎉 Demo complete. System is fully operational.")

if __name__ == "__main__":
    demo_conversation()
