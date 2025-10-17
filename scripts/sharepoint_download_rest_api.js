/**
 * SharePoint Office Files Downloader using REST API
 * 
 * INSTRUCTIONS:
 * 1. Open https://nomadrail.sharepoint.com in your browser and login
 * 2. Press F12 to open Developer Console
 * 3. Copy and paste this ENTIRE script into the console
 * 4. Press Enter
 * 5. The script will use SharePoint's REST API to download files
 * 
 * This approach uses SharePoint's Graph API to get direct download links
 * which should bypass the Office Online viewer.
 */

(async function() {
    console.log("🚀 SharePoint Office Files Downloader (REST API Method)");
    console.log("=" + "=".repeat(60));
    
    // Test URLs - replace with your actual Office file URLs
    const officeUrls = [
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Bid Development/BMS-BDEV-FOR-004 Bid Risk Register.xlsx?d=wc9775d7211364c82957b020a0148c710",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Bid Development/BMS-BDEV-FOR-002 Bid Sign Off Record.docx?d=w17541349903846e6a4e194efa42065ea",
        // Add more URLs here - the full list from your CSV
    ];
    
    console.log(`Total files to download: ${officeUrls.length}`);
    console.log("");
    
    let downloaded = 0;
    let failed = 0;
    const failedFiles = [];
    
    // Function to extract site-relative URL from full URL
    function getSiteRelativeUrl(fullUrl) {
        try {
            const url = new URL(fullUrl);
            // Remove query parameters
            const path = url.pathname.replace(url.search, '');
            return path;
        } catch (e) {
            return null;
        }
    }
    
    // Function to get filename from URL
    function getFilename(url) {
        const parts = url.split('/');
        const lastPart = parts[parts.length - 1];
        return decodeURIComponent(lastPart.split('?')[0]);
    }
    
    // Function to download using SharePoint REST API
    async function downloadFile(url, index) {
        const filename = getFilename(url);
        console.log(`[${index + 1}/${officeUrls.length}] ${filename}`);
        
        try {
            // Get the site-relative URL
            const siteRelativeUrl = getSiteRelativeUrl(url);
            if (!siteRelativeUrl) {
                throw new Error("Could not parse URL");
            }
            
            // Use SharePoint REST API to get file content
            // This endpoint returns the actual file binary
            const apiUrl = `https://nomadrail.sharepoint.com/_api/web/GetFileByServerRelativeUrl('${siteRelativeUrl}')/$value`;
            
            console.log(`  Fetching from: ${apiUrl.substring(0, 80)}...`);
            
            const response = await fetch(apiUrl, {
                method: 'GET',
                headers: {
                    'Accept': 'application/octet-stream',
                },
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Get the blob
            const blob = await response.blob();
            
            if (blob.size < 100) {
                throw new Error(`File too small (${blob.size} bytes) - likely an error`);
            }
            
            // Create download link
            const blobUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = filename;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            setTimeout(() => {
                document.body.removeChild(a);
                window.URL.revokeObjectURL(blobUrl);
            }, 100);
            
            console.log(`  ✅ ${(blob.size / 1024).toFixed(1)} KB`);
            downloaded++;
            
        } catch (error) {
            console.error(`  ❌ ${error.message}`);
            failed++;
            failedFiles.push({filename, error: error.message});
        }
        
        // Wait between downloads
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Download all files
    for (let i = 0; i < officeUrls.length; i++) {
        await downloadFile(officeUrls[i], i);
    }
    
    // Summary
    console.log("");
    console.log("=" + "=".repeat(60));
    console.log("📊 DOWNLOAD SUMMARY");
    console.log("=" + "=".repeat(60));
    console.log(`Total: ${officeUrls.length}`);
    console.log(`✅ Downloaded: ${downloaded}`);
    console.log(`❌ Failed: ${failed}`);
    
    if (failedFiles.length > 0 && failedFiles.length <= 10) {
        console.log("\nFailed files:");
        failedFiles.forEach(f => console.log(`  - ${f.filename}: ${f.error}`));
    }
    
    console.log("\n✅ Check your Downloads folder!");
    
})();
