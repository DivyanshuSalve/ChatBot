import streamlit as st
import google.generativeai as genai
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

# Page configuration
st.set_page_config(
    page_title="Alchemy Chemicals - AI Quotation Assistant",
    page_icon="🧪",
    layout="wide"
)

# Initialize Gemini API (user will need to add their API key)
# You can set this as an environment variable or directly here for the demo
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None) or st.sidebar.text_input("Gemini API Key", type="password")

model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

# Product pricing data structure
PRODUCTS = {
    "ashwagandha": {
        "name": "Ashwagandha Extract",
        "unit": "Withanolides",
        "specifications": {
            "2.5%": {"base_price": 1800, "moq": 25},
            "5%": {"base_price": 2800, "moq": 25},
            "10%": {"base_price": 3600, "moq": 20}
        }
    },
    "boswellia": {
        "name": "Boswellia Extract",
        "unit": "Boswellic Acid",
        "specifications": {
            "65%": {"base_price": 2200, "moq": 25},
            "85%": {"base_price": 3200, "moq": 20}
        }
    },
    "curcumin": {
        "name": "Curcumin Extract",
        "unit": "Purity",
        "specifications": {
            "90%": {"base_price": 2500, "moq": 25},
            "95%": {"base_price": 3000, "moq": 25},
            "98%": {"base_price": 3800, "moq": 20}
        }
    },
    "neem": {
        "name": "Neem Extract",
        "unit": "Azadirachtin",
        "specifications": {
            "1%": {"base_price": 1500, "moq": 30},
            "5%": {"base_price": 2600, "moq": 25}
        }
    },
    "tulsi": {
        "name": "Tulsi Extract",
        "unit": "Ursolic Acid",
        "specifications": {
            "2%": {"base_price": 1700, "moq": 30},
            "5%": {"base_price": 2400, "moq": 25}
        }
    }
}

# Volume discount tiers
VOLUME_DISCOUNTS = {
    (1, 24): 0,
    (25, 99): 10,
    (100, 499): 15,
    (500, float('inf')): 20
}

# Grade premiums
GRADE_PREMIUMS = {
    "pharmaceutical": 20,
    "pharma": 20,
    "cosmetic": 10,
    "food": 0,
    "food grade": 0
}

# Delivery costs
DELIVERY_COSTS = {
    "mumbai": 3500,
    "delhi": 4200,
    "bangalore": 4800,
    "bengaluru": 4800,
    "pune": 3200,
    "ujjain": 1000,
    "local": 1000
}

GST_RATE = 0.18

def parse_query_with_ai(query: str) -> Dict:
    """Use Gemini AI to parse natural language query into structured data"""
    
    if not model:
        return parse_query_simple(query)
    
    prompt = f"""Parse this herbal extract quotation request and extract the following information:
    - Product name (ashwagandha/boswellia/curcumin/neem/tulsi)
    - Specification/concentration (e.g., 5%, 10%)
    - Quantity in kg
    - Grade (pharmaceutical/cosmetic/food)
    - Delivery city

    Query: "{query}"

    Return ONLY a JSON object with keys: product, specification, quantity, grade, city
    If any field is missing, set it as null.
    Do not include any explanatory text, only the JSON.
    """
    
    try:
        response = model.generate_content(prompt)
        result = response.text
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        # Silently fall back to regex parser - no need to show error
        pass
    
    # Fallback to simple regex parsing
    return parse_query_simple(query)

def parse_query_simple(query: str) -> Dict:
    """Fallback simple parser using regex"""
    query_lower = query.lower()
    
    result = {
        "product": None,
        "specification": None,
        "quantity": None,
        "grade": None,
        "city": None
    }
    
    # Find product
    for product_key in PRODUCTS:
        if product_key in query_lower:
            result["product"] = product_key
            break
    
    # Find quantity (number followed by kg)
    qty_match = re.search(r'(\d+)\s*kg', query_lower)
    if qty_match:
        result["quantity"] = int(qty_match.group(1))
    
    # Find specification (percentage)
    spec_match = re.findall(r'(\d+(?:\.\d+)?)\s*%', query_lower)
    if spec_match:
        result["specification"] = f"{spec_match[0]}%"
    
    # Find grade
    for grade in GRADE_PREMIUMS:
        if grade in query_lower:
            result["grade"] = grade
            break
    
    # Find city
    for city in DELIVERY_COSTS:
        if city in query_lower:
            result["city"] = city
            break
    
    return result

