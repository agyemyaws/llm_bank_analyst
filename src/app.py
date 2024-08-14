from fastapi import FastAPI, HTTPException
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceHub
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import SequentialChain, LLMChain
from src.config import *
from src.db_connect import fetch_data_as_json
import json
import os
from pathlib import Path
import sys

# Get the absolute path to the project root
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Set environment variables for Langchain 
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY 

# Initialize FastAPI app
app = FastAPI(
    title="Bank Product Recommendation System",
    version="1.0",
    description="API for generating bank product recommendations using LangChain"
)

# Create a dictionary for direct customer lookup
customer_lookup = {}
documents = []

customers_json = project_root / 'data/customers.json'
products_json = project_root / 'data/products.json'

# Load and process customer data from MySQL
customer_data_loaded = fetch_data_as_json("Customers", customers_json)
with open(customers_json, 'r') as json_file:
    customer_dataset = json.load(json_file)
    for customer in customer_dataset:
    # Store customer data for direct lookup
        customer_lookup[customer["CustomerID"]] = customer


# Load product data from MySQL
product_data_loaded = fetch_data_as_json("Products", products_json)
with open(products_json, 'r') as json_file:
    product_dataset = json.load(json_file)
    

# Defining prompts
first_template = """
Task: Analyze bank customer data and provide financial insights.
Customer Information: {query}

Please provide a structured analysis including:
1. Financial Status Overview
2. Risk Assessment
3. Key Financial Needs
4. Opportunities for Financial Growth

Analysis:
"""

second_template = """
Task: Recommend suitable banking products based on customer analysis.
Customer Analysis: {customer_analysis}
Available Products: {product_info}

Please provide recommendations including:
1. Top Recommended Products
2. Justification for Each Product
3. Expected Benefits
4. Risk Considerations

Recommendation:
"""

# Initialize model and prompts
model = HuggingFaceHub(repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1", model_kwargs={"temperature": 0.6, "max_new_tokens": 1024})  # Commented out HuggingFace
#model = ChatOpenAI(model="gpt-4o-mini")

first_prompt = PromptTemplate(input_variables=["query"], template=first_template)
second_prompt = PromptTemplate(input_variables=["customer_analysis", "product_info"], template=second_template)

# Combine both chains into a SequentialChain
first_chain = LLMChain(llm=model, prompt=first_prompt, output_key="customer_analysis", verbose=True)
second_chain = LLMChain(llm=model, prompt=second_prompt, output_key="final_recommendation", verbose=True)

sequential_chain = SequentialChain(
    chains=[first_chain, second_chain],
    input_variables=["query", "product_info"],
    output_variables=["final_recommendation"]
)

# Define the route to get all customer IDs
@app.get("/customers")
async def get_customer_ids():
    return {"customer_ids": list(customer_lookup.keys())}

# Define the route to generate recommendations
@app.post("/recommendation")
async def generate_recommendation(customer_id: str):
    if customer_id not in customer_lookup:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer_info = json.dumps(customer_lookup[customer_id], indent=4)
    
    product_info = "\n".join(
        [f"Name: {prod['name']}, Category: {prod['category']}, Features: {prod['features']}, Description: {prod['description']}" 
        for prod in product_dataset]
    )
    
    result = sequential_chain({"query": customer_info, "product_info": product_info})
    
    return {"recommendation": result["final_recommendation"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)