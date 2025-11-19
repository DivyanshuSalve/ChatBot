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

# Initialize Gemini API
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)
except:
    GEMINI_API_KEY = None

if not GEMINI_API_KEY:
    GEMINI_API_KEY = st.sidebar.text_input("Gemini API Key (required for AI features)", type="password")

model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        st.sidebar.success("✅ Gemini AI Active")
    except Exception as e:
        st.sidebar.error(f"⚠️ Gemini API error: {e}")
        model = None

# Product catalog
PRODUCT_CATALOG = """
PRODUCT CATALOG:
1. Ashwagandha Extract
   - Specifications: 2.5%, 5%, 10% Withanolides
   - Base prices: ₹1,800/kg, ₹2,800/kg, ₹3,600/kg
   - MOQ: 25kg, 25kg, 20kg

2. Boswellia Extract
   - Specifications: 65%, 85% Boswellic Acid
   - Base prices: ₹2,200/kg, ₹3,200/kg
   - MOQ: 25kg, 20kg

3. Curcumin Extract
   - Specifications: 90%, 95%, 98% Purity
   - Base prices: ₹2,500/kg, ₹3,000/kg, ₹3,800/kg
   - MOQ: 25kg, 25kg, 20kg

4. Neem Extract
   - Specifications: 1%, 5% Azadirachtin
   - Base prices: ₹1,500/kg, ₹2,600/kg
   - MOQ: 30kg, 25kg

5. Tulsi Extract
   - Specifications: 2%, 5% Ursolic Acid
   - Base prices: ₹1,700/kg, ₹2,400/kg
   - MOQ: 30kg, 25kg

PRICING STRUCTURE:
- Volume Discounts: 1-24kg: 0%, 25-99kg: 10%, 100-499kg: 15%, 500+kg: 20%
- Grade Premiums: Pharmaceutical: +20%, Cosmetic: +10%, Food: 0%
- Delivery: Mumbai: ₹3,500, Delhi: ₹4,200, Bangalore: ₹4,800, Pune: ₹3,200, Ujjain/Local: ₹1,000
- GST: 18% on total
"""

# Products data for calculation
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

VOLUME_DISCOUNTS = {
    (1, 24): 0,
    (25, 99): 10,
    (100, 499): 15,
    (500, float('inf')): 20
}

GRADE_PREMIUMS = {
    "pharmaceutical": 20,
    "cosmetic": 10,
    "food": 0
}

DELIVERY_COSTS = {
    "mumbai": 3500,
    "delhi": 4200,
    "bangalore": 4800,
    "pune": 3200,
    "ujjain": 1000,
    "local": 1000
}

GST_RATE = 0.18

def get_volume_discount(quantity: int) -> Tuple[int, str]:
    """Calculate volume discount based on quantity"""
    for (min_qty, max_qty), discount in VOLUME_DISCOUNTS.items():
        if min_qty <= quantity <= max_qty:
            return discount, f"{min_qty}-{max_qty}kg" if max_qty != float('inf') else f"{min_qty}+kg"
    return 0, "No discount"

def calculate_quotation(order_data: Dict) -> Dict:
    """Calculate complete quotation with all pricing components"""
    try:
        product = order_data["product"].lower()
        specification = order_data["specification"]
        quantity = order_data["quantity"]
        grade = order_data["grade"].lower()
        city = order_data["city"].lower()
        
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
        grade_premium_pct = GRADE_PREMIUMS.get(grade, 0)
        grade_premium_amt = subtotal * (grade_premium_pct / 100)
        
        # Add delivery cost
        delivery_cost = DELIVERY_COSTS.get(city, 1000)
        
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
    except Exception as e:
        return {"error": f"Unable to calculate quotation: {str(e)}"}

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
• Volume Discount ({quote['volume_tier']} tier): -{quote['volume_discount_pct']}% = **-₹{quote['volume_discount_amt']:,.0f}**
• Grade Premium ({quote['grade']}): +{quote['grade_premium_pct']}% = **+₹{quote['grade_premium_amt']:,.0f}**
• Delivery ({quote['delivery_city']}): **₹{quote['delivery_cost']:,}**
• **Subtotal:** ₹{quote['subtotal_before_gst']:,.0f}
• GST (18%): ₹{quote['gst_amount']:,.0f}

