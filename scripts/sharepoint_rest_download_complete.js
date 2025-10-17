/**
 * SharePoint Office Files Downloader using REST API
 * 
 * INSTRUCTIONS:
 * 1. Open https://nomadrail.sharepoint.com in your browser and login
 * 2. Press F12 to open Developer Console  
 * 3. Copy and paste this ENTIRE script into the console
 * 4. Press Enter
 * 5. Allow multiple downloads when prompted
 * 
 * This uses SharePoint's REST API /_api/web/GetFileByServerRelativeUrl
 * to download files directly, bypassing Office Online viewer.
 */

(async function() {
    console.log("🚀 SharePoint Office Files Downloader (REST API)");
    console.log("=".repeat(70));
    
    const officeUrls = [
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Bid Development/BMS-BDEV-FOR-004 Bid Risk Register.xlsx?d=wc9775d7211364c82957b020a0148c710",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Bid Development/BMS-BDEV-FOR-011 EXco and SVC Bid Sign-Off Template.pptx?d=w6acf2e1609c540168ea09d89168fb032",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Bid Development/BMS-BDEV-FOR-002 Bid Sign Off Record.docx?d=w17541349903846e6a4e194efa42065ea",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Bid Development/BMS-BDEV-FOR-006 BOR For Alstom Opportunities.docx?d=webf5552d78f349379b081b92d2aa1dc6",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Bid Development/BMS-BDEV-FOR-001 BOR For External Opportunities.docx?d=wbfe0b43eef4f40b78c534b70110b0764",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Bid Development/BMS-BDEV-FOR-010 Commercial Proposal Template.docx?d=w7e97d1bd1c654ac2920ec5eac2002806",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Finance/BMS-FINA-FOR-001 Manual Payment form.docx?d=w0301264aa0c84c10b14fc8ed5beef7d0",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Finance/BMS-FINA-FOR-004 Supplier Approval Checklist.xlsx?d=wc40bf28127dc4de69fd458dde2153c5d",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/HR/BMS-HUMR-FOR-018 Driver Declaration Form.doc?d=wa6ebd0e85b764bcdae68dcce83da5438",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/HR/BMS-HUMR-FOR-005 Employee Referral Form.doc?d=w282f4207d5d141ebb798e28302ad1a8e",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/HR/BMS-HUMR-FOR-007 Example Interview Questions Template.docx?d=wa4b834b725a84b029e7f99f5cf6a5cfb",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/HR/BMS-HUMR-FOR-017 Job Description - Template.docx?d=w63d8e8e9763b4c9dba87e088c9bb8f67",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/HR/BMS-HUMR-FOR-009 Maternity Risk Assessment.docx?d=wffa5617b2ec9494eb73e672fbc36427e",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/HR/BMS-HUMR-FOR-008 - Peep Form.doc?d=w57e1432f315041ba8d8c6c389c26c6f9",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/InfoSec/BMS-ISEC-FOR-016 Customer Solution - Vulnerability Assessment Sign Off.docx?d=wb22a458bf9a742968a0a006cc13aff7e",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/InfoSec/BMS-ISEC-FOR-013 Data Protection Impact Assessment - Screening Checklist.docx?d=wda5bcd538ab749eb955aea1119b1e033",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/InfoSec/BMS-ISEC-FOR-015 Information Security Management Plan Template.docx?d=wa05079d7461849f5a5cfa3a31f5f61c6",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/InfoSec/BMS-ISEC-FOR-003 Incident Reporting Form.docx?d=w556b92950c9a4be59d0ce6ccc035a8c9",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/InfoSec/BMS-ISEC-FOR-008 Internal System Audit Report.docx?d=w73016d4acd5b4a5eac1ae218b01b55b7",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/InfoSec/BMS-ISEC-FOR-002 Physical Security Assessment Checklist.docx?d=wcb0e13aeddf54200b7b6e8f27bbe86ad",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/InfoSec/BMS-ISEC-FOR-010 System Access Audit Report.docx?d=wc1636b221a8b4933983791effe0a8710",
        "https://nomadrail.sharepoint.com/qms/BMS System/08 Registers/BMS-ISEC-REG-002 - Information Asset Register.xlsx?d=we07d2cd22852409d88f31f9febbced09",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Legal/BMS-LEGA-FOR-006 Nomad Digital Limited - Data Processing Agreement.doc?d=weec41ed6ed9543c49a0b13bb0b89e07e",
        "https://nomadrail.sharepoint.com/qms/BMS System/11 Marketing Templates/Word Document Templates/BMS-MARK-TEM-006 External Briefing document (short).docx?d=w64ed48e2b11b40139e5d9a3ce2f11c23",
        "https://nomadrail.sharepoint.com/qms/BMS System/11 Marketing Templates/Letterheads/BMS-MARK-LET-001 Blank - No Address Template.docx?d=wf4551a4f0c764f6b89341f9171eef44e",
        "https://nomadrail.sharepoint.com/qms/BMS System/11 Marketing Templates/Letterheads/BMS-MARK-LET-012  LetterHead Belgium.docx?d=wce7fe4505a6a41b5b015e94e2e43dc9b",
        "https://nomadrail.sharepoint.com/qms/BMS System/11 Marketing Templates/Letterheads/BMS-MARK-LET-006 Letterhead Newcastle.docx?d=w3fc4745e1ad24e52a1a852226e5df3b3",
        "https://nomadrail.sharepoint.com/qms/BMS System/11 Marketing Templates/Letterheads/BMS-MARK-LET-013 LetterHead France.docx?d=w629bc11c0c394a45901e5d3b694d50ef",
        "https://nomadrail.sharepoint.com/qms/BMS System/11 Marketing Templates/Letterheads/BMS-MARK-LET-009 Letterhead Vienna.docx?d=w8bb9d66aa7f6481d9432b9af7c550b1d",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Procurement/BMS-PROC-FOR-002 Goods In-Inspection Receipt.doc?d=w72cb703e58fe4c588bb17e0ad50faa0b",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Procurement/BMS-PROC-FOR-009 New Supplier Form for ERP Upload.xlsx?d=w28b9a1c28a0a41e6b39133003d6e1f93",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Procurement/BMS-PROC-FOR-006 Pack and Despatch Note.docx?d=w8650ec97c7b241b6ba872cec2160d406",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Procurement/BMS-PROC-FOR-007 Supplier Questionnaire.docx?d=wd69f71c69f58489c9416d79cc2527717",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Product Management/BMS-PROD-FOR-001 Product Change Request Form.docx?d=w61dc866f631e4240a5d8044acc87943b&csf=1&e=3e54e16f90fc42368cd735a830082aee",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Product Management/BMS-PROD-FOR-003 Product Requirements Summary Template.docx?d=waba25e942acf40f6877f7e1cacdf0ee4",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Projects/BMS-PROJ-FOR-014 Cable Schedule Example.xlsx?d=w4a63acc567d04f359b8afbdd06d15774",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Projects/BMS-PROJ-FOR-015 Commissioning Test Plan.docx?d=wd2082b1641ee4d3aba2d8c0b4d2d5bb5",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Projects/BMS-PROJ-FOR-003 Contractor Management Plan.docx?d=w1e79f1463ba54996990daaf967d3f553",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Projects/BMS-PROJ-FOR-017 DTR Form.docx?d=w1ed61f367f164d509fb78f442aff5751",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Projects/BMS-PROJ-FOR-001 Method Statement Template.docx?d=wf99ef8b3376c4b2ba8dfd575748ccc52",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Projects/BMS-PROJ-FOR-011 Project Change Control Form.docx?d=wb81b54866947485586fc10dea8762634",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Projects/BMS-PROJ-FOR-012 Project End Review Form.doc?d=w1eb7d2d6e267452c8f9770c408b6d53a",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Projects/BMS-PROJ-FOR-007 Project FAI Template.doc?d=wbd53707d951b43f68d878517a7e2d4c2",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Projects/BMS-PROJ-FOR-004 Project Initiation Document.docx?d=wd60512893a5d498492452d7ba75315ff",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Projects/BMS-PROJ-FOR-006 Project Quality Plan.docx?d=w6bfcc85056a44462bec16ba46b06e3a6",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Projects/BMS-PROJ-FOR-022 Project Safety Plan.docx?d=wb23846fa2b1c4e5db6fd7ab5f4986901",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Projects/BMS-PROJ-FOR-010 Project Technical Documentation.xlsx?d=wd123f5393438408db7897e00405a0b6b",
        "https://nomadrail.sharepoint.com/qms/BMS System/08 Registers/BMS-PROJ-REG-001 Doc Register Template.xlsx?d=wdb5769aed57c431a930b037843e21fd2",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-001 8D Analysis Report.doc?d=waf762a6aedf24adbaa520d808b3c73f1",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-008 Chemical Assessment Form.docx?d=w2c60a05f4eed4bb595bd2180bb51644d",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-024 Completion of Training Record.docx?d=w3c4ce89e59c143f08f657f60f2d00009",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-025 Completion of Training Record - German.docx?d=w0d3b5577ab46486c9ab444f86ace7064",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-026 Employee Equipment and PPE Allocation Form.doc?d=wfb3d0681632645b5a066fc8a6c71e126",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-019 Homeworker Health and Safety Questionnaire.doc?d=w022ca5b4925a4fd1af2aec2f100145e0",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-002 Internal Audit Report.docx?d=w30d5dbbeea07489c95cce723f9b2d5b3",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-027 IP Witness Statement.doc?d=w4503cb7940e24b0b939f16453b431c34",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-020 Monthly Fire Extinguisher Checklist.docx?d=wf5c1f5c64792487781207b64ff2eee73",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-039 Monthly Racking Inspection Checklist.docx?d=wdce5081f029f45a1a250c0028aca6a47",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-014 Office Inspection Checklist.doc?d=w7329b04ffb174f25911f8ef7efc6600a",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-022 Pallet Truck Monthly checklist.doc?d=w021ee69b6a4b41488f7e01edfeb337e6",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-036 Punchlist Action Template.xlsx?d=w2f224397b40145eea1c3b692892ba20e&csf=1&e=e47f1d43339444908d9d0dc4e1d7ea45",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-011 Risk Assessment Hazards Checklist.docx?d=w9fed6b00ad1640ddacb610e6f4b12231",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-009 Risk Assessment Template.docx?d=wf92a7687b2ca4fadb939683e705591af",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-003 Supplier Audit Report.docx?d=w63ae2175ce794bc68024f8e5cda32f8c",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/QHSE/BMS-QHSE-FOR-037 Toolbox Talk Prestart Talks Template.docx?d=w1d95f929264241f1ab5e026a0aabf597",
        "https://nomadrail.sharepoint.com/qms/BMS System/08 Registers/BMS-QHSE-REG-001 Environmental Aspects and Impacts Register.xlsx?d=w964f2893f849454586df91f83386f196",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Sales/BMS-SALE-FOR-001 Sales to Delivery Handover Checklist.xlsm?d=w5969ae9d0f8444038f21386adc22d735",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Service Management/BMS-SERV-FOR-007 APAC CR.docx?d=w96a970f93c1c438b8e95af8a6df96344",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Service Management/BMS-SERV-FOR-006 Incident Report Form.docx?d=w34d88d2ae0f343d8bf41df32d324738e",
        "https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/Service Management/BMS-SERV-FOR-005 Train Ride Test Report.docx?d=we9d72523f2a841e98fa09bcd35a0d0a6",
    ];
    
    console.log(`Total files: ${officeUrls.length}`);
    console.log("");
    
    let downloaded = 0;
    let failed = 0;
    const failedFiles = [];
    
    function getSiteRelativeUrl(fullUrl) {
        try {
            const url = new URL(fullUrl);
            return url.pathname.split('?')[0];
        } catch (e) {
            return null;
        }
    }
    
    function getFilename(url) {
        const parts = url.split('/');
        return decodeURIComponent(parts[parts.length - 1].split('?')[0]);
    }
    
    async function downloadFile(url, index) {
        const filename = getFilename(url);
        console.log(`[${index + 1}/${officeUrls.length}] ${filename}`);
        
        try {
            const siteRelativeUrl = getSiteRelativeUrl(url);
            if (!siteRelativeUrl) throw new Error("Could not parse URL");
            
            // Use SharePoint REST API
            const apiUrl = `https://nomadrail.sharepoint.com/_api/web/GetFileByServerRelativeUrl('${siteRelativeUrl}')/$value`;
            
            const response = await fetch(apiUrl, {
                method: 'GET',
                headers: {'Accept': 'application/octet-stream'},
                credentials: 'include'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const blob = await response.blob();
            if (blob.size < 100) throw new Error(`Too small (${blob.size} bytes)`);
            
            // Download
            const a = document.createElement('a');
            a.href = window.URL.createObjectURL(blob);
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            console.log(`  ✅ ${(blob.size / 1024).toFixed(1)} KB`);
            downloaded++;
            
        } catch (error) {
            console.error(`  ❌ ${error.message}`);
            failed++;
            failedFiles.push({filename, error: error.message});
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    for (let i = 0; i < officeUrls.length; i++) {
        await downloadFile(officeUrls[i], i);
    }
    
    console.log("\n" + "=".repeat(70));
    console.log(`✅ Downloaded: ${downloaded} | ❌ Failed: ${failed}`);
    if (failedFiles.length > 0 && failedFiles.length <= 10) {
        console.log("\nFailed:");
        failedFiles.forEach(f => console.log(`  - ${f.filename}`));
    }
    console.log("\n✅ Check your Downloads folder!");
})();
