# HTML Artifact Generation - Deployment & Testing Guide

**Version**: 4.0  
**Feature**: Static HTML document generation as artifacts  
**Status**: Ready for deployment

---

## 🎯 What Changed

### Before (v3.1): Search-Only Agent
- User asks for form → Agent describes what the form contains
- User asks for checklist → Agent lists items in chat
- User asks to compare → Agent writes paragraphs

### After (v4.0): Document Generator Agent
- User asks for form → **Agent generates complete HTML form**
- User asks for checklist → **Agent generates HTML checklist with checkboxes**
- User asks to compare → **Agent generates HTML comparison table**

**Result**: Downloadable, print-ready, professional documents

---

## 📋 Deployment Steps

### Step 1: Update System Prompt in OpenWebUI

1. **Open OpenWebUI Admin Panel**:
   ```
   http://localhost:3000/admin
   ```

2. **Navigate to**: Settings → Models → [Your Model] → System Prompt

3. **Copy New Prompt**:
   ```bash
   cat /workspace/001-bms-agent/docs/SYSTEM_PROMPT_v4.0.md
   ```

4. **Paste** entire content into system prompt field

5. **Save Changes**

6. **Restart Chat**: Start new conversation to apply changes

---

### Step 2: Verify BMS Search Tool Loaded

1. Open new chat in OpenWebUI
2. Check that "BMS Agent Search" tool appears
3. Ensure all 13 search functions available
4. Test basic search: "Show me GDPR documents"

---

### Step 3: Test HTML Artifact Generation

Run these 5 test prompts to verify HTML generation works:

#### Test 1: Form Generation ⭐
**Prompt**:
```
Fill out a vendor evaluation form for Bombardier Transportation. 
They're based in Berlin, Germany, have 25 years of railway experience, 
ISO9001 certified, and quoted €45,000 for brake components.
```

**Expected Output**:
- ✅ Complete HTML document appears above chat response
- ✅ Professional blue-themed form
- ✅ All vendor details filled in
- ✅ Evaluation criteria table with star ratings
- ✅ Recommendation section (Approved/Pending/Review)
- ✅ Citations footer with document URLs
- ✅ Print button at bottom

**If FAILS**: 
- Check system prompt is loaded (v4.0)
- Verify LLM supports HTML generation
- Try simpler prompt: "Create a vendor form for Bombardier"

---

#### Test 2: Checklist Generation
**Prompt**:
```
Create a safety checklist for HVAC system installation in Cityjet trains. 
Include pre-installation, during installation, and post-installation phases.
```

**Expected Output**:
- ✅ HTML checklist with ☐ checkboxes
- ✅ Organized by 3 phases
- ✅ 15-20 safety items
- ✅ Citations to safety procedures
- ✅ Print-ready format

---

#### Test 3: Comparison Table
**Prompt**:
```
Compare the procurement approval processes between ENGI and QHSE departments. 
Show differences in thresholds, timelines, and required documentation.
```

**Expected Output**:
- ✅ HTML table with side-by-side comparison
- ✅ Columns: Aspect | ENGI | QHSE | Difference
- ✅ Color-coded rows
- ✅ Explanation section
- ✅ Citations to both department procedures

---

#### Test 4: Workflow Generation
**Prompt**:
```
Create an onboarding workflow for a new railway engineer joining ENGI department. 
Include all required forms, training, and timeline.
```

**Expected Output**:
- ✅ HTML document with week-by-week timeline
- ✅ Sections: Week 1, Week 2, Week 3-4
- ✅ Forms listed with BMS document IDs
- ✅ Training requirements
- ✅ Responsibility assignments
- ✅ 10-15 cited documents

---

#### Test 5: Filled Form with Data
**Prompt**:
```
Generate a procurement request form for 100 LED display panels for Railjet fleet. 
Cost: €25,000. Priority: High. Needed for Q2 2025 upgrade project.
```

**Expected Output**:
- ✅ Complete procurement form
- ✅ Item details filled (100 LED panels, €25k)
- ✅ Department auto-determined (ENGI or SERV)
- ✅ Priority level set to High
- ✅ Approval routing based on €25k threshold
- ✅ Justification section filled

---

## ✅ Test Results Template

