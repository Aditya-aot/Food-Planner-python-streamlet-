# streamlit run food_planner.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import requests
import json
import io
from datetime import datetime, timedelta
import base64
from io import BytesIO
import os
import random
from urllib.parse import quote

# Use Streamlit for a web interface
st.title("Emergency Food Planner")

# Sidebar for inputs
with st.sidebar:
    st.header("Your Food Inventory")
    food_items = st.text_area("Enter food items (one per line):", 
                             placeholder="1kg rice\n2 apples\n4L milk\n20 bread slices\n3 chips packet")
    
    st.header("Optional Settings")
    use_optional = st.checkbox("Specify people and duration")
    
    people_data = []
    if use_optional:
        num_people = st.number_input("Number of people", min_value=1, value=1)
        
        for i in range(int(num_people)):
            col1, col2 = st.columns(2)
            with col1:
                person_type = st.selectbox(f"Person {i+1} type", 
                                          ["Adult", "Teen", "Child", "Infant", "Elderly"], key=f"type_{i}")
            with col2:
                age = st.number_input(f"Age", min_value=0, max_value=100, value=30, key=f"age_{i}")
            
            people_data.append({"type": person_type, "age": age})
        
        # Default to 7 days (one week)
        days = st.number_input("Days to plan for", min_value=1, max_value=30, value=7)
        
        # Calorie calculator
        total_daily_calories = 0
        for person in people_data:
            if person["type"] == "Adult":
                total_daily_calories += 2000
            elif person["type"] == "Teen":
                total_daily_calories += 2500
            elif person["type"] == "Child":
                total_daily_calories += 1500
            elif person["type"] == "Infant":
                total_daily_calories += 800
            elif person["type"] == "Elderly":
                total_daily_calories += 1800
                
        st.info(f"Estimated daily calorie need: {total_daily_calories} calories")

# Dictionary of food images for common ingredients - using base64 encoded images
FOOD_IMAGES = {
    "rice": "https://images.unsplash.com/photo-1536304929831-ee1ca9d44906",
    "pancakes": "https://images.unsplash.com/photo-1565299543923-37dd37887442",
    "bread": "https://images.unsplash.com/photo-1549931319-a545dcf3bc7c",
    "apple": "https://images.unsplash.com/photo-1570913149827-d2ac84ab3f9a",
    "milk": "https://images.unsplash.com/photo-1550583724-b2692b85b150",
    "chips": "https://images.unsplash.com/photo-1566478989037-eec170784d0b",
    "pasta": "https://images.unsplash.com/photo-1551462147-37885acc36f1",
    "ramen": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624",
    "soup": "https://images.unsplash.com/photo-1547592180-85f173990554",
    "stew": "https://images.unsplash.com/photo-1604152135912-04a022e23696",
    "oatmeal": "https://images.unsplash.com/photo-1614961233913-a5113a4a34ed",
    "cereal": "https://unsplash.com/photos/oatmeal-with-milk--0gya0UbwPs",
    "toast": "https://images.unsplash.com/photo-1525351484163-7529414344d8",
    "sandwich": "https://images.unsplash.com/photo-1553909489-cd47e0907980",
    "curry": "https://images.unsplash.com/photo-1505253758473-96b7015fcd40",
    "stir fry": "https://images.unsplash.com/photo-1512058564366-18510be2db19",
    "casserole": "https://images.unsplash.com/photo-1549240923-93a2e080e653",
    "default": "https://images.unsplash.com/photo-1498837167922-ddd27525d352"
}

# Function to get food images
def get_food_image_url(keyword):
    # Look for keyword in our dictionary
    for key in FOOD_IMAGES:
        if key in keyword.lower():
            return FOOD_IMAGES[key]
    
    # If not found, return default food image
    return FOOD_IMAGES["default"]

