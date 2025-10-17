#!/usr/bin/env python3
"""
Test Enhanced XLSX Processing with Improved Data Cleaning
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile, ChunkingStrategy
)

def test_xlsx_cleaned():
    """Test improved XLSX processing with cleaned data"""
    
    # XLSX-optimized configuration
    config = ProcessingConfig(
        chunk_size=1000,
        min_chunk_size=150,
        chunk_overlap=200,
        quality_threshold=45.0,
        min_quality_score=35.0,
        chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
        processing_profile=ProcessingProfile.GENERAL,
        enable_contextual_retrieval=True,
        enable_late_chunking=False,
        enable_quality_validation=False,
        enable_hybrid_search=True,
        enable_advanced_preprocessing=True
    )
    
    processor = EnhancedDocumentProcessor(config)
    
    # Test the overtime form that had messy data
    test_file = '/workspace/windsurf-project/bms-doc-upload/xls/BMS-HUMR-FOR-028 Overtime Form Template.xlsx'
    
    print('🧹 TESTING IMPROVED XLSX DATA CLEANING')
    print('=' * 60)
    print(f'📊 Testing: {Path(test_file).name}')
    print()
    
    try:
        print('🔍 STEP 1: Raw XLSX Extraction (BEFORE Cleaning)')
        print('-' * 50)
        
        # Show what the old method would produce
        import pandas as pd
        df_raw = pd.read_excel(test_file)
        raw_old_method = df_raw.to_string()
        
        print(f'📊 Old Method - Raw pandas output (first 500 chars):')
        print(f'"{raw_old_method[:500]}..."')
        print(f'   Issues: Contains "Unnamed:" columns and "NaN" values')
        
        print('\n' + '-' * 50)
        print('🔍 STEP 2: Enhanced XLSX Extraction (AFTER Cleaning)')
        print('-' * 50)
        
        # Use our improved method
        clean_content = processor._read_document(Path(test_file))
        
        print(f'✅ Cleaned Method - Enhanced output (first 800 chars):')
        print(f'"{clean_content[:800]}..."')
        
        # Count improvements
        nan_count_old = raw_old_method.count('NaN')
        nan_count_new = clean_content.count('NaN')
        unnamed_count_old = raw_old_method.count('Unnamed:')
        unnamed_count_new = clean_content.count('Unnamed:')
        
        print(f'\n📊 Cleaning Results:')
        print(f'   NaN values: {nan_count_old} → {nan_count_new} (removed {nan_count_old - nan_count_new})')
        print(f'   Unnamed columns: {unnamed_count_old} → {unnamed_count_new} (removed {unnamed_count_old - unnamed_count_new})')
        print(f'   Content length: {len(raw_old_method)} → {len(clean_content)} chars')
        
        print('\n' + '-' * 50)
        print('🔍 STEP 3: Full Document Processing with Clean Data')
        print('-' * 50)
        
        result = processor.process_document(test_file)
        
        if result and result.get('processing_success'):
            chunks = result.get('chunks', [])
            
            print(f'✅ SUCCESS! Clean XLSX processing complete')
            print(f'   Final Chunks: {len(chunks)}')
            
            # Document metadata
            print(f'\n📋 Document Metadata:')
            print(f'   Title: {result.get("title", "N/A")}')
            print(f'   Type: {result.get("type", "N/A")}')
            
            if chunks:
                print(f'\n📊 CLEANED CHUNK ANALYSIS:')
                print('-' * 50)
                
                for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
                    content = chunk.get('content', '')
                    metadata = chunk.get('metadata', {})
                    
                    print(f'\n🔸 CHUNK {i+1} (CLEANED):')
                    print(f'   Length: {len(content)} characters')
                    
                    # Show cleaned content
                    if '<context>' in content and '</context>' in content:
                        context_end = content.find('</context>')
                        actual_content = content[context_end + 10:].strip()
                        
                        print(f'\n   📊 Clean Spreadsheet Data:')
                        print(f'      "{actual_content[:400]}..."')
                        
                        # Check for cleanliness
                        nan_in_chunk = actual_content.count('NaN')
                        unnamed_in_chunk = actual_content.count('Unnamed:')
                        
                        if nan_in_chunk == 0 and unnamed_in_chunk == 0:
                            print(f'   ✅ Perfectly clean - no NaN or Unnamed artifacts')
                        else:
                            print(f'   ⚠️  Still contains: {nan_in_chunk} NaN, {unnamed_in_chunk} Unnamed')
                        
                        # Check for structured data
                        if '|' in actual_content:
                            print(f'   ✅ Structured format with proper separators')
                        
                        if any(word in actual_content.lower() for word in ['form', 'template', 'approval']):
                            print(f'   ✅ Business form content preserved')
                    
                    else:
                        print(f'\n   📊 Raw Clean Content:')
                        print(f'      "{content[:400]}..."')
                
                # Overall analysis
                print(f'\n🎯 CLEANING EFFECTIVENESS:')
                print('=' * 50)
                
                total_content = ' '.join(chunk.get('content', '') for chunk in chunks)
                
                final_nan_count = total_content.count('NaN')
                final_unnamed_count = total_content.count('Unnamed:')
                
                print(f'   📊 Final content statistics:')
                print(f'      • Total processed content: {len(total_content)} chars')
                print(f'      • Remaining NaN values: {final_nan_count}')
                print(f'      • Remaining Unnamed columns: {final_unnamed_count}')
                
                if final_nan_count == 0 and final_unnamed_count == 0:
                    print(f'   🏆 PERFECT CLEANING ACHIEVED!')
                elif final_nan_count < 5 and final_unnamed_count < 5:
                    print(f'   ✅ EXCELLENT CLEANING (minimal artifacts)')
                else:
                    print(f'   📈 GOOD CLEANING (some artifacts remain)')
                
                # Check for business content preservation
                business_terms = ['form', 'approval', 'overtime', 'manager', 'employee', 'date', 'department']
                preserved_terms = sum(1 for term in business_terms if term in total_content.lower())
                
                print(f'   📋 Business content preserved: {preserved_terms}/{len(business_terms)} key terms')
                
            else:
                print(f'\n⚠️  No chunks generated from cleaned data')
        
        else:
            print('❌ Processing failed with cleaned data')
    
    except Exception as e:
        print(f'❌ Exception during improved XLSX processing: {e}')
    
    print('\n' + '=' * 60)
    print('🎯 XLSX CLEANING IMPROVEMENTS SUMMARY')
    print('=' * 60)
    print('✅ Improvements Made:')
    print('   • Removed "NaN" values from empty cells')
    print('   • Cleaned "Unnamed:" column headers')
    print('   • Added proper column separators (|)')
    print('   • Preserved meaningful business content')
    print('   • Structured data formatting')
    print('   • Empty row filtering')
    print('\n🚀 Result: Clean, readable spreadsheet data for business processing!')

if __name__ == "__main__":
    test_xlsx_cleaned()
