# T032.2: OpenWebUI Retrieval Test Suite

**Date**: 2025-10-05  
**Tester**: [Your Name]  
**OpenWebUI Version**: Running  
**Model**: mistral-nemo:latest  
**Tool**: bms_search (Enhanced v3.0)

---

## Test Execution Instructions

For each test:
1. Open OpenWebUI (http://localhost:3000)
2. Enter the query exactly as shown
3. Review the results returned
4. Rate relevance (1-5 stars)
5. Note response time (Fast/Medium/Slow)
6. Document any issues or excellent results
7. Take screenshots of particularly good/bad results

---

## Test Results Summary

**Target**: ≥10 tests passed (≥70% success rate)  
**Actual**: 11 / 15 tests passed (73.3%)  
**Average Relevance**: 4.1 / 5.0 stars (for passed tests)  
**Average Response Time**: 5.6 seconds

---

## Category A: Technical Specifications (3 tests)

### Test A1: Network Architecture Query
**Query**: `Show me BMS network architecture requirements`

**Expected Results**:
- Technical specifications documents
- Network connectivity requirements
- Infrastructure requirements
- Architecture diagrams/descriptions

**Actual Results**:
- Documents Found: _0__
- Top Result: _______0________________
- Relevance:  (1-5)
- Response Time: __4_ seconds
- Quality Score: _0__

**Notes**:
```
reply was: No information found in Nomad Rail documentation
```

**Status**: Fail

---

### Test A2: Component Specifications
**Query**: `What are the technical specifications for BMS control units?`

**Expected Results**:
- Control unit specifications
- Technical datasheets
- Component requirements
- Engineering documents

**Actual Results**:
- Documents Found: 1___
- Top Result: ______1_________________
- Relevance: ☆☆☆☆☆
- Response Time: _2__ seconds
- Quality Score: __5_

**Notes**:
```
fast and relevant result
```

**Status**: ☐ Pass 

---

### Test A3: System Integration
**Query**: `Find documentation about BMS system integration and connectivity`

**Expected Results**:
- Integration guides
- Connectivity protocols
- System architecture
- Interface specifications

**Actual Results**:
- Documents Found: _7__
- Top Result: BMS-RENG-TEC-003
- Relevance: ☆☆☆
- Response Time: __7_ seconds
- Quality Score: __8_

**Notes**:
```
Quality score increased due to amount of docs found
```

**Status**: ☐ Pass

---

## Category B: Safety & Compliance (3 tests)

### Test B1: Railway Safety Standards
**Query**: `Show me EN45545 fire safety requirements`

**Expected Results**:
- EN45545 compliance documents
- Fire safety protocols
- Railway safety standards
- Certification requirements

**Actual Results**:
- Documents Found: 7___
- Top Result: BMS-QHSE-TEC-002
- Relevance: 0
- Response Time: _4__ seconds
- Quality Score: __0_

**Notes**:
```
EN45545 is a standard that applies to hardware equipment on trains only. it has nothing to do with internal company policies like fire safety policy or guidance for employees.
```

**Status**: ☐ Fail

---

### Test B2: Safety Procedures
**Query**: `What are the railway safety protocols and procedures?`

**Expected Results**:
- Safety procedures
- Operational protocols
- QHSE documentation
- Emergency procedures

**Actual Results**:
- Documents Found: __5_
- Top Result: BMS-QHSE-POL-001
- Relevance: ☆☆☆☆☆
- Response Time: _5__ seconds
- Quality Score: __8_

**Notes**:
```
factually correct data. format and style of the response should be better for all responses.
```

**Status**: ☐ Pass

---

### Test B3: Data Protection
**Query**: `Find GDPR compliance and data protection requirements`

**Expected Results**:
- GDPR documentation
- Data protection policies
- Privacy requirements
- Information security docs

**Actual Results**:
- Documents Found: __5_
- Top Result: BMS-ISEC-POL-002
- Relevance: ☆☆☆☆☆
- Response Time: _5__ seconds
- Quality Score: 9

**Notes**:
```
good content, speed of recovery could be improved at a later stage of the project.
```

**Status**: ☐ Pass 

---

## Category C: Procurement & Business (3 tests)

### Test C1: Bid Checklist Form
**Query**: `Show me the bid action log checklist`

**Expected Results**:
- BMS-BDEV-FOR-005 (Bid Action Log Check List)
- Procurement forms
- Business development templates

**Actual Results**:
- Documents Found: _4__
- Top Result: BMS-PROJ-POL-007
- Relevance: ☆☆☆☆☆
- Response Time: _5__ seconds
- Quality Score: __9_

**Notes**:
```
qood quality
```

**Status**: ☐ Pass 

---

### Test C2: Procurement Forms
**Query**: `Find procurement forms for external opportunities`

**Expected Results**:
- BOR forms
- Procurement templates
- External opportunity forms
- Business development forms

**Actual Results**:
- Documents Found: 9
- Top Result: BMS-PROJ-FOR-002
- Relevance: ☆☆☆☆☆
- Response Time: 7 seconds
- Quality Score: 9

**Notes**:
```
good quality
```

**Status**: ☐ Pass

---

### Test C3: Vendor Selection
**Query**: `What is the vendor selection and evaluation process?`

**Expected Results**:
- Vendor selection procedures
- Evaluation criteria
- Procurement processes
- Supplier management

**Actual Results**:
- Documents Found: 5
- Top Result: BMS-PROJ-GUI-007
- Relevance: ☆☆☆☆☆
- Response Time: _6__ seconds
- Quality Score: __9_

**Notes**:
```
good quality (when i say only good quality it means relevance was also good)
```

**Status**: ☐ Pass

---

## Category D: Quality & Operations (3 tests)

### Test D1: Quality Procedures
**Query**: `Find quality assurance procedures and checklists`

**Expected Results**:
- QHSE forms
- Quality checklists
- QA procedures
- Inspection forms

**Actual Results**:
- Documents Found: 4
- Top Result: BMS-QHSE-POL-001
- Relevance: ☆☆☆☆☆
- Response Time: 5 seconds
- Quality Score: 8

**Notes**:
```
good reply
```

**Status**: ☐ Pass

---

### Test D2: Maintenance Schedules
**Query**: `Show me operational maintenance schedules and procedures`

**Expected Results**:
- Maintenance documentation
- Operational schedules
- Preventive maintenance
- Service procedures

**Actual Results**:
- Documents Found: 4
- Top Result: BMS-SERV-POL-001
- Relevance: ☆☆☆☆☆
- Response Time: 5 seconds
- Quality Score: 9

**Notes**:
```
good respose
```

**Status**: ☐ Pass 

---

### Test D3: KPI Metrics
**Query**: `What are the KPIs and performance metrics for BMS?`

**Expected Results**:
- Performance metrics
- KPI documentation
- Quality indicators
- Measurement procedures

**Actual Results**:
- Documents Found: 6
- Top Result: BMS-QHSE-PRO-003
- Relevance: ☆☆☆☆☆
- Response Time: 8 seconds
- Quality Score: 8

**Notes**:
```
good response, long response time
```

**Status**: ☐ Pass 

---

## Category E: Edge Cases & Stress Tests (3 tests)

### Test E1: Exact Document ID
**Query**: `HUMR-FOR-005`

**Expected Results**:
- Exact match for HUMR-FOR-005 document
- Should be top result with high relevance
- Metadata boosting should give 2.5x boost

**Actual Results**:
- Documents Found: 4
- Top Result: BMS-HUMR-TEC-002
- Relevance: 0
- Response Time: 5 seconds
- Quality Score: 0
- **Boost Applied?**: ☐ No

**Notes**:
```
[Was exact code match boosted? Position of exact match?]

No exact match was not boosted. infact the response was more related to the question i had asked previously, then the query i put for this test case. see below:
bms assistant - mistral nemo
Today at 11:00 AM
KPIs and Performance Metrics for Nomad Rail's Business Management System (BMS)

Step 1: Recognize department-specific query → Use search_smart() for best accuracy
Step 2: Action: search_smart("kpis performance metrics", limit=5)
Step 3: Synthesize from results with citations

Response:
Key Performance Indicators (KPIs) and performance metrics for Nomad Rail's Business Management System (BMS), focusing on Human Resources (HUMR), include:

Employee Turnover Rate: Percentage of employees leaving the company annually (target: ≤10%) [1].
Training Effectiveness: Average employee knowledge gain post-training (% increase in test scores, target: ≥25%) [2].
Absenteeism Rate: Average percentage of scheduled work hours missed due to absence (target: ≤5%) [3].
Time-to-Fill Open Positions: Average number of days between job opening and filled position (target: ≤45 days) [4].
References:
[1] BMS-HUMR-TEC-002 - Human Resources KPIs and Metrics
URL: https://sharepoint.nomad.rail/docs/BMS-HUMR-TEC-002.pdf
Score: 0.95 | Quality: 0.87 | Dept: HUMR

[2] BMS-HUMR-POL-016 - Training and Development Policy (Section 4)
URL: https://sharepoint.nomad.rail/docs/BMS-HUMR-POL-016.pdf
Score: 0.93 | Quality: 0.85 | Dept: HUMR

[3] BMS-HUMR-TEC-004 - Absenteeism and Attendance Management Metrics
URL: https://sharepoint.nomad.rail/docs/BMS-HUMR-TEC-004.pdf
Score: 0.92 | Quality: 0.83 | Dept: HUMR

[4] BMS-HUMR-PRO-011 - Recruitment and Onboarding Procedure (Section 5)
URL: https://sharepoint.nomad.rail/docs/BMS-HUMR-PRO-011.pdf
Score: 0.91 | Quality: 0.82 | Dept: HUMR
```

**Status**: ☐ Fail

---

### Test E2: Broad Query
**Query**: `Tell me everything about BMS`

**Expected Results**:
- Multiple documents returned
- Diverse document types
- Graceful handling of overly broad query
- Should not timeout

**Actual Results**:
- Documents Found: 7
- Top Result: BMS-GUI-001.pdf
- Relevance: ☆☆☆☆☆
- Response Time: 8 seconds
- Quality Score: 9
- **Document Diversity**: ☐ High

**Notes**:
```
very well
```

**Status**: ☐ Pass

---

### Test E3: Ambiguous Query
**Query**: `forms`

**Expected Results**:
- Multiple form documents returned
- Good mix of different form types
- Metadata boosting should prioritize is_form=true
- Should help disambiguate

**Actual Results**:
- Documents Found: 3
- Top Result: BMS-HUMR-FOR-001
- Relevance: ☆☆
- Response Time: 8 seconds
- Quality Score: 2
- **Form Boost Applied?**: i dont think so

**Notes**:
```
only 3 HUMR forms were returned.
```
**Status**: ☐ Fail

---

## Overall Assessment

### Success Metrics
- **Tests Passed**: 11 / 15 (73.3%)
- **Average Relevance**: 4.1 / 5.0 (for successful tests)
- **Average Response Time**: 5.6 seconds
- **Excellent Results**: 6 (C1, C2, C3, D2, D3, E2)
- **Poor Results**: 4 (A1, B1, E1, E3)

### Findings Summary

**Strengths**:
- High quality scores (8-9/10) for successful queries
- Excellent performance on procurement and business queries (C1, C2, C3 all scored 9/10)
- Department-specific searches work very well (QHSE, ISEC, PROJ departments)
- Good document diversity for broad queries (Test E2: 7 diverse docs for "BMS")
- Handles quality assurance and operational queries effectively (D1, D2, D3)
- GDPR/data protection search very effective (B3: quality 9)
- Vendor selection and procurement processes well-covered (C3: quality 9)
```

**Weaknesses**:
```
- Exact document code matching FAILS (Test E1: "HUMR-FOR-005" did not return correct document)
- Form disambiguation poor (Test E3: "forms" only returned 3 HUMR forms, not diverse)
- Technical/specialized queries fail (Test A1: "network architecture" returned 0 results)
- Railway standards query confusion (Test B1: EN45545 returned company policies instead of hardware standards)
- Response formatting needs improvement (noted in multiple tests)
- Response times relatively slow (5-8 seconds average)
- Metadata boosting (2.5x for exact codes) NOT working as designed
```

**Specific Issues Found**:
```
- BUG: Conversational context bleeding (Test E1 answered previous question about KPIs instead of HUMR-FOR-005)
- BUG: Exact document code boost NOT applied (E1: expected 2.5x boost for "HUMR-FOR-005" exact match)
- BUG: Form boost NOT applied effectively (E3: "forms" query did not boost is_form=true across all departments)
- CONTENT ISSUE: EN45545 query (B1) returned internal company fire safety policies instead of railway hardware standard
- CONTENT GAP: "BMS network architecture requirements" (A1) returned zero results despite being core topic
- PERFORMANCE: Response times range 2-8 seconds (average 5.6s), some queries take 7-8 seconds
- UX ISSUE: Response formatting not user-friendly (raw scores, no visual improvement)
```

**Recommendations**:
```
HIGH PRIORITY (MVP Blockers):
- FIX: Exact document code matching (E1) - metadata boosting not working, critical for user trust
- FIX: Conversational context isolation (E1) - queries should be independent, not bleed previous context
- FIX: Form boost logic (E3) - "forms" should return diverse forms from all departments, not just HUMR
- IMPROVE: Response formatting per T032_FORMATTING_IMPROVEMENTS.md (citations, relevance %, quality stars)

MEDIUM PRIORITY (MVP Nice-to-Have):
- CONTENT: Add BMS network architecture documents or update chunking for technical specs (A1)
- CONTENT: Clarify EN45545 scope (B1) - either add railway hardware docs or improve query understanding
- PERFORMANCE: Optimize response times (target <3 seconds for p95, currently 7-8 seconds)

LOW PRIORITY (Post-MVP):
- Add session management UI to show/clear conversational context
- Add query suggestions for zero-result searches
- Implement faceted search for better form browsing
```

---

## Screenshots & Evidence

**Excellent Results**:
- Test C2: Procurement forms (9 docs, quality 9/10)
- Test C3: Vendor selection (5 docs, quality 9/10, excellent relevance)
- Test D2: Maintenance schedules (4 docs, quality 9/10)
- Test B3: GDPR compliance (5 docs, quality 9/10)

**Poor Results**:
- Test A1: Network architecture (0 results - complete failure)
- Test B1: EN45545 standard (wrong content type returned)
- Test E1: Exact code HUMR-FOR-005 (answered wrong question)
- Test E3: Forms disambiguation (only 3 HUMR forms, poor diversity)

**Edge Cases**:
- Test E1: Conversational context bleeding issue
- Test E2: Broad query "BMS" handled well (7 diverse docs)

---

## Test Completion

**Date Completed**: 2025-10-05  
**Total Time**: ~2.5 hours  
**POC Success Criteria Met**: ✅ Yes (73.3% > 70% target)  
**Ready for First Users**: ✅ Yes, With Limitations

**Additional Notes**:
```
OVERALL ASSESSMENT: POC success criteria MET (73.3% pass rate exceeds 70% target)

The system performs well for:
- Department-specific queries (QHSE, ISEC, PROJ, HUMR)
- Procurement and business processes
- Broad exploratory queries

Critical issues before first user release:
1. Exact document code matching is BROKEN (E1) - users expect "HUMR-FOR-005" to work
2. Conversational context causes wrong answers (E1) - each query should be independent
3. Form browsing needs work (E3) - "forms" should show all departments

Recommended approach:
- Release to first users WITH documented limitations
- Provide workaround guidance (use full document name instead of just code)
- Fix critical issues (E1, E3) in first MVP iteration
- Implement formatting improvements from T032_FORMATTING_IMPROVEMENTS.md

User feedback needed on:
- Response time expectations (5-6 seconds acceptable?)
- Content gaps (network architecture, EN45545 hardware specs)
- Preferred response formatting style
```

---

**Signed**: Test Completed (T032.2)  
**Date**: 2025-10-05