| Test | Prompt | Expected | Result | Notes |
|------|--------|----------|--------|-------|
| 1 | Vendor form | HTML with filled fields | ☐ Pass ☐ Fail | _________ |
| 2 | Safety checklist | HTML with checkboxes | ☐ Pass ☐ Fail | _________ |
| 3 | Comparison table | HTML side-by-side | ☐ Pass ☐ Fail | _________ |
| 4 | Onboarding workflow | HTML timeline | ☐ Pass ☐ Fail | _________ |
| 5 | Procurement form | HTML filled form | ☐ Pass ☐ Fail | _________ |

**Overall**: ____ / 5 passing

---

## 🚨 Troubleshooting

### Issue 1: No HTML Generated (Just Text Response)
**Symptoms**: Agent responds with text description instead of HTML artifact

**Possible Causes**:
1. System prompt v4.0 not loaded
2. LLM doesn't support HTML generation
3. Prompt too vague

**Solutions**:
- Verify system prompt: Check "HTML ARTIFACT GENERATION" section exists
- Try explicit prompt: "Generate an HTML form for..."
- Check LLM model: mistral-nemo or GPT-4 recommended
- Restart OpenWebUI to apply changes

---

### Issue 2: Incomplete HTML (Missing Sections)
**Symptoms**: HTML generated but missing footer, citations, or styling

**Possible Causes**:
1. LLM truncating response (token limit)
2. Prompt unclear about requirements

**Solutions**:
- Increase max tokens in model settings (2048+ recommended)
- Add "include all sections and citations" to prompt
- Simplify request (fewer fields/items)

---

### Issue 3: HTML Not Styled (No Colors/Layout)
**Symptoms**: HTML displays but looks plain/unstyled

**Possible Causes**:
1. CSS not embedded in HTML
2. Browser not rendering styles

**Solutions**:
- Check HTML contains `<style>` block
- View HTML source to verify CSS present
- Try different browser
- Download HTML and open locally

---

### Issue 4: No Citations in Footer
**Symptoms**: HTML generated but missing source documents

**Possible Causes**:
1. Search not executed before generation
2. Citations not being included in footer

**Solutions**:
- Ensure prompt requires search (references procedures/forms)
- Check "MANDATORY" rules in system prompt
- Add "cite all sources" to prompt

---

### Issue 5: HTML Not Downloadable/Printable
**Symptoms**: Can't save or print HTML artifact

**Possible Causes**:
1. OpenWebUI artifact display limitations
2. Print button not working

**Solutions**:
- Copy HTML and save as .html file locally
- Open .html file in browser
- Use browser's Save As → Web Page, Complete
- Use Print to PDF from browser

---

## 🎨 Customization Options

### Change Color Theme
Edit system prompt CSS:
```css
/* Current: Blue theme */
#0066cc → Corporate blue

/* Alternative: Green theme */
#0066cc → #28a745 (Success green)

/* Alternative: Purple theme */
#0066cc → #6f42c1 (Professional purple)
```

### Change Font
Edit system prompt CSS:
```css
/* Current */
font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;

/* Alternative: Professional */
font-family: 'Georgia', 'Times New Roman', serif;

/* Alternative: Modern */
font-family: 'Arial', 'Helvetica', sans-serif;
```

### Add Company Logo
Add to header section in HTML template:
```html
<div class="header">
    <img src="logo.png" alt="Nomad Digital" style="height: 50px;">
    <h1>[Document Title]</h1>
    ...
</div>
```

---

## 📊 Success Criteria

### For Deployment ✅
- [ ] System prompt v4.0 loaded in OpenWebUI
- [ ] BMS search tool active (13 functions)
- [ ] All 5 test prompts executed
- [ ] At least 4/5 tests generate HTML artifacts
- [ ] HTML artifacts include citations
- [ ] HTML artifacts are print-ready

### For Demo Recording ✅
- [ ] Choose 2-3 best artifact examples
- [ ] HTML displays cleanly on screen
- [ ] Print button works
- [ ] Citations visible in footer
- [ ] Professional appearance (blue theme)
- [ ] Downloadable as .html file

---

## 🎬 Demo Integration

### Update Agentic Demo Script

**Before (without HTML)**:
```
"I'll describe what the vendor evaluation form should contain..."
[Long text response in chat]
```

