#!/usr/bin/env python3
"""
Generate a complete browser console script with all SharePoint URLs
from the bms-docs-urls.md file
"""

import csv
import json
from pathlib import Path

def parse_csv_file(csv_path):
    """Parse the CSV file and extract document information"""
    documents = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'URL' in row and row['URL'].startswith('http'):
                documents.append({
                    'name': row.get('Display Text', '').strip(),
                    'url': row['URL'].strip(),
                    'cell': row.get('Cell', '').strip()
                })
    
    return documents

def generate_browser_script(documents, output_path):
    """Generate the complete browser console script"""
    
    # Convert documents to JSON for embedding in script
    docs_json = json.dumps(documents, indent=2)
    
    script = f'''/**
 * SharePoint Document Downloader - Browser Console Script
 * 
 * Downloads documents from SharePoint URLs, filtering for files modified after 2023-12-31
 * 
 * INSTRUCTIONS:
 * 1. Open SharePoint in your browser (https://nomadrail.sharepoint.com) and log in
 * 2. Open browser Developer Tools (F12 or Ctrl+Shift+I)
 * 3. Go to the Console tab
 * 4. Copy and paste this entire script
 * 5. Press Enter to run
 * 
 * FEATURES:
 * - Filters files by modification date (after 2023-12-31)
 * - Batch processing to avoid rate limiting
 * - Progress tracking and error reporting
 * - Automatic retry on failures
 * 
 * Total documents to process: {len(documents)}
 */

(async function() {{
    'use strict';
    
    // ==================== CONFIGURATION ====================
    const CUTOFF_DATE = new Date('2023-12-31T23:59:59Z');
    const DELAY_MS = 2000; // Delay between downloads (2 seconds)
    const BATCH_SIZE = 3; // Process 3 files at a time
    const MAX_RETRIES = 2; // Retry failed downloads
    
    // ==================== DOCUMENT DATA ====================
    const documents = {docs_json};
    
    console.log('🚀 SharePoint Document Downloader Started');
    console.log(`📅 Filtering for files modified after: ${{CUTOFF_DATE.toISOString()}}`);
    console.log(`📋 Total documents to check: ${{documents.length}}`);
    console.log('');
    
    // ==================== HELPER FUNCTIONS ====================
    
    function extractFileName(url) {{
        const fileMatch = url.match(/file=([^&]+)/);
        if (fileMatch) {{
            return decodeURIComponent(fileMatch[1]);
        }}
        
        // Fallback: try to extract from URL path
        const pathMatch = url.match(/\\/([^\\/]+\\.(pdf|docx?|xlsx?|pptx?|txt|csv))$/i);
        if (pathMatch) {{
            return pathMatch[1];
        }}
        
        return null;
    }}
    
    function sanitizeFileName(fileName) {{
        // Remove invalid characters for file names
        return fileName.replace(/[<>:"\\/\\|?*]/g, '_');
    }}
    
    async function checkFileDate(url) {{
        try {{
            // Try to get file info from SharePoint
            const response = await fetch(url, {{
                method: 'HEAD',
                credentials: 'include'
            }});
            
            if (response.ok) {{
                const lastModified = response.headers.get('Last-Modified');
                if (lastModified) {{
                    return new Date(lastModified);
                }}
            }}
        }} catch (error) {{
            console.warn(`   ⚠️  Could not check date: ${{error.message}}`);
        }}
        return null;
    }}
    
    async function downloadFile(doc, retryCount = 0) {{
        try {{
            const fileName = extractFileName(doc.url);
            if (!fileName) {{
                doc.error = 'Cannot extract filename from URL';
                doc.skipped = true;
                return false;
            }}
            
            console.log(`\\n📄 ${{doc.name}}`);
            console.log(`   File: ${{fileName}}`);
            
            // Check modification date
            const lastModified = await checkFileDate(doc.url);
            if (lastModified) {{
                console.log(`   Last Modified: ${{lastModified.toISOString()}}`);
                
                if (lastModified <= CUTOFF_DATE) {{
                    console.log(`   ⏭️  SKIPPED (modified before 2024)`);
                    doc.skipped = true;
                    doc.skipReason = 'too_old';
                    return false;
                }}
            }} else {{
                console.log(`   ⚠️  Date unknown, downloading anyway...`);
            }}
            
            // Download the file
            console.log(`   ⬇️  Downloading...`);
            const response = await fetch(doc.url, {{
                method: 'GET',
                credentials: 'include',
                redirect: 'follow'
            }});
            
            if (!response.ok) {{
                throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
            }}
            
            const blob = await response.blob();
            const size = (blob.size / 1024).toFixed(2);
            console.log(`   📦 Size: ${{size}} KB`);
            
            // Trigger download
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = sanitizeFileName(fileName);
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);
            
            doc.downloaded = true;
            doc.size = blob.size;
            console.log(`   ✅ DOWNLOADED`);
            return true;
            
        }} catch (error) {{
            console.log(`   ❌ ERROR: ${{error.message}}`);
            
            // Retry logic
            if (retryCount < MAX_RETRIES) {{
                console.log(`   🔄 Retrying (${{retryCount + 1}}/${{MAX_RETRIES}})...`);
                await new Promise(resolve => setTimeout(resolve, 3000));
                return await downloadFile(doc, retryCount + 1);
            }}
            
            doc.error = error.message;
            return false;
        }}
    }}
    
    // ==================== MAIN PROCESSING ====================
    
    let stats = {{
        processed: 0,
        downloaded: 0,
        skipped: 0,
        errors: 0,
        totalSize: 0
    }};
    
    console.log('\\n' + '═'.repeat(70));
    console.log('Starting batch processing...');
    console.log('═'.repeat(70));
    
    for (let i = 0; i < documents.length; i += BATCH_SIZE) {{
        const batch = documents.slice(i, i + BATCH_SIZE);
        const batchNum = Math.floor(i / BATCH_SIZE) + 1;
        const totalBatches = Math.ceil(documents.length / BATCH_SIZE);
        
        console.log(`\\n📦 Batch ${{batchNum}}/${{totalBatches}}`);
        console.log('─'.repeat(70));
        
        // Process batch sequentially to avoid overwhelming SharePoint
        for (const doc of batch) {{
            const success = await downloadFile(doc);
            
            stats.processed++;
            if (doc.downloaded) {{
                stats.downloaded++;
                stats.totalSize += doc.size || 0;
            }} else if (doc.skipped) {{
                stats.skipped++;
            }} else if (doc.error) {{
                stats.errors++;
            }}
            
            // Delay between downloads
            if (stats.processed < documents.length) {{
                await new Promise(resolve => setTimeout(resolve, DELAY_MS));
            }}
        }}
        
        // Progress update
        console.log('─'.repeat(70));
        console.log(`📊 Progress: ${{stats.processed}}/${{documents.length}} | ` +
                   `✅ ${{stats.downloaded}} | ⏭️  ${{stats.skipped}} | ❌ ${{stats.errors}}`);
    }}
    
    // ==================== FINAL SUMMARY ====================
    
    console.log('\\n' + '═'.repeat(70));
    console.log('🎉 DOWNLOAD COMPLETE');
    console.log('═'.repeat(70));
    console.log(`📊 Total Processed: ${{stats.processed}}`);
    console.log(`✅ Downloaded: ${{stats.downloaded}}`);
    console.log(`⏭️  Skipped (old files): ${{stats.skipped}}`);
    console.log(`❌ Errors: ${{stats.errors}}`);
    console.log(`💾 Total Size: ${{(stats.totalSize / 1024 / 1024).toFixed(2)}} MB`);
    console.log('═'.repeat(70));
    
    // Show failed downloads
    if (stats.errors > 0) {{
        console.log('\\n❌ Failed Downloads:');
        documents.filter(d => d.error && !d.skipped).forEach(doc => {{
            console.log(`   - ${{doc.name}}: ${{doc.error}}`);
        }});
    }}
    
    // Show download summary
    console.log('\\n📥 Downloaded Files:');
    documents.filter(d => d.downloaded).forEach(doc => {{
        const size = doc.size ? `(${{(doc.size / 1024).toFixed(2)}} KB)` : '';
        console.log(`   ✅ ${{doc.name}} ${{size}}`);
    }});
    
    console.log('\\n✨ All done! Check your Downloads folder for the files.');
    
}})();'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(script)
    
    print(f"✅ Generated browser script: {output_path}")
    print(f"📋 Total documents: {len(documents)}")
    print(f"\\n📝 Instructions:")
    print(f"   1. Open the generated file: {output_path}")
    print(f"   2. Copy the entire contents")
    print(f"   3. Open SharePoint in your browser and log in")
    print(f"   4. Press F12 to open Developer Tools")
    print(f"   5. Go to Console tab")
    print(f"   6. Paste the script and press Enter")

def main():
    # Paths
    project_root = Path(__file__).parent.parent
    csv_path = project_root / "docs" / "bms-docs-urls.md"
    output_path = project_root / "scripts" / "download_sharepoint_docs_complete.js"
    
    print("🔍 Parsing CSV file...")
    documents = parse_csv_file(csv_path)
    
    print(f"✅ Found {len(documents)} documents")
    
    print("\\n📝 Generating browser script...")
    generate_browser_script(documents, output_path)
    
    print("\\n✨ Done!")

if __name__ == "__main__":
    main()