def get_volume_discount(quantity: int) -> Tuple[int, str]:
    """Calculate volume discount based on quantity"""
    for (min_qty, max_qty), discount in VOLUME_DISCOUNTS.items():
        if min_qty <= quantity <= max_qty:
            return discount, f"{min_qty}-{max_qty}kg" if max_qty != float('inf') else f"{min_qty}+kg"
    return 0, "No discount"

def calculate_quotation(product: str, specification: str, quantity: int, grade: str, city: str) -> Dict:
    """Calculate complete quotation with all pricing components"""
    
    # Get product details
    product_info = PRODUCTS[product]
    spec_info = product_info["specifications"][specification]
    
    base_price = spec_info["base_price"]
    moq = spec_info["moq"]
    
    # Check MOQ
    if quantity < moq:
        return {"error": f"Minimum order quantity is {moq}kg for this product"}
    
    # Calculate base total
    subtotal = base_price * quantity
    
    # Apply volume discount
    volume_discount_pct, volume_tier = get_volume_discount(quantity)
    volume_discount_amt = subtotal * (volume_discount_pct / 100)
    
    # Apply grade premium
    grade_premium_pct = GRADE_PREMIUMS.get(grade.lower(), 0)
    grade_premium_amt = subtotal * (grade_premium_pct / 100)
    
    # Add delivery cost
    delivery_cost = DELIVERY_COSTS.get(city.lower(), 0)
    
    # Calculate subtotal before GST
    subtotal_before_gst = subtotal - volume_discount_amt + grade_premium_amt + delivery_cost
    
    # Calculate GST
    gst_amount = subtotal_before_gst * GST_RATE
    
    # Final total
    total = subtotal_before_gst + gst_amount
    
    return {
        "product_name": product_info["name"],
        "specification": f"{specification} {product_info['unit']}",
        "grade": grade.title(),
        "quantity": quantity,
        "base_price": base_price,
        "subtotal": subtotal,
        "volume_discount_pct": volume_discount_pct,
        "volume_tier": volume_tier,
        "volume_discount_amt": volume_discount_amt,
        "grade_premium_pct": grade_premium_pct,
        "grade_premium_amt": grade_premium_amt,
        "delivery_city": city.title(),
        "delivery_cost": delivery_cost,
        "subtotal_before_gst": subtotal_before_gst,
        "gst_amount": gst_amount,
        "total": total,
        "moq": moq,
        "lead_time": "2-3 days",
        "validity": (datetime.now() + timedelta(days=7)).strftime("%d %b %Y")
    }

def format_quotation(quote: Dict) -> str:
    """Format quotation in professional format"""
    
    if "error" in quote:
        return f"❌ {quote['error']}"
    
    formatted = f"""
**ALCHEMY CHEMICALS - QUOTATION**
---
**Product:** {quote['product_name']}
**Specification:** {quote['specification']}
**Grade:** {quote['grade']}
**Quantity:** {quote['quantity']}kg

**Pricing Breakdown:**
- Base Price: ₹{quote['base_price']:,}/kg
- Subtotal: ₹{quote['subtotal']:,}
- Volume Discount ({quote['volume_tier']} tier): -{quote['volume_discount_pct']}% = -₹{quote['volume_discount_amt']:,}
- Grade Premium ({quote['grade']}): +{quote['grade_premium_pct']}% = +₹{quote['grade_premium_amt']:,}
- Delivery ({quote['delivery_city']}): ₹{quote['delivery_cost']:,}
- **Subtotal:** ₹{quote['subtotal_before_gst']:,}
- GST (18%): ₹{quote['gst_amount']:,.0f}

**TOTAL: ₹{quote['total']:,.0f}**

**Terms & Conditions:**
- MOQ: {quote['moq']}kg
- Lead Time: {quote['lead_time']}
- Quote Validity: Until {quote['validity']}
- Certifications: ISO 9001:2015, GMP, FDA

**For order confirmation:** info@alchemychemicals.net
"""
    return formatted