**📍 TOTAL: ₹{quote['total']:,.0f}**

**Terms & Conditions:**
• MOQ: {quote['moq']}kg
• Lead Time: {quote['lead_time']}
• Quote Validity: Until {quote['validity']}
• Certifications: ISO 9001:2015, GMP, FDA

**For order confirmation:** info@alchemychemicals.net

✨ **Thank you for choosing Alchemy Chemicals!**
"""

def process_with_gemini(user_message: str, conversation_history: list, order_context: Dict) -> tuple:
    """Let Gemini handle the entire conversation intelligently"""
    
    if not model:
        return "I need Gemini API to work properly. Please add your API key in the sidebar.", order_context
    
    # Build conversation history for context
    history_text = ""
    for msg in conversation_history[-10:]:  # Last 10 messages for context
        role = "Customer" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"
    
    # Build current order status
    order_status = json.dumps(order_context, indent=2)
    
    prompt = f"""You are an AI sales assistant for Alchemy Chemicals, a premium herbal extract manufacturer. 
You help customers get quotations and answer questions about products.

{PRODUCT_CATALOG}

CONVERSATION HISTORY:
{history_text}

CURRENT ORDER CONTEXT (what we know so far):
{order_status}

NEW CUSTOMER MESSAGE: "{user_message}"

INSTRUCTIONS:
1. First, determine the customer's intent:
   - Are they asking for information? (product list, prices, MOQs, etc.)
   - Are they trying to place an order?
   - Are they greeting you?
   - Are they asking for help?

2. If they're asking for information, provide it directly. Don't try to extract order details.
   - "what products do you have?" -> List all products
   - "minimum order values" -> Show MOQ for each product
   - "prices" -> Show pricing structure

3. If they're placing an order or providing order details, extract and update the order context.

4. Respond naturally and helpfully based on the intent.

5. Return your response in this JSON format:
{{
    "response": "Your natural language response to the customer",
    "intent": "greeting/information/order/help",
    "order_context": {{
        "product": "product name if mentioned/updated or null",
        "specification": "spec if mentioned or null",
        "quantity": quantity if mentioned or null,
        "grade": "grade if mentioned or null",
        "city": "city if mentioned or null"
    }},
    "should_generate_quote": true/false
}}

IMPORTANT:
- For information queries, don't extract order details
- Handle typos and variations (ashwaganda->ashwagandha, cometic->cosmetic, etc.)
- Keep previous order context unless explicitly changed
- Only set should_generate_quote to true when ALL order details are complete
"""

    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            
            # Update order context only with non-null values
            if parsed.get("order_context"):
                for key, value in parsed["order_context"].items():
                    if value is not None:
                        order_context[key] = value
            
            return parsed.get("response", "I understand. How can I help you?"), order_context, parsed.get("should_generate_quote", False)
            
    except Exception as e:
        return f"I encountered an issue: {e}. Could you please rephrase?", order_context, False
    
    return "I'm having trouble understanding. Could you please rephrase?", order_context, False

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_msg = """👋 **Welcome to Alchemy Chemicals!**

I'm your AI sales assistant. I can help you:
• Get instant quotations for herbal extracts
• Answer questions about our products
• Explain pricing and minimum orders

**Our Products:**
🌿 Ashwagandha, Boswellia, Curcumin, Neem, Tulsi

**Just chat naturally!** Ask me anything like:
• "What products do you have?"
• "What are the minimum order quantities?"
• "I need 50kg Ashwagandha"
• "Show me prices for Tulsi"

