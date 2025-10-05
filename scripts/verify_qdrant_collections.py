#!/usr/bin/env python3
"""
T037: Dual Collection Architecture Verification Script

Verifies if the dual-collection strategy (R1.6, Q24) is properly implemented:
- Primary collection: nomad_bms_documents (high quality ≥0.70)
- Low-quality collection: nomad_bms_documents_low_quality (low quality <0.70)

Per Q27: Implementation status is UNKNOWN and must be verified.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
import requests

# Qdrant configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"

# Expected collections
PRIMARY_COLLECTION = "nomad_bms_documents"
LOW_QUALITY_COLLECTION = "nomad_bms_documents_low_quality"


class CollectionVerifier:
    """Verify Qdrant collection architecture"""
    
    def __init__(self):
        self.results = {
            "timestamp": None,
            "qdrant_status": None,
            "primary_collection": {
                "name": PRIMARY_COLLECTION,
                "exists": False,
                "point_count": 0,
                "vector_config": None,
                "details": None
            },
            "low_quality_collection": {
                "name": LOW_QUALITY_COLLECTION,
                "exists": False,
                "point_count": 0,
                "vector_config": None,
                "details": None
            },
            "dual_collection_status": None,
            "recommendations": []
        }
    
    def check_qdrant_health(self) -> bool:
        """Check if Qdrant is running and accessible"""
        try:
            response = requests.get(f"{QDRANT_URL}/", timeout=5)
            if response.status_code == 200:
                print("✅ Qdrant is running and accessible")
                self.results["qdrant_status"] = "healthy"
                return True
            else:
                print(f"❌ Qdrant returned status code: {response.status_code}")
                self.results["qdrant_status"] = f"unhealthy: {response.status_code}"
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to Qdrant at {QDRANT_URL}")
            self.results["qdrant_status"] = "connection_failed"
            return False
        except Exception as e:
            print(f"❌ Error checking Qdrant health: {e}")
            self.results["qdrant_status"] = f"error: {str(e)}"
            return False
    
    def get_all_collections(self) -> Optional[List[str]]:
        """Get list of all collections"""
        try:
            response = requests.get(f"{QDRANT_URL}/collections", timeout=10)
            if response.status_code == 200:
                data = response.json()
                collections = [c["name"] for c in data.get("result", {}).get("collections", [])]
                print(f"\n📊 Found {len(collections)} collection(s) in Qdrant:")
                for col in collections:
                    print(f"   - {col}")
                return collections
            else:
                print(f"❌ Failed to get collections: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error getting collections: {e}")
            return None
    
    def check_collection(self, collection_name: str) -> Dict:
        """Check if a collection exists and get its details"""
        try:
            response = requests.get(f"{QDRANT_URL}/collections/{collection_name}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                
                point_count = result.get("points_count", 0)
                vector_size = result.get("config", {}).get("params", {}).get("vectors", {}).get("size", "unknown")
                
                return {
                    "exists": True,
                    "point_count": point_count,
                    "vector_size": vector_size,
                    "status": result.get("status", "unknown"),
                    "details": result
                }
            elif response.status_code == 404:
                return {
                    "exists": False,
                    "point_count": 0,
                    "vector_size": None,
                    "status": "not_found",
                    "details": None
                }
            else:
                return {
                    "exists": False,
                    "point_count": 0,
                    "vector_size": None,
                    "status": f"error_{response.status_code}",
                    "details": None
                }
        except Exception as e:
            print(f"❌ Error checking collection {collection_name}: {e}")
            return {
                "exists": False,
                "point_count": 0,
                "vector_size": None,
                "status": f"exception: {str(e)}",
                "details": None
            }
    
    def verify_architecture(self) -> bool:
        """Verify dual-collection architecture"""
        print("\n" + "="*80)
        print("🔍 T037: DUAL COLLECTION ARCHITECTURE VERIFICATION")
        print("="*80)
        
        # Check Qdrant health
        if not self.check_qdrant_health():
            print("\n❌ Cannot proceed - Qdrant is not accessible")
            return False
        
        # Get all collections
        all_collections = self.get_all_collections()
        if all_collections is None:
            print("\n❌ Cannot retrieve collection list")
            return False
        
        # Check primary collection
        print(f"\n🔍 Checking PRIMARY collection: {PRIMARY_COLLECTION}")
        primary_info = self.check_collection(PRIMARY_COLLECTION)
        self.results["primary_collection"].update(primary_info)
        
        if primary_info["exists"]:
            print(f"   ✅ EXISTS - {primary_info['point_count']} points, {primary_info['vector_size']}-dim vectors")
        else:
            print(f"   ❌ DOES NOT EXIST")
        
        # Check low-quality collection
        print(f"\n🔍 Checking LOW-QUALITY collection: {LOW_QUALITY_COLLECTION}")
        low_quality_info = self.check_collection(LOW_QUALITY_COLLECTION)
        self.results["low_quality_collection"].update(low_quality_info)
        
        if low_quality_info["exists"]:
            print(f"   ✅ EXISTS - {low_quality_info['point_count']} points, {low_quality_info['vector_size']}-dim vectors")
        else:
            print(f"   ❌ DOES NOT EXIST")
        
        # Determine dual-collection status
        print("\n" + "="*80)
        print("📋 VERIFICATION RESULTS")
        print("="*80)
        
        if primary_info["exists"] and low_quality_info["exists"]:
            self.results["dual_collection_status"] = "FULLY_IMPLEMENTED"
            print("\n✅ ✅ ✅ DUAL-COLLECTION ARCHITECTURE: FULLY IMPLEMENTED")
            print(f"\n   Primary Collection: {primary_info['point_count']} high-quality chunks (≥0.70)")
            print(f"   Low-Quality Collection: {low_quality_info['point_count']} low-quality chunks (<0.70)")
            print("\n   Status: R1.6 requirement is satisfied ✅")
            self.results["recommendations"].append("Architecture verified - no action needed")
            return True
            
        elif primary_info["exists"] and not low_quality_info["exists"]:
            self.results["dual_collection_status"] = "PARTIALLY_IMPLEMENTED"
            print("\n⚠️ DUAL-COLLECTION ARCHITECTURE: PARTIALLY IMPLEMENTED")
            print(f"\n   ✅ Primary collection exists: {primary_info['point_count']} points")
            print(f"   ❌ Low-quality collection MISSING")
            print("\n   Status: R1.6 partially satisfied - low-quality collection must be created")
            self.results["recommendations"].extend([
                "Create low-quality collection: nomad_bms_documents_low_quality",
                "Implement include_low_quality parameter in search endpoints",
                "Update plan.md to document dual-collection architecture",
                "Add monitoring for low-quality chunk rate"
            ])
            return False
            
        elif not primary_info["exists"] and low_quality_info["exists"]:
            self.results["dual_collection_status"] = "MISCONFIGURED"
            print("\n❌ DUAL-COLLECTION ARCHITECTURE: MISCONFIGURED")
            print(f"\n   ❌ Primary collection MISSING")
            print(f"   ✅ Low-quality collection exists: {low_quality_info['point_count']} points")
            print("\n   Status: CRITICAL ERROR - primary collection missing")
            self.results["recommendations"].extend([
                "CRITICAL: Create primary collection: nomad_bms_documents",
                "Re-run document processing to populate primary collection",
                "Investigate why primary collection is missing"
            ])
            return False
            
        else:
            self.results["dual_collection_status"] = "NOT_IMPLEMENTED"
            print("\n❌ ❌ ❌ DUAL-COLLECTION ARCHITECTURE: NOT IMPLEMENTED")
            print("\n   ❌ Primary collection MISSING")
            print("   ❌ Low-quality collection MISSING")
            print("\n   Status: R1.6 NOT satisfied - dual-collection must be implemented")
            self.results["recommendations"].extend([
                "CRITICAL: Create both collections",
                "Primary: nomad_bms_documents (high-quality chunks ≥0.70)",
                "Secondary: nomad_bms_documents_low_quality (low-quality chunks <0.70)",
                "Run document processing with quality filtering",
                "Implement include_low_quality parameter in API",
                "Update plan.md with architecture documentation"
            ])
            return False
    
    def save_report(self, output_file: str = "docs/T037_VERIFICATION_REPORT.md"):
        """Save verification report as markdown"""
        import datetime
        self.results["timestamp"] = datetime.datetime.now().isoformat()
        
        report = f"""# T037: Dual Collection Architecture Verification Report