def is_greeting_or_general(query: str) -> Optional[str]:
    """Detect greetings and general queries, return friendly response"""
    query_lower = query.lower().strip()
    
    # Greetings
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'namaste']
    if any(greeting in query_lower for greeting in greetings):
        return """Hello! 👋 Welcome to Alchemy Chemicals!

I'm your AI quotation assistant. I can help you get instant price quotes for our premium herbal extracts.

**Our Products:**
🌿 Ashwagandha Extract (2.5%, 5%, 10% withanolides)
🌿 Boswellia Extract (65%, 85% boswellic acid)
🌿 Curcumin Extract (90%, 95%, 98% purity)
🌿 Neem Extract (1%, 5% azadirachtin)
🌿 Tulsi Extract (2%, 5% ursolic acid)

**Try asking me something like:**
• "Price for 50kg Ashwagandha 5% pharmaceutical grade, Mumbai delivery"
• "I need 100kg Curcumin 95% for cosmetic use, Delhi"
• "Quote for Boswellia extract"

How can I help you today? 😊"""
    
    # Help queries
    help_terms = ['help', 'how to use', 'what can you do', 'how does this work']
    if any(term in query_lower for term in help_terms):
        return """I'm here to help! 🤝

**How to get a quotation:**
Just tell me what you need in plain English. Include:
1. Product name (e.g., Ashwagandha, Curcumin)
2. Specification (e.g., 5% withanolides, 95% purity)
3. Quantity in kg
4. Grade (pharmaceutical/cosmetic/food)
5. Delivery city

**Example:**
"I need 50kg of Ashwagandha extract 5% withanolides, pharmaceutical grade, delivery to Mumbai"

Don't worry about perfect formatting - I understand natural language! Try asking now. 💬"""
    
    # Thank you
    thank_terms = ['thank', 'thanks', 'appreciate']
    if any(term in query_lower for term in thank_terms):
        return """You're very welcome! 😊

Is there anything else you'd like to know?
• Need a quote for a different product?
• Want to compare different specifications?
• Questions about pricing or delivery?

I'm here to help!"""
    
    # Product inquiry without details
    products_mentioned = [p for p in PRODUCTS.keys() if p in query_lower]
    if products_mentioned and len(query_lower.split()) < 8:  # Short query
        product = products_mentioned[0]
        product_info = PRODUCTS[product]
        specs = list(product_info["specifications"].keys())
        
        return f"""Great choice! I can help you with **{product_info['name']}**. 🌿

**Available specifications:**
{chr(10).join([f'• {spec} {product_info["unit"]}' for spec in specs])}

**To get a quotation, please tell me:**
1. Which specification? ({', '.join(specs)})
2. How many kg do you need?
3. Grade: pharmaceutical/cosmetic/food?
4. Delivery city: Mumbai/Delhi/Bangalore/Pune/local?

**Example:**
"I need 50kg of {product_info['name']} {specs[0]} {product_info['unit']}, pharmaceutical grade, Mumbai delivery"

What would you like? 😊"""
    
    return None

def handle_missing_info(parsed_data: Dict) -> Optional[str]:
    """Check for missing information and prompt user in a friendly way"""
    missing = []
    suggestions = []
    
    if not parsed_data.get("product"):
        missing.append("**Product name**")
        suggestions.append("Which product? (Ashwagandha/Boswellia/Curcumin/Neem/Tulsi)")
    
    if parsed_data.get("product") and not parsed_data.get("specification"):
        product = parsed_data["product"]
        if product in PRODUCTS:
            specs = list(PRODUCTS[product]["specifications"].keys())
            missing.append("**Specification**")
            suggestions.append(f"Which concentration? ({'/'.join(specs)})")
    
    if not parsed_data.get("quantity"):
        missing.append("**Quantity**")
        suggestions.append("How many kg do you need?")
    
    if not parsed_data.get("grade"):
        missing.append("**Grade**")
        suggestions.append("Which grade? (Pharmaceutical/Cosmetic/Food)")
    
    if not parsed_data.get("city"):
        missing.append("**Delivery city**")
        suggestions.append("Where should we deliver? (Mumbai/Delhi/Bangalore/Pune/Ujjain)")
    
    if missing:
        return f"""I'd love to help! 😊 I just need a bit more information:

{chr(10).join([f'{i+1}. {sugg}' for i, sugg in enumerate(suggestions)])}

**Or try this format:**
"[Quantity]kg [Product] [Spec]%, [Grade] grade, [City] delivery"

What else can you tell me?"""
    
    return None

