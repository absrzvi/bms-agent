# Specific Test Queries for Anlage 3F Case Study

Based on actual content extracted from the 513 indexed chunks.

## Hardware Specifications

### Power Supply & Electrical

```
What are the soft start circuit specifications for the inrush current limiter?
```

```
Find specifications for the galvanic isolated 250Watt power supply
```

```
What are the EN50155 compliance requirements for power supplies?
```

```
Tell me about supply interruption class S3 requirements
```

```
What fuses are compatible with the vehicle power system?
```

```
Find information about 10A/0.5ms fuse specifications
```

### CPU and Processing

```
What CPU is used in the 5G solution?
```

```
Find specifications for the 11th Generation Intel Xeon W-11555MRE processor
```

```
What are the CPU specifications: cores, cache, and frequency?
```

```
Tell me about the 6-core CPU with 64GB RAM configuration
```

```
What is the Intel RM590E chipset used for?
```

### Storage and Memory

```
What storage options are available in the system?
```

```
Find information about the external CFAST program storage
```

```
How much CFAST storage is provided? (expecting 64GB)
```

```
What RAM configuration is used in the updated solution?
```

## Rack Configuration

```
Describe the R5001C rack unit specifications
```

```
What is the form factor of the compact rack unit?
```

```
How can R5001C units be mounted in dual configuration?
```

```
What is the size specification: 3U, 4U, or other?
```

```
Can the system be mounted in standard 19-inch rack cabinets?
```

```
Tell me about confined cabinet mounting options
```

```
What is the 8HP CPCI-S.O formfactor specification?
```

## Wireless and Connectivity

### Modems and SIM Cards

```
How many internal WAN modems are supported?
```

```
What modem configurations are available: Minicard PCIe or M.2?
```

```
Tell me about MIMO configurations: 2x2 or 4x4?
```

```
How many SIM slots does the SIM farm module have?
```

```
Find specifications for the external replaceable SIM farm module
```

```
What are the embedded SIM (eUICC) capabilities?
```

```
How many 3FF MicroSim slots are provided?
```

### GNSS and GPS

```
What GNSS receiver specifications are included?
```

```
How many channels does the GNSS receiver support?
```

```
What satellite systems are supported: GPS, QZSS, etc.?
```

```
Find information about the 72-channel high sensitivity GNSS receiver
```

### Network Ports

```
What network port options are available on CPU blades?
```

```
Find information about 10GE ports on the front of CPU blades
```

```
What Ethernet connectivity is provided for landside servers?
```

```
Tell me about 10Gbps Ethernet connectivity requirements
```

## Software and Protocols

### Network Protocols

```
What is HTTP/3 used for in the solution?
```

```
Tell me about QUIC protocol implementation
```

```
How does HTTP/3 provide advanced congestion control?
```

```
What are the benefits of QUIC for mobile development?
```

```
Find information about TCP replacement with QUIC
```

### MQTT

```
Describe the MQTT client solution
```

```
What MQTT capabilities are implemented?
```

### Security Protocols

```
What SNMPv3 features are used for security?
```

```
How is user authentication handled in SNMPv3?
```

```
Which Nomad components use SNMPv3: CCU, Access Points?
```

```
Tell me about SNMP OID configuration in Zabbix
```

## Access Control and Authentication

### WiFi and RADIUS

```
How do users connect to the Staff SSID?
```

```
Describe the FreeRadius authentication process
```

```
What certificate-based authentication is used?
```

```
Explain the data flow between user device, Access Point, and CCU
```

```
How does RADIUS authentication work in the system?
```

### Security Management

```
What is the ISO/IEC 27001:2022 framework used for?
```

```
Describe the Information Security Management System (ISMS)
```

```
Tell me about supplier security audits by the QHSE team
```

```
What is the Security Scorecard Platform used for?
```

```
How are suppliers monitored for security compliance?
```

```
Describe the supplier approval process
```

## Monitoring and Management

### Nomad Insight

```
What fleet KPIs are tracked in the dashboard?
```

```
How is CCU uptime monitored?
```

```
What modem statistics are shown in Nomad Insight?
```

```
Tell me about CPU usage monitoring per train
```

```
How are SLA thresholds configured and monitored?
```

```
What custom alerts can users set?
```

### Incident Management

```
Describe the incident management process
```

```
What ITIL v4 best practices are implemented?
```

```
How are incidents tracked and reported?
```

```
Where are incident documents stored?
```

```
What access does OBB have to incident records?
```

## High Availability

```
What happens when a node fails in the system?
```

```
How long is the maximum downtime during component failure?
```

```
Describe the automatic component restart process
```