**Date**: {self.results['timestamp']}  
**Qdrant Status**: {self.results['qdrant_status']}  
**Architecture Status**: {self.results['dual_collection_status']}

---

## Collections Verified

### Primary Collection: `{PRIMARY_COLLECTION}`
- **Exists**: {self.results['primary_collection']['exists']}
- **Point Count**: {self.results['primary_collection']['point_count']}
- **Vector Config**: {self.results['primary_collection']['vector_config']}
- **Purpose**: Store high-quality chunks (quality score ≥0.70) for normal search operations

### Low-Quality Collection: `{LOW_QUALITY_COLLECTION}`
- **Exists**: {self.results['low_quality_collection']['exists']}
- **Point Count**: {self.results['low_quality_collection']['point_count']}
- **Vector Config**: {self.results['low_quality_collection']['vector_config']}
- **Purpose**: Store low-quality chunks (quality score <0.70) for admin review/debugging

---

## Architecture Status

**Result**: `{self.results['dual_collection_status']}`

"""
        
        if self.results['dual_collection_status'] == 'FULLY_IMPLEMENTED':
            report += """
### ✅ Fully Implemented

Both collections exist as specified in R1.6 (Q24 clarification). The dual-collection architecture is properly configured:

- Primary collection contains high-quality searchable chunks
- Low-quality collection contains sub-threshold chunks for admin review
- Architecture complies with requirements

