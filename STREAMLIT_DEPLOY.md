# 🚀 Streamlit Cloud Deployment - Quick Guide

## Deploy in 3 Minutes

### Step 1: Go to Streamlit Cloud
Visit: **https://share.streamlit.io/**

### Step 2: Create New App
1. Click **"New app"** button
2. Fill in:
   - **Repository:** `DivyanshuSalve/ChatBot`
   - **Branch:** `main`
   - **Main file path:** `app.py`

### Step 3: Add Gemini API Key (CRITICAL!)
**Before clicking Deploy:**
1. Click **"Advanced settings"**
2. In the **"Secrets"** section, paste this EXACTLY:
   ```toml
   GEMINI_API_KEY = "AIzaSyANaxNxRTVgClU0Jz3W3ONCioejCe8jlWc"
   ```
3. Click **"Deploy"**

**OR after deployment:**
1. Click **⋮ menu** → **Settings** → **Secrets**
2. Paste the same content
3. Click **"Save"** (app will restart automatically)

---

## ✅ Verify It's Working

After deployment, check:
1. **Sidebar shows:** "✅ Gemini AI Active" (green)
2. **No API key input field** visible
3. **Test conversation:**
   - Type: "Hi"
   - Should get intelligent greeting response
   - Type: "What products do you have?"
   - Should list all 5 products

---

## 🔒 Security

- ✅ API key is stored securely in Streamlit Cloud
- ✅ Not visible in code or to users
- ✅ Not committed to GitHub (in `.gitignore`)
- ✅ Only accessible to your deployed app

---

## 🐛 Troubleshooting

### "ℹ️ Using smart parser mode" appears
**Problem:** API key not loaded
**Fix:** 
1. Go to app Settings → Secrets
2. Verify the format is EXACTLY:
   ```toml
   GEMINI_API_KEY = "AIzaSyANaxNxRTVgClU0Jz3W3ONCioejCe8jlWc"
   ```
3. No extra spaces, correct quotes
4. Save and wait for restart

### App shows error on startup
**Problem:** Dependencies not installed
**Fix:** Check `requirements.txt` includes:
```
streamlit==1.29.0
google-generativeai
python-dotenv==1.0.0
```

### Model error (404)
**Problem:** Wrong model name
**Fix:** Code should use `gemini-2.0-flash` (already updated)

---

## 📱 Your Live App URL

After deployment, your app will be at:
```
https://[your-app-name].streamlit.app
```

Example: `https://divyanshusalve-chatbot-app-xyz123.streamlit.app`

**Share this URL** during your sales demo!

---

## 🎯 Demo Checklist

Before your sales call:
- [ ] App deployed and accessible
- [ ] Gemini API key working (green checkmark in sidebar)
- [ ] Test conversation flow works
- [ ] Test quotation generation works
- [ ] Download button works
- [ ] Bookmark the live URL

---

## 🔄 Updating Your App

When you push changes to GitHub:
1. Streamlit Cloud auto-detects changes
2. App rebuilds automatically
3. Usually takes 1-2 minutes
4. No manual redeployment needed!

---

## 💡 Pro Tips

1. **Test locally first:** Always test changes locally before pushing
2. **Use the sidebar:** Shows what the bot remembers
3. **Clear order button:** Resets conversation for new quote
4. **Download quotations:** Great for showing clients

---

**You're ready to deploy! Good luck with your demo! 🚀**
