/**
 * SharePoint Document Downloader - Browser Console Script
 * 
 * This script downloads documents from SharePoint URLs listed in bms-docs-urls.md
 * Filters for files modified after December 31, 2023
 * 
 * INSTRUCTIONS:
 * 1. Open SharePoint in your browser and log in
 * 2. Open browser Developer Tools (F12)
 * 3. Go to the Console tab
 * 4. Copy and paste this entire script
 * 5. Press Enter to run
 * 
 * The script will:
 * - Parse the URLs from the data below
 * - Check modification dates via SharePoint API
 * - Download only files modified after 2023-12-31
 * - Show progress in the console
 */

(async function() {
    'use strict';
    
    // Configuration
    const CUTOFF_DATE = new Date('2023-12-31T23:59:59Z');
    const DELAY_MS = 1000; // Delay between downloads to avoid rate limiting
    const BATCH_SIZE = 5; // Number of concurrent downloads
    
    // Parse the CSV data from bms-docs-urls.md
    const urlData = \`Sheet,Cell,Display Text,URL,Type
query,$A$2,Bid Action Log Check List,https://nomadrail.sharepoint.com/:x:/r/qms/_layouts/15/Doc.aspx?sourcedoc=%7B8216852E-8E45-409E-94D6-CF85DB882F2D%7D&file=BMS-BDEV-FOR-005%20Bid%20Action%20Log%20Check%20List.xlsx&action=default&mobileredirect=true,Embedded
query,$A$3,Bid Kick Off Template,https://nomadrail.sharepoint.com/:p:/r/qms/_layouts/15/Doc.aspx?sourcedoc=%7B7448B95F-93CE-4CF1-AB5D-651403C58A6F%7D&file=BMS-BDEV-FOR-008%20Bid%20Kick%20Off%20Template.pptx&action=edit&mobileredirect=true,Embedded
query,$A$4,Bid Project Task Sheet - Restricted Document,https://nomadrail.sharepoint.com/:x:/r/qms/_layouts/15/Doc.aspx?sourcedoc=%7BA470F67F-7528-4322-ACE8-7245456C9E9F%7D&file=BMS-BDEV-FOR-027%20Bid%20Project%20Task%20Sheet.xlsx&action=default&mobileredirect=true,Embedded
\`; // Add all your URLs here - truncated for brevity
    
    console.log('🚀 SharePoint Document Downloader Started');
    console.log(`📅 Filtering for files modified after: ${CUTOFF_DATE.toISOString()}`);
    console.log('');
    
    // Parse CSV data
    const lines = urlData.trim().split('\n').slice(1); // Skip header
    const documents = lines.map(line => {
        const parts = line.split(',');
        if (parts.length < 4) return null;
        
        // Extract URL (may contain commas in the display text)
        const urlMatch = line.match(/https:\/\/[^,]+/);
        if (!urlMatch) return null;
        
        const url = urlMatch[0];
        const displayText = parts[2];
        
        return {
            name: displayText,
            url: url,
            downloaded: false,
            skipped: false,
            error: null
        };
    }).filter(doc => doc !== null);
    
    console.log(`📋 Found ${documents.length} documents to process`);
    console.log('');
    
    // Helper function to extract file info from SharePoint URL
    function extractFileInfo(url) {
        const fileMatch = url.match(/file=([^&]+)/);
        if (!fileMatch) return null;
        
        const fileName = decodeURIComponent(fileMatch[1]);
        const extension = fileName.split('.').pop().toLowerCase();
        
        return { fileName, extension };
    }
    
    // Helper function to get file metadata from SharePoint
    async function getFileMetadata(url) {
        try {
            // Extract the source document ID
            const docIdMatch = url.match(/sourcedoc=%7B([^%]+)%7D/);
            if (!docIdMatch) {
                console.warn(`⚠️  Cannot extract document ID from: ${url}`);
                return null;
            }
            
            const docId = docIdMatch[1];
            
            // Construct SharePoint REST API URL
            // Note: This is a simplified approach - actual implementation may vary
            const siteUrl = url.match(/https:\/\/[^\/]+/)[0];
            const apiUrl = `${siteUrl}/_api/web/GetFileById('${docId}')?$select=TimeLastModified,Name,Length`;
            
            const response = await fetch(apiUrl, {
                headers: {
                    'Accept': 'application/json;odata=verbose'
                }
            });
            
            if (!response.ok) {
                return null;
            }
            
            const data = await response.json();
            return {
                lastModified: new Date(data.d.TimeLastModified),
                name: data.d.Name,
                size: data.d.Length
            };
        } catch (error) {
            console.warn(`⚠️  Error fetching metadata: ${error.message}`);
            return null;
        }
    }
    
    // Helper function to download a file
    async function downloadFile(doc) {
        try {
            const fileInfo = extractFileInfo(doc.url);
            if (!fileInfo) {
                doc.error = 'Cannot extract filename';
                doc.skipped = true;
                return;
            }
            
            // Get file metadata to check modification date
            const metadata = await getFileMetadata(doc.url);
            
            if (metadata) {
                console.log(`📄 ${doc.name}`);
                console.log(`   Last Modified: ${metadata.lastModified.toISOString()}`);
                console.log(`   Size: ${(metadata.size / 1024).toFixed(2)} KB`);
                
                // Check if file is recent enough
                if (metadata.lastModified <= CUTOFF_DATE) {
                    console.log(`   ⏭️  SKIPPED (too old)`);
                    doc.skipped = true;
                    return;
                }
            } else {
                console.log(`📄 ${doc.name} (metadata unavailable, downloading anyway)`);
            }
            
            // Download the file
            const response = await fetch(doc.url, {
                method: 'GET',
                credentials: 'include' // Include cookies for authentication
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const blob = await response.blob();
            
            // Create download link
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = fileInfo.fileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);
            
            doc.downloaded = true;
            console.log(`   ✅ DOWNLOADED`);
            
        } catch (error) {
            doc.error = error.message;
            console.log(`   ❌ ERROR: ${error.message}`);
        }
    }
    
    // Process documents in batches
    let processed = 0;
    let downloaded = 0;
    let skipped = 0;
    let errors = 0;
    
    for (let i = 0; i < documents.length; i += BATCH_SIZE) {
        const batch = documents.slice(i, i + BATCH_SIZE);
        
        console.log(`\n📦 Processing batch ${Math.floor(i / BATCH_SIZE) + 1}/${Math.ceil(documents.length / BATCH_SIZE)}`);
        console.log('─'.repeat(60));
        
        await Promise.all(batch.map(doc => downloadFile(doc)));
        
        processed += batch.length;
        downloaded = documents.filter(d => d.downloaded).length;
        skipped = documents.filter(d => d.skipped).length;
        errors = documents.filter(d => d.error && !d.skipped).length;
        
        console.log('─'.repeat(60));
        console.log(`📊 Progress: ${processed}/${documents.length} | ✅ ${downloaded} | ⏭️  ${skipped} | ❌ ${errors}`);
        
        // Delay between batches
        if (i + BATCH_SIZE < documents.length) {
            console.log(`⏳ Waiting ${DELAY_MS}ms before next batch...`);
            await new Promise(resolve => setTimeout(resolve, DELAY_MS));
        }
    }
    
    // Final summary
    console.log('\n');
    console.log('═'.repeat(60));
    console.log('🎉 DOWNLOAD COMPLETE');
    console.log('═'.repeat(60));
    console.log(`📊 Total Processed: ${documents.length}`);
    console.log(`✅ Downloaded: ${downloaded}`);
    console.log(`⏭️  Skipped (old): ${skipped}`);
    console.log(`❌ Errors: ${errors}`);
    console.log('═'.repeat(60));
    
    // Show errors if any
    if (errors > 0) {
        console.log('\n❌ Failed Downloads:');
        documents.filter(d => d.error && !d.skipped).forEach(doc => {
            console.log(`   - ${doc.name}: ${doc.error}`);
        });
    }
    
})();