```
How is data integrity ensured during failures?
```

```
What redundant operation capabilities exist?
```

## Network Architecture

### Firewalling and NAT

```
How is traffic separated between diagnostic and management networks?
```

```
When does firewalling take place relative to NAT?
```

```
How is passenger traffic firewalled?
```

```
What servers can diagnostic network traffic reach?
```

### Traffic Management

```
What recommendations exist for user traffic throttling?
```

```
How is bandwidth allocation managed?
```

```
What happens when a user is throttled with available bandwidth?
```

## IOB Server Integration

```
How are additional IOB Servers (CCUs) integrated?
```

```
What scalability features support system growth?
```

```
Describe redundant operation support for CCUs
```

## Content Delivery and Portal

```
What features does the passenger portal have?
```

```
How are content blocks positioned on the portal?
```

```
Is the portal design responsive across devices?
```

```
What screen sizes are supported: smartphone, laptop, tablet?
```

```
Describe the user interface flow for passengers
```

## Cloud Data Center (CDC)

```
What dimensions are used for CDC resource planning?
```

```
What are the typical landside server resource requirements?
```

```
How much CPU and memory does a landside VM need?
```

```
What virtual machine specifications are required?
```

## Vulnerability Management

```
What vulnerability assessment processes are in place?
```

```
When does security testing occur: before deployment?
```

```
How is customer-specific configuration tested?
```

```
Where does testing occur: project test bench?
```

```
What firmware vulnerability assessments are performed?
```

## Domain Management

```
What domain allow and block list features exist?
```

```
How are universal lists configured?
```

```
Can allow/block lists be imported via CSV?
```

```
What are top-level domains (TLDs) used for?
```

```
How do universal lists span across multiple policies?
```

## Testing Combinations

### Multi-Topic Queries

```
How do power supply specifications and EN50155 compliance work together?
```

```
Describe the integration between GNSS receiver and modem configurations
```

```
What is the relationship between CPU specifications and rack form factor?
```

```
How do security protocols (SNMPv3) integrate with monitoring (Zabbix)?
```

```
Explain the connection between high availability and incident management
```

### Comparative Queries

```
What's the difference between 2x2 and 4x4 MIMO configurations?
```

```
Compare Minicard PCIe and M.2 modem options
```

```
What are the differences between diagnostic and management networks?
```

```
Compare HTTP/3 and TCP for web traffic
```

### Troubleshooting Queries

```
What happens if a CPU blade fails?
```

```
How do you troubleshoot modem connectivity issues?
```

```
What should be checked if authentication fails?
```

```
How do you diagnose network separation problems?
```

## Expected High-Score Queries (>0.6)

These should return excellent matches based on exact content:

```
Built-in soft start circuit active inrush current limiter vehicle fuses
```

```
6-core CPU 64GB RAM 11th Generation Intel Xeon W-11555MRE
```

```
External replaceable SIM farm module 12 MicroSim slots 6 embedded SIM
```

```
72 channel high sensitivity GNSS receiver GPS QZSS
```

```
ISO IEC 27001:2022 Information Security Management System ISMS
```

```
HTTP/3 QUIC protocol congestion control lower latency mobile
```

```
FreeRadius authentication Staff SSID certificate OEBB
```

```
R5001C 4U 19-inch rack dual configuration compact half size
```

## Query Testing Tips

1. **Use exact technical terms** from the document for best results
2. **Combine 3-4 keywords** for optimal retrieval
3. **Include model numbers** when searching for hardware specs
4. **Use protocol names** (HTTP/3, SNMPv3, QUIC) for networking queries
5. **Reference specific components** (CCU, Access Points, CPU blades)

## Verification Commands

Test all hardware queries:
```bash
for q in "soft start circuit" "Intel Xeon W-11555MRE" "72 channel GNSS" "R5001C rack"; do
  echo "Query: $q"
  curl -s -X POST http://localhost:8000/api/v1/search/semantic \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$q\", \"limit\": 1}" \
    | jq -r '.results[0] | "Score: \(.score) | \(.text[:100])"'
  echo ""
done
```

Test all security queries:
```bash
for q in "ISO 27001 ISMS" "SNMPv3 authentication" "Security Scorecard" "vulnerability assessment"; do
  echo "Query: $q"
  curl -s -X POST http://localhost:8000/api/v1/search/semantic \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$q\", \"limit\": 1}" \
    | jq -r '.results[0] | "Score: \(.score) | \(.text[:100])"'
  echo ""
done
```

---

**Total Queries:** 100+
**Categories:** 15
**Content Coverage:** Hardware, Software, Security, Networking, Management, Operations
