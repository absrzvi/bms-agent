# Performance Monitoring - Quick Reference

## 🎯 Currently Running

**Monitor Status**: ✅ ACTIVE (PID: 53558)

Performance monitoring is currently capturing system metrics every 1 second.

---

## 📊 What's Being Monitored

- **System**: CPU %, Memory %, Disk usage
- **OpenWebUI**: Process CPU/RAM usage
- **Ollama**: Process CPU/RAM + API status
- **Qdrant**: Process CPU/RAM + collection stats  
- **BMS API**: Health status

---

## 🛑 Stop Monitoring

To stop and save results:

```bash
# Find the monitor process
ps aux | grep monitor_performance

# Kill it (replace PID)
kill 53558

# Or use killall
killall -INT python3
```

Results will auto-save to this directory.

---

## 📈 View Results

After stopping:

```bash
# Analyze the latest session
python3 /workspace/001-bms-agent/scripts/analyze_performance.py logs/performance/session_*.json

# Compare multiple sessions
python3 /workspace/001-bms-agent/scripts/analyze_performance.py logs/performance/*.json
```

---

## 🔄 Restart Monitoring

```bash
python3 /workspace/001-bms-agent/scripts/monitor_performance.py
```

---

## 📝 Test Scenarios

See: `/workspace/001-bms-agent/docs/PERFORMANCE_TEST_PLAN.md`

Recommended queries to test:
1. Simple: `Show me GDPR compliance documents`
2. Complex: `Compare procurement procedures across departments`
3. Conversational: Multiple related queries
4. Ambiguous: `I want to start a new project`

---

**Monitoring active - submit your query now!** 🚀
