# Alchemy Chemicals AI Quotation Chatbot Demo

## Quick Start (30 seconds)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
streamlit run app.py
```

### Step 3: Add OpenAI API Key
- Either add your OpenAI API key in the sidebar when the app opens
- OR create a `.streamlit/secrets.toml` file with:
```toml
OPENAI_API_KEY = "your-api-key-here"
```

**Note:** The app works without OpenAI API key using fallback regex parsing, but AI parsing provides better natural language understanding.

## 🎯 Demo Queries for Your Sales Call

### Basic Queries (Copy & Paste These):

1. **Standard Pharmaceutical Order:**
   ```
   Price for 50kg Ashwagandha extract 5% withanolides, pharmaceutical grade, delivery to Mumbai
   ```

2. **Bulk Cosmetic Order:**
   ```
   I need 100kg of Curcumin 95% purity for cosmetic use, deliver to Delhi
   ```

3. **Large Pharma Order (Volume Discount):**
   ```
   Quote for 200kg Boswellia extract 85% boswellic acid, pharma grade, Bangalore delivery
   ```

4. **Small Food Grade Order:**
   ```
   25kg Neem extract 5% azadirachtin, food grade, ship to Pune
   ```

5. **Local Delivery:**
   ```
   Tulsi extract 5% ursolic acid, 75kg, pharmaceutical grade, local delivery
   ```

### Advanced Demo Scenarios:

**Scenario 1: Price Comparison**
- First query: "50kg Ashwagandha 2.5% pharma Mumbai"
- Then query: "50kg Ashwagandha 5% pharma Mumbai"
- Show how concentration affects pricing

**Scenario 2: Volume Discount Demo**
- Query 1: "20kg Curcumin 95% pharma Delhi"
- Query 2: "50kg Curcumin 95% pharma Delhi"
- Query 3: "150kg Curcumin 95% pharma Delhi"
- Show discount tiers in action

**Scenario 3: Grade Premium Demo**
- Query same product with different grades:
  - "50kg Boswellia 65% food grade Mumbai"
  - "50kg Boswellia 65% cosmetic Mumbai"
  - "50kg Boswellia 65% pharmaceutical Mumbai"

## 📊 Key Features to Highlight

1. **Natural Language Understanding**
   - Works with informal queries like "need some ashwagandha for pharma use"
   - Handles variations: "pharmaceutical" or "pharma", "Bangalore" or "Bengaluru"

2. **Transparent Pricing Breakdown**
   - Shows all components: base price, discounts, premiums, delivery, GST
   - Client can verify calculations

3. **Professional Output**
   - Ready to copy-paste into emails
   - Includes all compliance info (certifications, MOQ, validity)

4. **Smart Validation**
   - Checks minimum order quantities
   - Prompts for missing information
   - Handles edge cases gracefully

## 🚀 Deployment Options

### Option 1: Local Demo (What you'll likely use)
- Run on your laptop during screen share
- Most reliable, no internet dependency except for OpenAI API

### Option 2: Streamlit Cloud (If time permits)
1. Push to GitHub
2. Deploy via share.streamlit.io
3. Share link with client

### Option 3: Quick Public URL (Using localtunnel)
```bash
npm install -g localtunnel
streamlit run app.py
# In another terminal:
lt --port 8501
```

## 💡 Sales Talking Points

### Value Propositions:
1. **Speed**: Instant quotations vs 2-3 hours manual process
2. **Accuracy**: Eliminates calculation errors
3. **Consistency**: Same pricing logic every time
4. **24/7 Availability**: Sales team can generate quotes anytime
5. **Scalability**: Handle multiple queries simultaneously

### ROI Metrics:
- Current: 2-3 hours per quotation × 20 quotations/day = 40-60 hours
- With Bot: 30 seconds × 20 quotations = 10 minutes
- Time Saved: ~39-59 hours daily
- Cost Savings: ₹500/hour × 40 hours = ₹20,000/day

### Integration Possibilities:
- Connect to ERP for live inventory
- WhatsApp Business API integration
- Email automation
- CRM integration
- Multi-language support (Hindi, Gujarati)

## ⚠️ Troubleshooting

### If OpenAI API doesn't work:
- App has fallback regex parsing
- Still functional, just less sophisticated

### If Streamlit won't start:
```bash
python -m streamlit run app.py
```

### Port already in use:
```bash
streamlit run app.py --server.port 8502
```

## 📝 Configuration Notes

### Products Available:
- Ashwagandha Extract (2.5%, 5%, 10% withanolides)
- Boswellia Extract (65%, 85% boswellic acid)
- Curcumin Extract (90%, 95%, 98% purity)
- Neem Extract (1%, 5% azadirachtin)
- Tulsi Extract (2%, 5% ursolic acid)

### Pricing Logic:
- Base prices: ₹1,500-4,000/kg
- Volume discounts: 0-20%
- Grade premiums: 0-20%
- Delivery: ₹1,000-4,800
- GST: 18% on total

### Customization for Demo:
- Easy to modify products in `PRODUCTS` dict
- Simple to adjust pricing in respective dictionaries
- Can add new cities, grades, etc.

## 🎬 Demo Script

1. **Opening (30 sec)**
   - "Let me show you our AI quotation assistant"
   - Show the clean interface

2. **Basic Query (1 min)**
   - Type: "50kg Ashwagandha 5% pharma grade Mumbai"
   - Point out instant response
   - Highlight pricing breakdown

3. **Complex Query (1 min)**
   - Show bulk order with volume discount
   - Demonstrate grade premium calculation

4. **Error Handling (30 sec)**
   - Type incomplete query
   - Show how bot asks for missing info

5. **Closing (30 sec)**
   - "This is just a demo built in 40 minutes"
   - "Full version can integrate with your ERP, WhatsApp, etc."
   - "ROI within 2 weeks of deployment"

---

**For urgent support during demo:** The app is designed to be robust. If anything fails, the fallback parser will still work. Focus on the business value, not technical perfection.

Good luck with your pitch! 🚀