**After (with HTML v4.0)**:
```
📄 [HTML Form Appears Above]

"I've generated a complete vendor evaluation form above. 
You can print it, download it, or submit it for approval."
```

### Recording Tips for HTML Artifacts

1. **Show HTML Loading**: Wait for complete artifact to render
2. **Scroll Through**: Show all sections (header, fields, footer)
3. **Highlight Print Button**: Click to show print dialog
4. **Point Out Citations**: Scroll to footer, show source documents
5. **Download Demo**: Save as .html, show it opens in browser

### Demo Prompts (HTML-Optimized)

Use these instead of generic prompts:

| Scenario | Prompt | Shows |
|----------|--------|-------|
| Form filling | "Fill out vendor eval for Siemens, ISO9001, €75k" | Complete form generation |
| Checklist | "Safety checklist for brake installation in Railjet" | Checkbox list, phases |
| Comparison | "Compare ENGI vs QHSE procurement processes" | Table with differences |
| Workflow | "Onboarding plan for QHSE safety officer" | Timeline with forms |

---

## 💡 Best Practices

### For Users

**DO**:
- ✅ Be specific about what document you need
- ✅ Provide all data upfront (vendor name, amounts, dates)
- ✅ Request specific document types (form, checklist, workflow)
- ✅ Download HTML artifacts for record-keeping
- ✅ Print for signatures/approvals

**DON'T**:
- ❌ Ask vague questions like "tell me about vendors"
- ❌ Expect HTML for general information queries
- ❌ Edit HTML in browser (download and edit locally)

### For Administrators

**DO**:
- ✅ Keep system prompt version in sync (v4.0)
- ✅ Monitor token usage (HTML generation uses more tokens)
- ✅ Test HTML generation monthly
- ✅ Collect user feedback on artifact quality
- ✅ Update CSS styling based on brand guidelines

**DON'T**:
- ❌ Mix v3.1 and v4.0 prompts
- ❌ Reduce max tokens below 2048
- ❌ Remove citation requirements
- ❌ Allow HTML without footer/sources

---

## 📈 Metrics to Track

### Quality Metrics
- **HTML Completeness**: % of artifacts with all sections
- **Citation Accuracy**: % of artifacts with correct source URLs
- **Styling Consistency**: % of artifacts using blue theme
- **Print Success**: % of artifacts successfully printed

### Usage Metrics
- **Adoption Rate**: % of queries requesting artifacts
- **Document Types**: Forms vs checklists vs comparisons vs workflows
- **Download Rate**: % of artifacts downloaded as .html
- **Time Savings**: Estimated hours saved (30 min → 2 min per form)

### User Satisfaction
- **Usefulness**: 1-5 rating of artifact quality
- **Accuracy**: % of artifacts requiring manual corrections
- **Preference**: HTML artifacts vs text descriptions

---

## 🚀 Next Steps

### After Successful Deployment

1. **Update Agentic Demo Guide**:
   - Add HTML artifact screenshots
   - Update recording script with artifact demos
   - Show download/print functionality

2. **Create Example Library**:
   - Save 10-15 high-quality HTML artifacts
   - Organize by type (forms, checklists, workflows)
   - Use as templates for future requests

3. **User Training**:
   - Create quick-start guide for HTML generation
   - Document common prompts and expected outputs
   - Train key users on downloading/printing

4. **Iterate**:
   - Collect feedback on styling/layout
   - Add new document types as needed
   - Refine CSS based on user preferences

---

## 📚 Reference

### Files
- `docs/SYSTEM_PROMPT_v4.0.md` - Full system prompt with HTML
- `docs/SYSTEM_PROMPT_v3.1.md` - Previous version (search-only)
- `docs/AGENTIC_CAPABILITIES_DEMO.md` - Demo scenarios

### Related Tasks
- T032.3: Demo recording (now includes HTML artifacts)
- T036: API endpoint coverage (HTML generation builds on this)

### Version History
- **v4.0** (2025-10-05): Added HTML artifact generation
- **v3.1** (2025-10-04): Search functions and explainability
- **v3.0** (2025-10-03): Initial agent capabilities

---

**Deployment Status**: ☐ Not Started ☐ In Progress ☐ Complete ☐ Verified

**Notes**:
```
[Your deployment notes here]
```

**Date Deployed**: __________  
**Deployed By**: __________  
**Test Results**: ____ / 5 passing
