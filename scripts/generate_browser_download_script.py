#!/usr/bin/env python3
"""
Generate browser download script with all Office file URLs from bms-docs-urls.md
"""

import csv
from pathlib import Path

def main():
    # Read URLs from CSV
    csv_file = Path('/workspace/001-bms-agent/docs/bms-docs-urls.md')
    
    office_urls = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('URL', '')
            if url:
                # Check if it's an Office file URL
                if any(ext in url.lower() for ext in ['.docx', '.xlsx', '.pptx', '.doc', '.xls', '.ppt', '.xlsm', '.potx']):
                    office_urls.append(url)
    
    print(f"Found {len(office_urls)} Office file URLs")
    
    # Generate JavaScript
    js_template = '''/**
 * SharePoint Office Files Browser Downloader
 * 
 * INSTRUCTIONS:
 * 1. Open SharePoint in your browser and login: https://nomadrail.sharepoint.com
 * 2. Open browser Developer Console (F12 or Ctrl+Shift+J)
 * 3. Copy and paste this ENTIRE script into the console
 * 4. Press Enter to run
 * 5. Your browser will download all files (may ask for permission)
 * 
 * IMPORTANT: 
 * - Keep the browser tab open until all downloads complete
 * - Check your Downloads folder for the files
 * - If downloads fail, you may need to refresh your SharePoint session
 */

(async function() {
    const officeUrls = [
{urls}
    ];
    
    console.log("🚀 SharePoint Office Files Downloader");
    console.log("=====================================");
    console.log(`Total files to download: ${officeUrls.length}`);
    console.log("NOTE: Your browser may ask permission to download multiple files");
    console.log("");
    
    let downloaded = 0;
    let failed = 0;
    const failedFiles = [];
    
    function getFilename(url) {{
        const match = url.match(/file=([^&]+)/);
        if (match) {{
            return decodeURIComponent(match[1]);
        }}
        const parts = url.split('/');
        const lastPart = parts[parts.length - 1];
        return decodeURIComponent(lastPart.split('?')[0]);
    }}
    
    async function downloadFile(url, index) {{
        const filename = getFilename(url);
        console.log(`[${index + 1}/${officeUrls.length}] ${filename}`);
        
        try {{
            let downloadUrl = url;
            
            // Convert Office Online URLs to download URLs
            if (url.includes('/_layouts/15/Doc.aspx')) {{
                const match = url.match(/sourcedoc=(%7B[^%]+%7D)/);
                if (match) {{
                    const guid = match[1];
                    downloadUrl = `https://nomadrail.sharepoint.com/_layouts/15/download.aspx?UniqueId=${guid}`;
                }}
            }} else if (url.includes('?d=')) {{
                downloadUrl = url.replace('?d=', '?download=1&d=');
            }}
            
            const response = await fetch(downloadUrl);
            
            if (!response.ok) {{
                throw new Error(`HTTP ${response.status}`);
            }}
            
            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('text/html')) {{
                throw new Error('Got HTML instead of file (auth issue)');
            }}
            
            const blob = await response.blob();
            
            // Check if blob is too small (likely an error page)
            if (blob.size < 100) {{
                throw new Error(`File too small (${blob.size} bytes)`);
            }}
            
            const blobUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = filename;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            
            setTimeout(() => {{
                document.body.removeChild(a);
                window.URL.revokeObjectURL(blobUrl);
            }}, 100);
            
            console.log(`  ✅ ${(blob.size / 1024).toFixed(1)} KB`);
            downloaded++;
            
        }} catch (error) {{
            console.error(`  ❌ ${error.message}`);
            failed++;
            failedFiles.push({{filename, url, error: error.message}});
        }}
        
        await new Promise(resolve => setTimeout(resolve, 800));
    }}
    
    for (let i = 0; i < officeUrls.length; i++) {{
        await downloadFile(officeUrls[i], i);
    }}
    
    console.log("");
    console.log("=====================================");
    console.log("📊 DOWNLOAD SUMMARY");
    console.log("=====================================");
    console.log(`Total: ${officeUrls.length}`);
    console.log(`✅ Downloaded: ${downloaded}`);
    console.log(`❌ Failed: ${failed}`);
    
    if (failedFiles.length > 0 && failedFiles.length <= 10) {{
        console.log("\\nFailed files:");
        failedFiles.forEach(f => console.log(`  - ${f.filename}: ${f.error}`));
    }}
    
    console.log("\\n✅ Check your Downloads folder!");
    
}})();
'''
    
    # Format URLs for JavaScript array
    urls_js = ',\n'.join(f'        "{url}"' for url in office_urls)
    
    js_code = js_template.format(urls=urls_js)
    
    # Save to file
    output_file = Path('/workspace/001-bms-agent/scripts/download_office_files_browser.js')
    output_file.write_text(js_code)
    
    print(f"\n✅ Generated browser script: {output_file}")
    print(f"   Contains {len(office_urls)} Office file URLs")
    print("\nTo use:")
    print("1. Open SharePoint in browser: https://nomadrail.sharepoint.com")
    print("2. Open Developer Console (F12)")
    print(f"3. Copy contents of {output_file}")
    print("4. Paste into console and press Enter")
    print("5. Files will download to your Downloads folder")

if __name__ == '__main__':
    main()
