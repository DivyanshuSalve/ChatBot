import streamlit as st
import google.generativeai as genai
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from difflib import get_close_matches

# Page configuration
st.set_page_config(
    page_title="Alchemy Chemicals - AI Quotation Assistant",
    page_icon="🧪",
    layout="wide"
)

# Initialize Gemini API
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)
except:
    GEMINI_API_KEY = None

if not GEMINI_API_KEY:
    GEMINI_API_KEY = st.sidebar.text_input("Gemini API Key (optional - uses smart parser if empty)", type="password")

model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        st.sidebar.success("✅ Gemini AI Active")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Gemini error: Using smart parser")
        model = None
else:
    st.sidebar.info("ℹ️ Using smart parser mode")

# Product pricing data structure
PRODUCTS = {
    "ashwagandha": {
        "name": "Ashwagandha Extract",
        "unit": "Withanolides",
        "aliases": ["ashwaganda", "ashvagandha", "ashwagandah"],
        "specifications": {
            "2.5%": {"base_price": 1800, "moq": 25},
            "5%": {"base_price": 2800, "moq": 25},
            "10%": {"base_price": 3600, "moq": 20}
        }
    },
    "boswellia": {
        "name": "Boswellia Extract",
        "unit": "Boswellic Acid",
        "aliases": ["boswelia", "boswella"],
        "specifications": {
            "65%": {"base_price": 2200, "moq": 25},
            "85%": {"base_price": 3200, "moq": 20}
        }
    },
    "curcumin": {
        "name": "Curcumin Extract",
        "unit": "Purity",
        "aliases": ["curcumine", "turmeric", "haldi"],
        "specifications": {
            "90%": {"base_price": 2500, "moq": 25},
            "95%": {"base_price": 3000, "moq": 25},
            "98%": {"base_price": 3800, "moq": 20}
        }
    },
    "neem": {
        "name": "Neem Extract",
        "unit": "Azadirachtin",
        "aliases": ["nim", "neam"],
        "specifications": {
            "1%": {"base_price": 1500, "moq": 30},
            "5%": {"base_price": 2600, "moq": 25}
        }
    },
    "tulsi": {
        "name": "Tulsi Extract",
        "unit": "Ursolic Acid",
        "aliases": ["tulasi", "basil", "holy basil"],
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

# Grade premiums with aliases
GRADE_PREMIUMS = {
    "pharmaceutical": {"premium": 20, "aliases": ["pharma", "medical", "pharmceutical"]},
    "cosmetic": {"premium": 10, "aliases": ["cosmetics", "beauty", "cometic", "cosmatic"]},
    "food": {"premium": 0, "aliases": ["food grade", "edible", "dietary"]}
}

# Delivery costs with aliases
DELIVERY_COSTS = {
    "mumbai": {"cost": 3500, "aliases": ["bombay", "mumbay"]},
    "delhi": {"cost": 4200, "aliases": ["new delhi", "dilli"]},
    "bangalore": {"cost": 4800, "aliases": ["bengaluru", "banglore", "bangaluru"]},
    "pune": {"cost": 3200, "aliases": ["poona"]},
    "ujjain": {"cost": 1000, "aliases": ["ujain"]},
    "local": {"cost": 1000, "aliases": ["locally", "pickup"]}
}

GST_RATE = 0.18

def find_best_match(text: str, options: Dict, check_aliases: bool = True) -> Optional[str]:
    """Find the best match for a given text in options, considering aliases and typos"""
    text_lower = text.lower().strip()
    
    # First check exact matches
    for key in options:
        if key in text_lower or text_lower in key:
            return key
    
    # Then check aliases if available
    if check_aliases:
        for key, value in options.items():
            if isinstance(value, dict) and "aliases" in value:
                for alias in value["aliases"]:
                    if alias in text_lower or text_lower in alias:
                        return key
    
    # Finally, use fuzzy matching for typos
    all_options = list(options.keys())
    if check_aliases:
        for value in options.values():
            if isinstance(value, dict) and "aliases" in value:
                all_options.extend(value["aliases"])
    
    matches = get_close_matches(text_lower, all_options, n=1, cutoff=0.7)
    if matches:
        # Find which key this match belongs to
        for key, value in options.items():
            if matches[0] == key:
                return key
            if isinstance(value, dict) and "aliases" in value:
                if matches[0] in value["aliases"]:
                    return key
    
    return None

def extract_all_info(text: str, context: Dict) -> Dict:
    """Extract all possible information from user input, handling compound statements"""
    text_lower = text.lower()
    result = context.copy()
    
    # Extract product
    product_found = find_best_match(text, PRODUCTS, check_aliases=True)
    if product_found:
        result["product"] = product_found
    
    # Extract quantity (with various formats)
    qty_patterns = [
        r'(\d+)\s*kg',
        r'(\d+)\s*kgs',
        r'(\d+)\s*kilogram',
        r'(\d+)\s*kilos',
        r'for\s+(\d+)',
        r'need\s+(\d+)',
        r'want\s+(\d+)'
    ]
    for pattern in qty_patterns:
        match = re.search(pattern, text_lower)
        if match:
            result["quantity"] = int(match.group(1))
            break
    
    # If just a number is provided and we need quantity
    if not result.get("quantity") and re.match(r'^\d+$', text.strip()):
        result["quantity"] = int(text.strip())
    
    # Extract specification
    spec_patterns = [
        r'(\d+(?:\.\d+)?)\s*%',
        r'(\d+(?:\.\d+)?)\s*percent',
        r'(\d+(?:\.\d+)?)\s*concentration'
    ]
    for pattern in spec_patterns:
        match = re.search(pattern, text_lower)
        if match:
            spec_value = f"{match.group(1)}%"
            # Validate against product specifications if product is known
            if result.get("product") and result["product"] in PRODUCTS:
                if spec_value in PRODUCTS[result["product"]]["specifications"]:
                    result["specification"] = spec_value
                else:
                    # Find closest valid specification
                    specs = list(PRODUCTS[result["product"]]["specifications"].keys())
                    for spec in specs:
                        if spec.replace("%", "") == match.group(1):
                            result["specification"] = spec
                            break
            else:
                result["specification"] = spec_value
            break
    
    # Extract grade
    for grade_key, grade_info in GRADE_PREMIUMS.items():
        if grade_key in text_lower:
            result["grade"] = grade_key
            break
        for alias in grade_info["aliases"]:
            if alias in text_lower:
                result["grade"] = grade_key
                break
    
    # Extract city
    for city_key, city_info in DELIVERY_COSTS.items():
        # Check for patterns like "in Mumbai", "to Delhi", "at Pune"
        city_patterns = [
            rf'\b(?:in|to|at|for|deliver to|delivery to|ship to)\s+{city_key}\b',
            rf'\b{city_key}\b\s*(?:delivery|deliver|ship)',
            rf'\b{city_key}\b'
        ]
        
        for pattern in city_patterns:
            if re.search(pattern, text_lower):
                result["city"] = city_key
                break
        
        if result.get("city"):
            break
            
        # Check aliases
        for alias in city_info["aliases"]:
            for pattern in city_patterns:
                pattern_alias = pattern.replace(city_key, alias)
                if re.search(pattern_alias, text_lower):
                    result["city"] = city_key
                    break
            if result.get("city"):
                break
    
    return result

def parse_with_ai(query: str, context: Dict) -> Dict:
    """Use Gemini AI for intelligent parsing with context awareness"""
    if not model:
        return extract_all_info(query, context)
    
    context_str = json.dumps({k: v for k, v in context.items() if v}, indent=2)
    
    prompt = f"""You are helping process an order for herbal extracts. Parse the user's message and extract/update order information.

Current order context:
{context_str if context_str != '{{}}' else 'No previous information'}

User message: "{query}"

Extract and return a JSON with these fields (keep existing values if not mentioned in new message):
- product: ashwagandha/boswellia/curcumin/neem/tulsi (handle typos/variations)
- specification: percentage like "2.5%", "5%", "10%" etc
- quantity: number in kg
- grade: pharmaceutical/cosmetic/food (handle variations like "pharma", "cometic")
- city: mumbai/delhi/bangalore/pune/ujjain/local (handle variations)

Important:
- If user mentions a product but you already have different info, UPDATE to the new product
- Handle spelling mistakes (e.g., "cometic" = "cosmetic", "delli" = "delhi")
- Extract ALL information from compound sentences
- Keep previous context values if not explicitly changed
- Return ONLY the JSON object, no explanations"""
    
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            # Merge with context
            merged = context.copy()
            for key, value in parsed.items():
                if value:
                    merged[key] = value
            return merged
    except:
        pass
    
    # Fallback to smart parser
    return extract_all_info(query, context)

def is_greeting(text: str) -> bool:
    """Check if text is a greeting using word boundaries"""
    greetings = ['hi', 'hello', 'hey', 'namaste', 'good morning', 'good afternoon', 'good evening']
    text_lower = text.lower().strip()
    
    for greeting in greetings:
        # Check for exact match or word boundary match
        if text_lower == greeting or re.match(rf'^{greeting}\b', text_lower) or re.match(rf'\b{greeting}$', text_lower):
            return True
    return False

def generate_response(parsed_data: Dict) -> str:
    """Generate intelligent conversational response based on what's missing"""
    missing = []
    has_info = []
    
    # Track what we have and what we need
    for field in ["product", "specification", "quantity", "grade", "city"]:
        if parsed_data.get(field):
            has_info.append(field)
        else:
            missing.append(field)
    
    # If we have everything, return None (will generate quotation)
    if not missing:
        return None
    
    # Build contextual response
    response_parts = []
    
    # Acknowledge what we have
    if has_info:
        ack_parts = []
        if parsed_data.get("product"):
            product_name = PRODUCTS[parsed_data["product"]]["name"]
            ack_parts.append(f"**{product_name}**")
        if parsed_data.get("specification"):
            ack_parts.append(f"**{parsed_data['specification']}**")
        if parsed_data.get("quantity"):
            ack_parts.append(f"**{parsed_data['quantity']}kg**")
        if parsed_data.get("grade"):
            ack_parts.append(f"**{parsed_data['grade'].title()} grade**")
        if parsed_data.get("city"):
            ack_parts.append(f"**delivery to {parsed_data['city'].title()}**")
        
        if ack_parts:
            response_parts.append(f"Great! I have: {', '.join(ack_parts)} ✅")
    
    # Ask for missing information naturally
    response_parts.append("\nI just need:")
    
    questions = []
    if not parsed_data.get("product"):
        questions.append("• Which product? (Ashwagandha/Boswellia/Curcumin/Neem/Tulsi)")
    elif not parsed_data.get("specification"):
        product = parsed_data["product"]
        specs = list(PRODUCTS[product]["specifications"].keys())
        questions.append(f"• Which concentration? ({'/'.join(specs)})")
    
    if not parsed_data.get("quantity"):
        questions.append("• How many kg?")
    
    if not parsed_data.get("grade"):
        questions.append("• Which grade? (Pharmaceutical/Cosmetic/Food)")
    
    if not parsed_data.get("city"):
        questions.append("• Delivery location? (Mumbai/Delhi/Bangalore/Pune/Local)")
    
    response_parts.extend(questions)
    
    # Add helpful tip
    response_parts.append("\n💡 **Tip:** You can tell me everything at once like:")
    response_parts.append(f"*\"{75 if not parsed_data.get('quantity') else parsed_data['quantity']}kg {parsed_data.get('product', 'Ashwagandha')} {parsed_data.get('specification', '5%') if parsed_data.get('product') else '5%'}, {parsed_data.get('grade', 'pharmaceutical') if not parsed_data.get('grade') else parsed_data['grade']} grade, {parsed_data.get('city', 'Mumbai') if not parsed_data.get('city') else parsed_data['city']} delivery\"*")
    
    return "\n".join(response_parts)

def get_volume_discount(quantity: int) -> Tuple[int, str]:
    """Calculate volume discount based on quantity"""
    for (min_qty, max_qty), discount in VOLUME_DISCOUNTS.items():
        if min_qty <= quantity <= max_qty:
            return discount, f"{min_qty}-{max_qty}kg" if max_qty != float('inf') else f"{min_qty}+kg"
    return 0, "No discount"

def calculate_quotation(parsed_data: Dict) -> Dict:
    """Calculate complete quotation with all pricing components"""
    product = parsed_data["product"]
    specification = parsed_data["specification"]
    quantity = parsed_data["quantity"]
    grade = parsed_data["grade"]
    city = parsed_data["city"]
    
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
    grade_premium_pct = GRADE_PREMIUMS[grade]["premium"]
    grade_premium_amt = subtotal * (grade_premium_pct / 100)
    
    # Add delivery cost
    delivery_cost = DELIVERY_COSTS[city]["cost"]
    
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
    
    return f"""
**ALCHEMY CHEMICALS - QUOTATION** 📋
---
**Product:** {quote['product_name']}
**Specification:** {quote['specification']}
**Grade:** {quote['grade']}
**Quantity:** {quote['quantity']}kg

**💰 Pricing Breakdown:**
• Base Price: ₹{quote['base_price']:,}/kg
• Subtotal: ₹{quote['subtotal']:,}
• Volume Discount ({quote['volume_tier']} tier): -{quote['volume_discount_pct']}% = **-₹{quote['volume_discount_amt']:,}**
• Grade Premium ({quote['grade']}): +{quote['grade_premium_pct']}% = **+₹{quote['grade_premium_amt']:,}**
• Delivery ({quote['delivery_city']}): **₹{quote['delivery_cost']:,}**
• **Subtotal:** ₹{quote['subtotal_before_gst']:,}
• GST (18%): ₹{quote['gst_amount']:,.0f}

**📍 TOTAL: ₹{quote['total']:,.0f}**

**Terms & Conditions:**
• MOQ: {quote['moq']}kg
• Lead Time: {quote['lead_time']}
• Quote Validity: Until {quote['validity']}
• Certifications: ISO 9001:2015, GMP, FDA

**For order confirmation:** info@alchemychemicals.net

---
✨ **Thank you for choosing Alchemy Chemicals!**
"""

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_msg = """👋 **Welcome to Alchemy Chemicals!**

I'm your AI assistant, powered by advanced language understanding. I can help you get instant quotations for our premium herbal extracts.

**Just chat naturally!** I understand:
• Product names (even with typos!)
• Compound sentences
• Partial information
• Context from our conversation

**Our Products:**
🌿 Ashwagandha, Boswellia, Curcumin, Neem, Tulsi

Try saying something like:
• "Hi, I need 50kg Ashwagandha"
• "Show me prices for Tulsi"
• "75kg pharmaceutical grade for Delhi"

Let's get started! How can I help you today? 😊"""
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# Initialize context
if "context" not in st.session_state:
    st.session_state.context = {
        "product": None,
        "specification": None,
        "quantity": None,
        "grade": None,
        "city": None
    }

# Streamlit UI
st.title("🧪 Alchemy Chemicals - AI Quotation Assistant")
st.markdown("Powered by conversational AI • Understands natural language • Remembers context")

# Sidebar
with st.sidebar:
    st.header("📋 Product Catalog")
    for product_key, product_info in PRODUCTS.items():
        with st.expander(f"🌿 {product_info['name']}"):
            for spec, details in product_info["specifications"].items():
                st.write(f"• {spec} {product_info['unit']}: ₹{details['base_price']:,}/kg")
                st.write(f"  MOQ: {details['moq']}kg")
    
    st.divider()
    st.header("🧠 What I Remember")
    
    memory_items = []
    if st.session_state.context["product"]:
        memory_items.append(f"✅ Product: **{PRODUCTS[st.session_state.context['product']]['name']}**")
    else:
        memory_items.append("⬜ Product: —")
        
    if st.session_state.context["specification"]:
        memory_items.append(f"✅ Specification: **{st.session_state.context['specification']}**")
    else:
        memory_items.append("⬜ Specification: —")
        
    if st.session_state.context["quantity"]:
        memory_items.append(f"✅ Quantity: **{st.session_state.context['quantity']}kg**")
    else:
        memory_items.append("⬜ Quantity: —")
        
    if st.session_state.context["grade"]:
        memory_items.append(f"✅ Grade: **{st.session_state.context['grade'].title()}**")
    else:
        memory_items.append("⬜ Grade: —")
        
    if st.session_state.context["city"]:
        memory_items.append(f"✅ City: **{st.session_state.context['city'].title()}**")
    else:
        memory_items.append("⬜ City: —")
    
    for item in memory_items:
        st.markdown(item)
    
    if all(v is None for v in st.session_state.context.values()):
        st.caption("Start chatting to build your order!")
    
    # Clear context button
    if st.button("🔄 Start New Quote"):
        st.session_state.context = {k: None for k in st.session_state.context}
        st.rerun()

# Main chat interface
st.markdown("### 💬 Chat with me naturally!")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type naturally... I understand context, typos, and compound sentences!"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process query
    with st.chat_message("assistant"):
        with st.spinner("Understanding your request..."):
            
            # Check for greeting
            if is_greeting(prompt):
                response = """Hello! 👋 Great to see you!

I'm here to help you get instant quotations for our herbal extracts. 

**What would you like to order today?** You can:
• Name a product (e.g., "Ashwagandha")
• Give me complete details (e.g., "50kg Tulsi 5%, pharmaceutical, Mumbai")
• Ask questions about our products

I remember our conversation, so just tell me what you need! 😊"""
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                # Reset context on greeting
                st.session_state.context = {k: None for k in st.session_state.context}
                
            # Check for help request
            elif any(word in prompt.lower() for word in ['help', 'how to', 'what can you']):
                response = """**I'm here to help!** 🤝

I understand natural language, so just chat with me like you would with a human sales representative.

**Examples of what you can say:**
• "I need Ashwagandha" → I'll ask for details
• "50kg" → I'll add quantity to your order
• "pharmaceutical grade" → I'll note the grade
• "deliver to Mumbai" → I'll add delivery location
• "75kg Tulsi 5% cosmetic Delhi" → I'll process everything!

**I also understand:**
• Spelling mistakes ("cometic" = cosmetic)
• Different formats ("in Pune", "to Delhi", "at Mumbai")
• Context (I remember what you've told me)

**Current order status:** Check the sidebar to see what I remember!

What would you like to order? 💬"""
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            else:
                # Parse the query with context
                if model:
                    parsed_data = parse_with_ai(prompt, st.session_state.context)
                else:
                    parsed_data = extract_all_info(prompt, st.session_state.context)
                
                # Update context
                for key, value in parsed_data.items():
                    if value is not None:
                        st.session_state.context[key] = value
                
                # Generate appropriate response
                response = generate_response(st.session_state.context)
                
                if response:
                    # Still missing information
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    # We have everything - generate quotation
                    try:
                        quotation = calculate_quotation(st.session_state.context)
                        formatted_quote = format_quotation(quotation)
                        st.markdown(formatted_quote)
                        st.session_state.messages.append({"role": "assistant", "content": formatted_quote})
                        
                        # Add download button
                        if "error" not in quotation:
                            st.download_button(
                                label="📥 Download Quotation",
                                data=formatted_quote,
                                file_name=f"quotation_{st.session_state.context['product']}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                                mime="text/plain"
                            )
                            
                            # Offer next steps
                            follow_up = """
---
**What would you like to do next?** 🤔
• Modify this quote? Just tell me what to change!
• Get a quote for another product? Just name it!
• Compare different specifications? Ask away!

I'm here to help! 😊"""
                            st.markdown(follow_up)
                            
                    except Exception as e:
                        error_msg = f"I encountered an issue: {str(e)}\n\nCould you please rephrase or provide the missing information? I'm here to help! 😊"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Example section
with st.expander("💡 Conversation Examples"):
    st.markdown("""
    **Natural Conversations:**
    • You: "Hi" → Bot greets and explains
    • You: "I need Ashwagandha" → Bot asks for details
    • You: "5%" → Bot remembers Ashwagandha, asks for more
    • You: "75kg pharmaceutical Mumbai" → Bot completes order!
    
    **Or say everything at once:**
    • "75kg Tulsi 5% cosmetic grade deliver to Pune"
    • "I need 100kg of Ashwagandha 10% for pharmaceutical use in Delhi"
    
    **Handles typos and variations:**
    • "cometic" → cosmetic
    • "delli" → Delhi
    • "ashwaganda" → Ashwagandha
    """)
