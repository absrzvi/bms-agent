# BMS Agent Performance Testing Plan

**Created**: 2025-10-05  
**Purpose**: Monitor system performance during OpenWebUI queries  
**Components**: OpenWebUI, Ollama (mistral-nemo), Qdrant, BMS API

---

## 🎯 Test Objectives

1. **Baseline Performance**: Measure resource usage at idle and during queries
2. **Query Performance**: Track response times for different query types
3. **System Load**: Identify bottlenecks (CPU, RAM, I/O)
4. **Service Performance**: Monitor individual service resource usage
5. **Scalability**: Test behavior under different query complexities

---

## 🔧 Test Setup

### Prerequisites
- All services running: OpenWebUI, Ollama, Qdrant, BMS API
- Monitor script ready: `/workspace/001-bms-agent/scripts/monitor_performance.py`
- Clean system state (no other heavy processes)

### Monitoring Configuration
- **Capture Interval**: 1 second (default)
- **Metrics Tracked**:
  - System: CPU %, Memory %, Disk usage
  - OpenWebUI: Process CPU/RAM
  - Ollama: Process CPU/RAM, API status
  - Qdrant: Process CPU/RAM, collection stats
  - BMS API: Process CPU/RAM, health status

---

## 📋 Test Scenarios

### Test 1: Idle Baseline (30 seconds)
**Purpose**: Establish baseline resource usage

**Steps**:
1. Start monitoring
2. Wait 30 seconds (no queries)
3. Stop monitoring

**Expected**:
- Low CPU (<10%)
- Stable RAM usage
- All services responsive

---

### Test 2: Simple Document Lookup (Single Query)
**Purpose**: Measure single query performance

**Query**: `Show me GDPR compliance documents`

**Steps**:
1. Start monitoring
2. Wait 5s (baseline)
3. Submit query in OpenWebUI
4. Wait for complete response
5. Wait 10s (cooldown)
6. Stop monitoring

**Expected**:
- CPU spike during LLM inference
- Response time: 5-15 seconds
- RAM increase during query processing

---

### Test 3: Complex Multi-Document Query
**Purpose**: Test performance with comprehensive searches

**Query**: `Compare procurement procedures across ENGI, QHSE, and PROJ departments`

**Steps**:
1. Start monitoring
2. Wait 5s (baseline)
3. Submit query
4. Wait for complete response
5. Wait 10s (cooldown)
6. Stop monitoring

**Expected**:
- Higher CPU load (multi-document synthesis)
- Longer response time: 10-20 seconds
- Qdrant query activity

---

### Test 4: Conversational Session (3 Queries)
**Purpose**: Test performance during multi-turn conversation

**Queries**:
1. `What is the sick leave policy?`
2. `What form do I need?`
3. `How do I submit it?`

**Steps**:
1. Start monitoring
2. Submit query 1, wait for response
3. Submit query 2, wait for response
4. Submit query 3, wait for response
5. Wait 10s (cooldown)
6. Stop monitoring

**Expected**:
- Consistent performance across queries
- Session context maintained
- No memory leaks

---

### Test 5: Rapid Fire Queries (5 Quick Queries)
**Purpose**: Test system under load

**Queries**:
1. `Show me GDPR docs`
2. `Find procurement forms`
3. `What is BMS-HUMR-FOR-029?`
4. `Show safety procedures`
5. `Find engineering standards`

**Steps**:
1. Start monitoring
2. Submit queries back-to-back (minimal wait)
3. Wait for all responses
4. Wait 15s (cooldown)
5. Stop monitoring

**Expected**:
- High CPU during burst
- Potential queuing behavior
- System remains responsive

---

### Test 6: Ambiguous Query Handling
**Purpose**: Test performance when LLM needs to search broadly

**Query**: `I want to start a new project, what should I do?`

**Steps**:
1. Start monitoring
2. Submit query
3. Wait for response
4. Wait 10s (cooldown)
5. Stop monitoring

**Expected**:
- LLM should call search_smart
- Similar performance to Test 2
- Multiple search attempts possible

