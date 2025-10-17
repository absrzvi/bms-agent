# 🔧 OpenWebUI Connection Issue - SOLUTION

## ✅ Problem Identified

The API works perfectly:
```bash
 curl http://localhost:8000/api/v1/search/semantic → Returns 3 results
 Tool code updated in OpenWebUI
 Tool still returns "No results found"
```

This means: **OpenWebUI can't connect to the BMS API**

---

## 🎯 SOLUTION: Update BMS_API_URL in Valves

### Option 1: Use Machine IP (RECOMMENDED)

Your machine IP: **10.128.14.2**

1. Go to OpenWebUI: http://localhost:3000
2. Click: **Workspace** → **Tools**
3. Find: **"bms_search"** tool
4. Click: **⚙️ SETTINGS** (gear icon)
5. Change **BMS_API_URL** to:
   ```
   http://10.128.14.2:8000
   ```
6. Click **SAVE**
7. Test: "what is business continuity"

### Option 2: Use 0.0.0.0 (Alternative)

If Option 1 doesn't work:
```
http://0.0.0.0:8000
```

### Option 3: Use 127.0.0.1

```
http://127.0.0.1:8000
```

---

## 🔍 Why This Happens

OpenWebUI might be running in a context where `localhost` resolves differently.

Using the actual machine IP (10.128.14.2) ensures OpenWebUI can reach the API.

---

## ✅ Verification

After changing the URL, test with:
```
"what is business continuity"
```

Should return:
```

1. BMS-BCON-FOR-005-Business Continuity Response PR Scenario.docx
2. BMS-BCON-FOR-001-Business Continuity Response Template.docx
3. BMS-BCON-FOR-004-Business Continuity Response Template - IT.docx
```

---

## 🚨 Important

The BMS API is listening on **0.0.0.0:8000** which means it accepts connections from any interface.

The issue is just that OpenWebUI needs the correct URL to reach it.

**Try the machine IP first: http://10.128.14.2:8000**
