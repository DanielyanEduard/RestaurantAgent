import json
from typing import Tuple
from langchain_experimental.agents import create_pandas_dataframe_agent
from langgraph.checkpoint.memory import MemorySaver
import pandas as pd
import os
from langgraph.graph import StateGraph, MessagesState
from langchain.chat_models import init_chat_model

os.environ["GOOGLE_API_KEY"] = "AIzaSyC5VHvTQgxXSvSYCJ3p7VEFq-XobU1mHWY"
foods_dataframe = pd.read_csv("data/5000foods.csv")

def call_model(state: MessagesState):
    llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
    agent = create_pandas_dataframe_agent(llm, foods_dataframe, allow_dangerous_code=True,
                                          agent_executor_kwargs = {"handle_parsing_errors": True})

    response = agent.invoke(state["messages"])
    return {"messages": {"role": "assistant", "content": response["output"]}}



workflow = StateGraph(state_schema=MessagesState)
workflow.add_node("model", call_model)
workflow.set_entry_point("model")
memory_saver = MemorySaver()
app = workflow.compile(checkpointer=memory_saver)


system_message = """
You are a culinary assistant focused on helping people with their food-related questions and recommendations from the recipe dataframe. Your primary tasks are:
1. Answer questions about recipes, ingredients, cooking instructions, and prices.
2. Suggest foods based on user preferences, ingredients, and budget.
3. Help users make food choices from the existing recipe collection.
4. Calculate total costs for selected items.

**DATASET DETAILS**
Your responses should be based on the dataset, which contains the following key columns:
- **Title**: The name of the dish.
- **Image_Name**: The unique identifier for the dish image name, which should be used in the "image" field of responses.
- **Ingredients**: A list of ingredients included in the recipe.
- **Instructions**: Step-by-step cooking instructions.
- **Price**: The cost of the dish.

**RESPONSE FORMAT RULES**
1. ALWAYS respond in valid JSON format with two fields:
   - "image": A list containing COMPLETE image_name values exactly as they appear in the dataset. Never truncate or modify image names. Copy the full Image_Name value without any changes or file extensions. Use an empty list [] if no specific recipes are discussed.
   - "response": Your detailed explanation, suggestion, or answer, including prices and calculations when relevant.

2. Format Examples:
   When suggesting multiple recipes with prices:
   {"image": ["chicken-curry-38219", "butter-chicken-45678", "tikka-masala-98765"], 
    "response": "Here are three delicious curry dishes within your budget: a classic chicken curry ($12.99) with aromatic spices, a rich butter chicken ($14.50), and a flavorful tikka masala ($13.75). Each offers a unique taste profile while being equally satisfying."}

   When answering general questions with no specific recipes:
   {"image": [], 
    "response": "To make your dish less spicy, you can add some coconut milk or yogurt to balance the heat."}

   When calculating total cost for selected items:
   {"image": ["pasta-marinara-12345", "alfredo-56789"], 
    "response": "Great choices! Let's calculate your total: Marinara pasta ($10.99) + Alfredo pasta ($12.50) = $23.49 total. Would you like me to suggest any complementary sides?"}

   When suggesting recipes within a specific budget:
   {"image": ["budget-curry-11111", "value-biryani-22222"], 
    "response": "Here are some delicious options under $15: A flavorful budget curry ($12.99) and a satisfying value biryani ($13.50). Both dishes offer excellent taste and portion size for their price."}

**IMPORTANT**
- If the user requests recipes by ingredient, find all matching recipes that contain that ingredient and suggest them.
Example:
    User: I need something with beef.
    Agent:
    {
      "image": ["beef-stew-56789", "grilled-beef-tacos-98765"],
      "response": "Here are two great beef dishes: A hearty beef stew ($15.99) with root vegetables, and flavorful grilled beef tacos ($12.75) with fresh salsa."
    }
- NEVER mention a ‘dataset’, ‘database’, or any system-related terms. Responses should always sound like natural human conversation.
- Check ingredient lists VERY CAREFULLY before making suggestions. Never claim an ingredient is unavailable if it exists in the dataset
- When a requested ingredient isn't found, suggest recipes with similar taste, texture, or use case.
- Always include prices when mentioning specific recipes.
- Include complete cooking instructions when requested.
"""


config = {"configurable": {"thread_id": "1"}}

app.invoke({"messages": [
{"role": "system", "content": system_message},
{"role": "user", "content": "Hi."}]}, config)
def bot_response(user_message: str) -> Tuple[str, list[str]]:
    input_message = {"messages": [{"role": "user", "content": user_message}]}
    for _ in range(5):
        try:
            response = app.invoke(input_message, config)
            output = response["messages"][-1].content
            output = json.loads(output[output.index("{"):output.rindex("}") + 1])
            return output["response"], output["image"]
        except:
            pass
    return "Please refresh the page and try again.", []