---

## 📊 Metrics to Capture

### System Metrics
- **CPU Usage**: Average, Peak, Minimum
- **Memory Usage**: Average, Peak, Available
- **Disk I/O**: Read/Write activity

### Process Metrics (Per Service)
- **CPU %**: Per-process CPU usage
- **RAM MB**: Memory consumption
- **Status**: Running/Not running

### Query Metrics (Manual Recording)
- **Response Time**: Time from submit to complete response
- **Tool Calls**: Number of search function calls
- **Results Count**: Number of documents retrieved
- **Error Rate**: Any failures or issues

---

## 🚀 Quick Start Commands

### Start Monitoring
```bash
python3 /workspace/001-bms-agent/scripts/monitor_performance.py
```

**Options**:
- Default: 1-second interval
- Custom interval: `python3 monitor_performance.py 0.5` (500ms)

### Stop Monitoring
- Press **Ctrl+C**
- Results auto-saved to `/workspace/001-bms-agent/logs/performance/`

### Analyze Results
```bash
# Single session
python3 /workspace/001-bms-agent/scripts/analyze_performance.py logs/performance/session_YYYYMMDD_HHMMSS.json

# Compare multiple sessions
python3 /workspace/001-bms-agent/scripts/analyze_performance.py logs/performance/*.json
```

---

## 📝 Recording Template

Use this template to record manual observations:

```
Test: [Test Name]
Date: [YYYY-MM-DD HH:MM]
Session ID: [from monitor output]

Query: "[exact query text]"

Observations:
- Response Time: [X] seconds
- Tool Called: [function name]
- Results: [N] documents
- User Experience: [smooth/laggy/error]
- Visual: [formatting correct? stars/percentages visible?]

Issues:
- [any problems observed]

Notes:
- [additional comments]
```

---

## 🎯 Success Criteria

### Performance Targets
- ✅ **Response Time**: <15 seconds for simple queries
- ✅ **CPU Average**: <50% during queries
- ✅ **Memory**: No leaks (stable after cooldown)
- ✅ **System Stability**: No crashes or freezes

### Quality Targets
- ✅ **Tool Usage**: LLM calls search functions
- ✅ **Formatting**: Stars, percentages, emojis visible
- ✅ **Citations**: Inline [1], [2], [3] present
- ✅ **Workflow**: Step 1, Step 2, Step 3 shown

---

## 🔍 Troubleshooting

### High CPU Usage
- **Cause**: Ollama model inference
- **Solution**: Normal during query, should drop after

### High Memory Usage
- **Cause**: Model loaded in RAM, vector cache
- **Solution**: Monitor for leaks, restart if growing

### Slow Responses
- **Cause**: Large result sets, complex synthesis
- **Solution**: Check Qdrant query time, reduce limit parameter

### Tool Not Called
- **Cause**: System prompt issue
- **Solution**: Verify prompt v3.1 loaded, check examples

---

## 📦 Output Files

### Monitoring Session
```
/workspace/001-bms-agent/logs/performance/session_YYYYMMDD_HHMMSS.json
```

**Contains**:
- All performance snapshots (1/second)
- Summary statistics
- Peak load periods
- Service status history

### Analysis Output
Printed to console, includes:
- Duration and snapshot count
- System performance (CPU/RAM avg/peak)
- Process performance (per service)
- Peak load analysis
- Performance rating
- Recommendations

---

## 🎬 Ready to Test?

**Pre-Test Checklist**:
- [ ] All services running (OpenWebUI, Ollama, Qdrant, BMS API)
- [ ] Monitor script tested and ready
- [ ] OpenWebUI browser tab open
- [ ] Recording template prepared
- [ ] System in clean state (no other heavy processes)

**To Begin**:
1. Open terminal
2. Run: `python3 /workspace/001-bms-agent/scripts/monitor_performance.py`
3. Wait for status check
4. When ready, submit your query in OpenWebUI
5. Observe metrics in terminal
6. Press Ctrl+C when done
7. Review analysis output

---

**Ready when you are!** 🚀