# Streamlit UI
st.title("🧪 Alchemy Chemicals - AI Quotation Assistant")
st.markdown("Get instant quotations for premium herbal extracts")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add welcome message
    welcome_msg = """👋 **Welcome to Alchemy Chemicals!**

I'm your AI quotation assistant, ready to help you get instant price quotes for premium herbal extracts.

**Just type naturally!** Try:
• "Hi" - to see what I can do
• "Price for 50kg Ashwagandha" - to get started
• "Help" - for more guidance

Looking forward to assisting you! 😊"""
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# Sidebar with product catalog
with st.sidebar:
    st.header("📋 Product Catalog")
    
    for product_key, product_info in PRODUCTS.items():
        with st.expander(f"🌿 {product_info['name']}"):
            for spec, details in product_info["specifications"].items():
                st.write(f"• {spec} {product_info['unit']}: ₹{details['base_price']:,}/kg")
                st.write(f"  MOQ: {details['moq']}kg")
    
    st.divider()
    st.header("💰 Pricing Structure")
    st.write("**Volume Discounts:**")
    st.write("• 1-24kg: 0%")
    st.write("• 25-99kg: 10%")
    st.write("• 100-499kg: 15%")
    st.write("• 500+kg: 20%")
    
    st.write("\n**Grade Premiums:**")
    st.write("• Pharmaceutical: +20%")
    st.write("• Cosmetic: +10%")
    st.write("• Food Grade: 0%")

# Main chat interface
st.markdown("### 💬 Chat with our AI Assistant")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask for a quotation (e.g., 'Price for 50kg Ashwagandha extract 5% withanolides, pharmaceutical grade, delivery to Mumbai')"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process query
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Check if it's a greeting or general query first
            greeting_response = is_greeting_or_general(prompt)
            
            if greeting_response:
                st.markdown(greeting_response)
                st.session_state.messages.append({"role": "assistant", "content": greeting_response})
            else:
                # Parse the query for quotation
                if GEMINI_API_KEY:
                    parsed_data = parse_query_with_ai(prompt)
                else:
                    parsed_data = parse_query_simple(prompt)
                
                # Check for missing info
                missing_info_msg = handle_missing_info(parsed_data)
                
                if missing_info_msg:
                    st.info(missing_info_msg)
                    st.session_state.messages.append({"role": "assistant", "content": missing_info_msg})
                else:
                    # All info available, calculate quotation
                    try:
                        quotation = calculate_quotation(
                            parsed_data["product"],
                            parsed_data["specification"],
                            parsed_data["quantity"],
                            parsed_data["grade"],
                            parsed_data["city"]
                        )
                        
                        formatted_quote = format_quotation(quotation)
                        st.markdown(formatted_quote)
                        
                        # Add to history
                        st.session_state.messages.append({"role": "assistant", "content": formatted_quote})
                        
                        # Add download button for quotation
                        if "error" not in quotation:
                            st.download_button(
                                label="📥 Download Quotation",
                                data=formatted_quote,
                                file_name=f"quotation_{parsed_data['product']}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                                mime="text/plain"
                            )
                            
                            # Add friendly follow-up
                            follow_up = "\n\n---\n\n💡 **Need something else?**\n• Modify quantity or specification?\n• Get a quote for another product?\n• Compare different options?\n\nJust ask!"
                            st.markdown(follow_up)
                            
                    except Exception as e:
                        error_msg = f"Oops! Something went wrong: {str(e)}\n\nPlease try again or rephrase your request. I'm here to help! 😊"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Example queries section
with st.expander("📝 Example Queries"):
    st.markdown("""
    Try these example queries:
    1. "Price for 50kg Ashwagandha extract 5% withanolides, pharmaceutical grade, delivery to Mumbai"
    2. "I need 100kg of Curcumin 95% purity for cosmetic use, deliver to Delhi"
    3. "Quote for 200kg Boswellia extract 85% boswellic acid, pharma grade, Bangalore delivery"
    4. "25kg Neem extract 5% azadirachtin, food grade, ship to Pune"
    5. "Tulsi extract 5% ursolic acid, 75kg, pharmaceutical grade, local delivery"
    """)