How can I help you today? 😊"""
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# Initialize order context
if "order_context" not in st.session_state:
    st.session_state.order_context = {
        "product": None,
        "specification": None,
        "quantity": None,
        "grade": None,
        "city": None
    }

# Streamlit UI
st.title("🧪 Alchemy Chemicals - AI Quotation Assistant")
st.markdown("Powered by Gemini AI • Natural conversations • Intelligent responses")

# Sidebar
with st.sidebar:
    st.header("📋 Quick Reference")
    
    with st.expander("🌿 Products & MOQ"):
        st.markdown("""
        **Ashwagandha Extract**
        • 2.5% - MOQ: 25kg
        • 5% - MOQ: 25kg  
        • 10% - MOQ: 20kg
        
        **Boswellia Extract**
        • 65% - MOQ: 25kg
        • 85% - MOQ: 20kg
        
        **Curcumin Extract**
        • 90% - MOQ: 25kg
        • 95% - MOQ: 25kg
        • 98% - MOQ: 20kg
        
        **Neem Extract**
        • 1% - MOQ: 30kg
        • 5% - MOQ: 25kg
        
        **Tulsi Extract**
        • 2% - MOQ: 30kg
        • 5% - MOQ: 25kg
        """)
    
    st.divider()
    st.header("🛒 Current Order")
    
    if st.session_state.order_context["product"]:
        st.success(f"✅ Product: **{st.session_state.order_context['product']}**")
    else:
        st.info("⬜ Product: —")
        
    if st.session_state.order_context["specification"]:
        st.success(f"✅ Specification: **{st.session_state.order_context['specification']}**")
    else:
        st.info("⬜ Specification: —")
        
    if st.session_state.order_context["quantity"]:
        st.success(f"✅ Quantity: **{st.session_state.order_context['quantity']}kg**")
    else:
        st.info("⬜ Quantity: —")
        
    if st.session_state.order_context["grade"]:
        st.success(f"✅ Grade: **{st.session_state.order_context['grade']}**")
    else:
        st.info("⬜ Grade: —")
        
    if st.session_state.order_context["city"]:
        st.success(f"✅ City: **{st.session_state.order_context['city']}**")
    else:
        st.info("⬜ City: —")
    
    # Clear order button
    if st.button("🔄 Clear Order"):
        st.session_state.order_context = {k: None for k in st.session_state.order_context}
        st.rerun()

# Main chat interface
st.markdown("### 💬 Chat with me")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about our products or place an order..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process with Gemini
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response, updated_context, should_quote = process_with_gemini(
                prompt, 
                st.session_state.messages,
                st.session_state.order_context
            )
            
            # Update order context
            st.session_state.order_context = updated_context
            
            # Generate quotation if ready
            if should_quote:
                quotation = calculate_quotation(st.session_state.order_context)
                formatted_quote = format_quotation(quotation)
                st.markdown(formatted_quote)
                st.session_state.messages.append({"role": "assistant", "content": formatted_quote})
                
                if "error" not in quotation:
                    st.download_button(
                        label="📥 Download Quotation",
                        data=formatted_quote,
                        file_name=f"quotation_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain"
                    )
                    
                    follow_up = "\n**What next?** Modify this quote? Get another product quote? Just let me know! 😊"
                    st.markdown(follow_up)
            else:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# Info section
with st.expander("ℹ️ How to Use"):
    st.markdown("""
    **Ask Questions:**
    • "What products do you have?"
    • "Show me minimum order quantities"
    • "What are your prices?"
    
    **Place Orders:**
    • "I need 50kg Ashwagandha"
    • "5% concentration"
    • "Pharmaceutical grade"
    • "Deliver to Mumbai"
    
    **Or all at once:**
    • "50kg Ashwagandha 5% pharmaceutical Mumbai"
    
    I understand natural language and remember our conversation!
    """)
