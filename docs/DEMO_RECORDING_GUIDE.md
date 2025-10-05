# BMS Agent POC Demo Recording Guide

**Purpose**: Record 3-5 minute demonstration video for POC completion  
**Target Audience**: Stakeholders, project sponsors, technical reviewers  
**Success Criteria**: Show working system with real search results from 644-document corpus

---

## ✅ Pre-Recording Checklist (Complete This First)

### System Status Verification
- [x] **BMS API**: ✅ Healthy (http://localhost:8000/health)
- [x] **Qdrant**: ✅ Connected (1,794 chunks indexed)
- [ ] **OpenWebUI**: Check http://localhost:3000 (needs verification)
- [ ] **BMS Search Tool**: Verify tool loaded in OpenWebUI admin panel

### Document Corpus Status
- [x] **Total Documents**: 644 documents processed
- [x] **Total Chunks**: 1,794 chunks indexed
- [x] **SharePoint URLs**: 565 documents with URLs (87.7%)
- [x] **Quality**: All documents ≥0.70 quality threshold
- [x] **Collections**: Dual-collection architecture verified (T037)

### Test Results Ready
- [x] **Retrieval Tests**: 11/15 passing (73.3%)
- [x] **Best Performers**: Procurement (100%), Quality (100%), GDPR (9/10)
- [x] **Known Limitations**: 3 documented with workarounds

---

## 🎬 Recording Setup (10 minutes before recording)

### 1. Browser Preparation
```bash
# Close unnecessary tabs
# Set zoom to 110% for better readability
# Clear any previous OpenWebUI chats
# Open OpenWebUI in fresh browser window
```

### 2. Screen Recording Tool
**Options**:
- **Linux**: OBS Studio, SimpleScreenRecorder, Kazam
- **Mac**: QuickTime, ScreenFlow
- **Windows**: OBS Studio, Xbox Game Bar

**Recommended Settings**:
- Resolution: 1920x1080 (1080p)
- Frame rate: 30 fps
- Audio: Optional (voiceover or text captions)
- Format: MP4 (H.264 codec)

### 3. Test Quick Queries (Rehearsal)
Run these in OpenWebUI to verify speed:
- `Show me GDPR compliance documents` (5 seconds)
- `Find procurement forms for external opportunities` (7 seconds)
- `What is the vendor selection process?` (6 seconds)

**If any query takes >10 seconds**: Note it and use backup query

---

## 📝 Demo Script (3-5 minutes)

### Scene 1: Introduction (30 seconds)
**What to show**: OpenWebUI home screen

**What to say/caption**:
```
BMS Agent - Railway Documentation Search System
- 644 internal documents indexed
- 1,794 semantic chunks
- 13 departments covered
- Real SharePoint URLs
```

**Action**: Show clean OpenWebUI interface, point out "BMS Agent Search" tool

---

### Scene 2: GDPR Compliance Search (60 seconds)
**Query**: `Show me GDPR compliance documents`

**Expected Results**:
- 5 documents returned
- BMS-ISEC-POL-002 as top result (quality 9/10)
- Real SharePoint URL with 🔗 icon
- Star ratings: ⭐⭐⭐⭐⭐
- Relevance: 88%

**What to highlight**:
- "Search completed in under 5 seconds"
- "Top result is exact match for GDPR policy"
- "Real SharePoint link for direct access"
- "Quality score shows document reliability"

**Backup Query** (if slow): `GDPR compliance`

---

### Scene 3: Procurement Forms (60 seconds)
**Query**: `Find procurement forms for external opportunities`

**Expected Results**:
- 9 documents returned
- BMS-PROJ-FOR-002 included
- Multiple departments (PROJ, BDEV)
- Quality 9/10

**What to highlight**:
- "System found 9 relevant forms"
- "Covers procurement workflow end-to-end"
- "Multiple document types (PDF, Excel, Word)"
- "Department filtering works automatically"

**Backup Query**: `procurement forms`

---

### Scene 4: Business Process (60 seconds)
**Query**: `What is the vendor selection process?`

**Expected Results**:
- 5 documents returned
- BMS-PROJ-GUI-007 as top result
- Comprehensive guidance
- Quality 9/10

**What to highlight**:
- "System understands business process queries"
- "Returns structured guidance document"
- "Includes evaluation criteria and procedures"
- "High relevance and quality scores"

**Backup Query**: `vendor selection and evaluation process`

---

### Scene 5: Strengths Summary (30 seconds)
**What to show**: Results from previous queries still visible

**What to say/caption**:
```
System Strengths Demonstrated:
✅ Fast retrieval (5-7 seconds average)
✅ High accuracy (73.3% test success rate)
✅ Department coverage (QHSE, ISEC, PROJ, HUMR)
✅ Real SharePoint URLs (87.7% coverage)
✅ Quality filtering (≥0.70 threshold)
✅ 644 documents, 1,794 searchable chunks
```

---

### Scene 6: Known Limitations (30 seconds - Optional)
**What to show**: Text slide or caption

**What to say**:
```
Known Limitations (POC Phase):
- Technical architecture queries limited
- Exact document code matching needs improvement
- Response times 5-7 seconds (MVP target: <3s)
- MVP improvements planned
```

**Note**: This shows transparency and sets expectations

---

## 🎯 Alternative Demo Paths

### Path A: Feature-Focused (Recommended)
1. Introduction (30s)
2. GDPR Search - **Accuracy** (60s)
3. Procurement Forms - **Coverage** (60s)
4. Vendor Selection - **Business Value** (60s)
5. Summary + Stats (30s)
**Total**: 3.5 minutes

### Path B: Use-Case Focused
1. Introduction (30s)
2. Compliance Scenario - "I need GDPR docs" (90s)
3. Procurement Scenario - "I'm filling a form" (90s)
4. Summary (30s)
**Total**: 4 minutes

### Path C: Technical Deep-Dive
1. Introduction (30s)
2. Simple Search - GDPR (45s)
3. Complex Search - Multi-doc procurement (60s)
4. Smart Search - Show metadata boosting (60s)
5. Architecture Stats (45s)
**Total**: 4.5 minutes

---

## 🚨 Troubleshooting During Recording

### Issue: Query Takes >10 seconds
**Solution**: 
- Pause recording
- Use backup query
- Or: Keep recording and say "System under load" (honest)

### Issue: Wrong Results Returned
**Solution**:
- Use backup query from test cases
- Or: Show it as "learning opportunity" (honest approach)

### Issue: OpenWebUI Not Responding
**Solution**:
- Check http://localhost:3000
- Restart OpenWebUI if needed
- Reload tool in admin panel

### Issue: No Results Found
**Solution**:
- Verify Qdrant: `curl http://localhost:6333/collections/nomad_bms_documents`
- Check API: `curl http://localhost:8000/health`
- Use known-good query: "GDPR compliance"

---

## ✅ Pre-Recording System Tests (Run 30 minutes before)

Copy these exact tests from `T032.3_PRE_DEMO_TEST.md`:

### Test 1: GDPR Compliance ✅
```
Query: Show me GDPR compliance documents
Expected: 5 docs, BMS-ISEC-POL-002 top, quality 9/10
Status: [ ] Pass [ ] Fail
Time: ____ seconds
```

### Test 2: Procurement Forms ✅
```
Query: Find procurement forms for external opportunities
Expected: 9 docs, BMS-PROJ-FOR-002, quality 9/10
Status: [ ] Pass [ ] Fail
Time: ____ seconds
```

### Test 3: Vendor Selection ✅
```
Query: What is the vendor selection process?
Expected: 5 docs, BMS-PROJ-GUI-007 top, quality 9/10
Status: [ ] Pass [ ] Fail
Time: ____ seconds
```

**If all 3 pass**: ✅ Ready to record  
**If any fail**: Troubleshoot before recording

---

## 📹 Recording Steps

### Before Recording
1. [ ] Run pre-recording tests (above)
2. [ ] Close unnecessary applications
3. [ ] Set browser zoom to 110%
4. [ ] Clear OpenWebUI chat history
5. [ ] Open screen recorder
6. [ ] Position OpenWebUI window (full screen or centered)
7. [ ] Take deep breath 😊

### During Recording
1. [ ] Start screen recording
2. [ ] Show OpenWebUI home screen (5 seconds)
3. [ ] Execute Scene 1: Introduction
4. [ ] Execute Scene 2: GDPR Search
5. [ ] Execute Scene 3: Procurement Forms
6. [ ] Execute Scene 4: Vendor Selection
7. [ ] Execute Scene 5: Summary
8. [ ] Stop recording

### After Recording
1. [ ] Save video as `videos/openwebui-demo-v1.mp4`
2. [ ] Review video (check audio/video quality)
3. [ ] Verify all queries shown clearly
4. [ ] Optional: Add captions or voiceover
5. [ ] Mark T032.3 complete
6. [ ] Proceed to T026 (POC signoff)

---

## 💡 Pro Tips

### For Best Results
1. **Rehearse once** - Run through all queries before recording
2. **Use new chat** - Start fresh to avoid context bleeding
3. **Slow down** - Give viewers time to read results
4. **Zoom in** - 110% browser zoom makes text readable
5. **Pause between queries** - 2-3 second pause shows results clearly

### If Recording Multiple Takes
- Save as: `openwebui-demo-v1.mp4`, `v2.mp4`, etc.
- Keep best take
- First take is often the best (natural)

### Voice Over vs Captions
- **Voice over**: More engaging, personal
- **Captions**: Less production time, works in silent mode
- **Both**: Professional, but more effort

### Length Guidelines
- **Too short** (<2 min): Feels rushed, missing context
- **Just right** (3-4 min): Perfect for stakeholder attention span
- **Too long** (>5 min): Loses audience, too detailed for POC

---

## 📊 Recording Checklist Summary

### Pre-Recording (30 min before)
- [ ] System health verified (API, Qdrant, OpenWebUI)
- [ ] Test queries executed successfully
- [ ] Recording software tested
- [ ] Browser prepared (zoom, tabs, chat cleared)

### Recording (3-5 minutes)
- [ ] Introduction shown
- [ ] GDPR search demonstrated
- [ ] Procurement search demonstrated
- [ ] Vendor selection demonstrated
- [ ] Summary displayed

### Post-Recording (10 minutes)
- [ ] Video saved to `videos/openwebui-demo-v1.mp4`
- [ ] Video reviewed for quality
- [ ] Captions/voiceover added (optional)
- [ ] Ready for T026 POC signoff

---

## 🎉 After Demo Recording

### Mark T032.3 Complete
Update `tasks.md`:
```markdown
- T032.3: Demo Video Production ✅ - Demo recorded at videos/openwebui-demo-v1.mp4
```

### Proceed to T026
With demo complete, you can:
1. Collect all POC evidence
2. Create `docs/poc-completion-report.md`
3. Obtain stakeholder signoff
4. **Graduate to MVP phase! 🎓**

---

## 📚 Reference Documents

- **Pre-Demo Test Checklist**: `docs/T032.3_PRE_DEMO_TEST.md` (369 lines)
- **Test Cases**: `tests/manual/retrieval-test-cases.md` (572 lines)
- **Test Results**: 11/15 passing (73.3%)
- **Known Limitations**: Documented in `docs/T032_COMPLETION_SUMMARY.md`

---

**Ready to Record?**

1. Run pre-recording tests (30 min before)
2. Follow demo script (3-5 min recording)
3. Review and save video
4. Mark T032.3 complete
5. Proceed to T026 for POC signoff! 🚀

---

**Recording Target**: 3-5 minutes  
**Difficulty**: Easy (system tested and ready)  
**Impact**: POC completion blocker → MVP transition  
**Estimated Total Time**: 1 hour (prep 30min + record 10min + review 20min)