# Parse ingredients into a proper inventory
def parse_inventory(items_text):
    inventory = {}
    items_list = items_text.strip().split('\n')
    
    for item in items_list:
        # Try to extract quantity and name
        parts = item.split(' ', 1)
        if len(parts) == 2:
            try:
                # Check if first part is numeric
                if parts[0][0].isdigit():
                    quantity = parts[0]
                    name = parts[1]
                    inventory[name] = {"total": quantity, "remaining": quantity}
                else:
                    inventory[item] = {"total": "1", "remaining": "1"}
            except:
                inventory[item] = {"total": "1", "remaining": "1"}
        else:
            inventory[item] = {"total": "1", "remaining": "1"}
    
    return inventory

# Function to call AI
@st.cache_data
def get_food_plan(items, people=None, days=7):  # Default to 7 days
    # Use local Ollama or remote API
    api_url = "http://localhost:11434/api/generate"
    
    # Format the prompt for better output structure
    prompt = "You are an emergency food planner. Create a detailed plan for the following ingredients:\n\n"
    prompt += items + "\n\n"
    
    if people and days:
        # Fixed string formatting issue
        people_str = ", ".join([f"{p['type']} (age {p['age']})" for p in people])
        prompt += f"This needs to feed {len(people)} people ({people_str}) "
        prompt += f"for {days} days in an emergency situation.\n\n"
    else:
        prompt += f"Create a 7-day food plan that maximizes these ingredients.\n\n"
    
    prompt += """
Format your response in this JSON structure:
{
  "analysis": "Brief analysis of the food inventory and nutritional content",
  "preservation_tips": ["tip1", "tip2", "tip3"],
  "daily_plans": [
    {
      "day": 1,
      "meals": [
        {
          "name": "Breakfast - Recipe Name",
          "recipe": "Detailed step-by-step instructions",
          "ingredients_used": ["item1: amount", "item2: amount"],
          "image_keyword": "simple keyword for the meal image"
        },
        {
          "name": "Lunch - Recipe Name",
          "recipe": "Detailed step-by-step instructions",
          "ingredients_used": ["item1: amount", "item2: amount"],
          "image_keyword": "simple keyword for the meal image"
        },
        {
          "name": "Dinner - Recipe Name",
          "recipe": "Detailed step-by-step instructions",
          "ingredients_used": ["item1: amount", "item2: amount"],
          "image_keyword": "simple keyword for the meal image"
        }
      ],
      "remaining_inventory": ["item1: amount remaining out of total", "item2: amount remaining out of total"]
    }
    // Include at least 7 days of planning
  ]
}
"""
    
    try:
        # For demo/testing, you can return mock data if the API isn't working
        if api_url.startswith("http://localhost"):
            try:
                # Try real API first
                payload = {
                    "model": "llama3",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
                response = requests.post(api_url, json=payload, timeout=30)
                response_data = response.json()
                result = response_data.get("response", "")
                
                # Extract JSON from the response
                try:
                    # Find JSON in the response if it's embedded in text
                    start_idx = result.find('{')
                    end_idx = result.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = result[start_idx:end_idx]
                        return json.loads(json_str)
                    return json.loads(result)
                except json.JSONDecodeError:
                    # If real API fails, fall back to mock data
                    pass
            except Exception as e:
                st.warning(f"API connection issue: {str(e)}. Using mock data for demonstration.")
            
            # Mock data for demonstration/development when API isn't available
            inventory = parse_inventory(items)
            return generate_mock_data(inventory, days or 7)
    except Exception as e:
        return {"error": str(e)}

def generate_mock_data(inventory, days):
    """Generate mock data for demonstration when API isn't available"""
    # Parse inventory and track usage
    remaining_inventory = {k: v.copy() for k, v in inventory.items()}
    
    mock_data = {
        "analysis": f"Your food inventory contains {len(inventory)} items including starches, proteins, and some fresh produce. This plan maximizes shelf-stable items first while using perishables early in the plan.",
        "preservation_tips": [
            "Store rice in airtight containers to prevent bugs",
            "Freeze bread to extend shelf life",
            "Use milk early or make yogurt/cheese to preserve"
        ],
        "daily_plans": []
    }
    
    meal_types = {
        "Breakfast": ["Oatmeal", "Cereal", "Toast", "Pancakes", "Rice Porridge"],
        "Lunch": ["Sandwich", "Rice Bowl", "Soup", "Stir Fry", "Pasta"],
        "Dinner": ["Casserole", "Curry", "Roasted Vegetables", "Stew", "Rice and Beans"]
    }
    
    # Helper function to use ingredients and track remaining amounts
    def use_ingredient(inventory_dict, ingredient_name, amount_used=0.25):
        # Mock tracking of ingredient usage
        if ingredient_name in inventory_dict:
            # Simulate using some amount of the ingredient
            item = inventory_dict[ingredient_name]
            total = item["total"]
            
            # Extract numeric part if present
            num_part = ''.join(filter(lambda x: x.isdigit() or x == '.', total))
            if num_part:
                try:
                    total_num = float(num_part)
                    used = min(total_num * amount_used, total_num)
                    remaining = total_num - used
                    
                    # Update remaining amount
                    unit = ''.join(filter(lambda x: not (x.isdigit() or x == '.'), total))
                    item["remaining"] = f"{remaining}{unit}"
                    
                    # Format used amount
                    return f"{used}{unit} of {total}{unit}"
                except:
                    return "portion"
            
            return "portion"
        return "portion"
    
    # Generate unique meal plans for each day
    for day in range(1, days+1):
        day_plan = {
            "day": day,
            "meals": [],
            "remaining_inventory": []
        }
        
        # Available inventory for this day (items with remaining > 0)
        available_items = [k for k, v in remaining_inventory.items()]
        
        for meal_time in ["Breakfast", "Lunch", "Dinner"]:
            meal_base = random.choice(meal_types[meal_time])
            
            # Use some random ingredients from our list without duplicates
            used_items = []
            used_ingredients = set()
            meal_ingredients = []
            
            # Try to use 2-3 unique ingredients per meal
            for _ in range(min(3, len(available_items))):
                if available_items:
                    # Choose a random ingredient not already used in this meal
                    available_unused = [i for i in available_items if i not in used_ingredients]
                    if not available_unused:
                        break
                        
                    item = random.choice(available_unused)
                    used_ingredients.add(item)
                    
                    # Track usage
                    usage = use_ingredient(remaining_inventory, item)
                    meal_ingredients.append(f"{item}: {usage}")
            
            meal = {
                "name": f"{meal_time} - {meal_base}",
                "recipe": f"Step 1: Prepare the {meal_base} by combining ingredients.\nStep 2: Cook until done.\nStep 3: Serve warm.",
                "ingredients_used": meal_ingredients,
                "image_keyword": meal_base.lower()
            }
            day_plan["meals"].append(meal)
        
        # Update remaining inventory
        day_plan["remaining_inventory"] = [
            f"{k}: {v['remaining']} of {v['total']}" 
            for k, v in remaining_inventory.items()
        ]
        
        mock_data["daily_plans"].append(day_plan)
    
    return mock_data

# Create meal cards with images
def create_meal_card(meal):
    cols = st.columns([1, 2])
    
    with cols[0]:
        # Get image based on meal name or keyword
        image_keyword = meal.get("image_keyword", meal["name"].split("-")[1].strip())
        image_url = get_food_image_url(image_keyword)
        st.image(image_url, caption=meal["name"])
    
    with cols[1]:
        # Recipe and ingredients
        st.markdown(f"**{meal['name']}**")
        st.markdown("**Ingredients:**")
        for ingredient in meal["ingredients_used"]:
            st.markdown(f"• {ingredient}")
        
        with st.expander("Cooking Instructions"):
            st.write(meal["recipe"])

# Create detailed image for downloading
def create_detailed_plan_image(plan_data):
    days = len(plan_data["daily_plans"])
    # Make the image taller to accommodate all days
    fig = plt.figure(figsize=(12, max(10, days*4 + 3)))
    
    # Title and analysis
    plt.suptitle("Emergency Food Plan", fontsize=20)
    plt.figtext(0.05, 0.97, plan_data["analysis"], wrap=True, fontsize=10)
    
    # Add preservation tips
    tip_text = "Preservation Tips:\n" + "\n".join([f"• {tip}" for tip in plan_data["preservation_tips"]])
    plt.figtext(0.05, 0.93, tip_text, wrap=True, fontsize=8)
    
    # Create a grid for days
    current_date = datetime.now()
    
    for i, day_plan in enumerate(plan_data["daily_plans"]):
        day_date = current_date + timedelta(days=i)
        day_str = day_date.strftime("%A, %b %d")
        
        # Add day header
        y_pos = 0.89 - (i * (0.85/days))
        plt.figtext(0.05, y_pos, f"Day {day_plan['day']} ({day_str})", fontsize=12, weight='bold')
        
        # Add meals with more details and formatting
        y_offset = 0.02
        for meal in day_plan["meals"]:
            meal_title = meal["name"]
            # Format recipe in a condensed way
            recipe_text = meal["recipe"].replace("\n", " ")
            if len(recipe_text) > 100:
                recipe_text = recipe_text[:97] + "..."
                
            ingredients = ", ".join(meal["ingredients_used"])
            
            meal_text = f"{meal_title}\n" 
            meal_text += f"Ingredients: {ingredients}\n"
            meal_text += f"Instructions: {recipe_text}"
            
            plt.figtext(0.07, y_pos-y_offset, meal_text, wrap=True, fontsize=8)
            y_offset += 0.06
        
        # Add remaining inventory
        remaining_text = "Remaining Inventory:\n" + "\n".join(day_plan["remaining_inventory"][:8])
        if len(day_plan["remaining_inventory"]) > 8:
            remaining_text += "\n..."
            
        plt.figtext(0.75, y_pos, remaining_text, fontsize=7, 
                  bbox=dict(facecolor='white', alpha=0.5, boxstyle='round,pad=0.5'))
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

# Main app logic
if st.button("Generate Plan"):
    if not food_items:
        st.error("Please enter your food items")
    else:
        with st.spinner("Generating your emergency food plan..."):
            # Convert the text area input to a list
            items_list = food_items.strip().split('\n')
            
            # Call the AI with default 7 days if not specified
            if use_optional:
                plan_data = get_food_plan(food_items, people_data, days)
            else:
                plan_data = get_food_plan(food_items)
                
            if isinstance(plan_data, dict) and "error" in plan_data:
                st.error(f"Error: {plan_data['error']}")
                if "raw_response" in plan_data:
                    st.text(plan_data["raw_response"])
            else:
                # Display the plan
                st.subheader("Your Emergency Food Plan")
                
                # Analysis
                st.write(plan_data["analysis"])
                
                # Tips
                with st.expander("Preservation Tips"):
                    for tip in plan_data["preservation_tips"]:
                        st.write(f"• {tip}")
                
                # Day navigation tabs
                day_tabs = st.tabs([f"Day {day['day']}" for day in plan_data["daily_plans"]])
                
                for i, day_tab in enumerate(day_tabs):
                    with day_tab:
                        day_plan = plan_data["daily_plans"][i]
                        st.subheader(f"Day {day_plan['day']} - {(datetime.now() + timedelta(days=i)).strftime('%A, %b %d')}")
                        
                        # Display meals with images
                        for meal in day_plan["meals"]:
                            st.markdown("---")
                            create_meal_card(meal)
                        
                        # Remaining inventory
                        st.markdown("---")
                        st.subheader("Remaining Inventory")
                        cols = st.columns(3)
                        for j, item in enumerate(day_plan["remaining_inventory"]):
                            cols[j % 3].markdown(f"• {item}")
                
                # Generate and display the downloadable image
                image_buf = create_detailed_plan_image(plan_data)
                
                # Download button
                st.download_button(
                    label="Download Complete Plan as Image",
                    data=image_buf,
                    file_name="emergency_food_plan.png",
                    mime="image/png"
                )
                
                # Show a preview of the downloadable image
                st.subheader("Plan Overview (Preview)")
                st.image(image_buf, use_column_width=True)