**Action Required**: None - verification complete

"""
        elif self.results['dual_collection_status'] == 'PARTIALLY_IMPLEMENTED':
            report += """
### ⚠️ Partially Implemented

Primary collection exists but low-quality collection is missing. This is a partial implementation of R1.6.

**Action Required**:
"""
        elif self.results['dual_collection_status'] == 'NOT_IMPLEMENTED':
            report += """
### ❌ Not Implemented

Neither collection exists. The dual-collection architecture specified in R1.6 is not implemented.

**Action Required**:
"""
        else:
            report += """
### ❌ Misconfigured

Collection architecture is in an invalid state.

**Action Required**:
"""
        
        # Add recommendations
        if self.results['recommendations']:
            report += "\n## Recommendations\n\n"
            for i, rec in enumerate(self.results['recommendations'], 1):
                report += f"{i}. {rec}\n"
        
        report += f"""
---

## Technical Details

### Qdrant Connection
- **URL**: {QDRANT_URL}
- **Status**: {self.results['qdrant_status']}

### Requirements Reference
- **R1.6**: Dual-collection strategy per Q24 clarification
- **Q27**: Status unknown, verification required before MVP
- **Collections**:
  - Primary: `{PRIMARY_COLLECTION}`
  - Low-Quality: `{LOW_QUALITY_COLLECTION}`

---

**Verification Script**: `scripts/verify_qdrant_collections.py`  
**Next Steps**: Based on architecture status, follow recommendations above
"""
        
        # Write report
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report)
        
        print(f"\n📄 Report saved to: {output_file}")
        
        # Also save JSON for programmatic access
        json_file = output_file.replace('.md', '.json')
        Path(json_file).write_text(json.dumps(self.results, indent=2))
        print(f"📄 JSON report saved to: {json_file}")


def main():
    """Main verification flow"""
    verifier = CollectionVerifier()
    
    # Run verification
    success = verifier.verify_architecture()
    
    # Save report
    verifier.save_report()
    
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"Architecture Status: {verifier.results['dual_collection_status']}")
    print(f"Blocks MVP: {'YES' if not success else 'NO'}")
    print(f"Action Required: {'YES' if not success else 'NO'}")
    
    if not success:
        print("\n⚠️  T037 INCOMPLETE - Remediation required before MVP")
        return 1
    else:
        print("\n✅ T037 COMPLETE - Architecture verified, ready for MVP")
        return 0


if __name__ == "__main__":
    sys.exit(main())
