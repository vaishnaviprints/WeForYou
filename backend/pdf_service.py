import os
from pathlib import Path
from datetime import datetime
import logging
from weasyprint import HTML, CSS
from io import BytesIO

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        self.use_local = os.environ.get('USE_LOCAL_STORAGE', 'true').lower() == 'true'
        self.local_path = Path(os.environ.get('LOCAL_STORAGE_PATH', '/app/backend/storage'))
        self.local_path.mkdir(parents=True, exist_ok=True)
        
    def generate_receipt_html(self, donation: dict, user: dict, campaign: dict, receipt: dict) -> str:
        """Generate HTML for donation receipt"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{
                    font-family: 'Helvetica', 'Arial', sans-serif;
                    color: #333;
                    line-height: 1.6;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid #2563eb;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #2563eb;
                }}
                .receipt-title {{
                    font-size: 20px;
                    margin-top: 10px;
                    color: #666;
                }}
                .receipt-number {{
                    font-size: 14px;
                    color: #999;
                    margin-top: 5px;
                }}
                .section {{
                    margin: 25px 0;
                }}
                .section-title {{
                    font-size: 16px;
                    font-weight: bold;
                    color: #2563eb;
                    margin-bottom: 10px;
                    border-bottom: 1px solid #e5e7eb;
                    padding-bottom: 5px;
                }}
                .info-row {{
                    display: flex;
                    padding: 8px 0;
                    border-bottom: 1px solid #f3f4f6;
                }}
                .info-label {{
                    width: 40%;
                    font-weight: 600;
                    color: #666;
                }}
                .info-value {{
                    width: 60%;
                    color: #333;
                }}
                .amount-box {{
                    background: #f0f9ff;
                    border: 2px solid #2563eb;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                }}
                .amount-label {{
                    font-size: 14px;
                    color: #666;
                    margin-bottom: 5px;
                }}
                .amount-value {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #2563eb;
                }}
                .footer {{
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 2px solid #e5e7eb;
                    text-align: center;
                    font-size: 12px;
                    color: #999;
                }}
                .note-box {{
                    background: #fffbeb;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    margin: 20px 0;
                    font-size: 13px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">WeForYou Foundation</div>
                <div class="receipt-title">Donation Receipt</div>
                <div class="receipt-number">Receipt No: {receipt['receipt_number']}</div>
            </div>
            
            <div class="amount-box">
                <div class="amount-label">Donation Amount</div>
                <div class="amount-value">₹{donation['amount']:,.2f}</div>
            </div>
            
            <div class="section">
                <div class="section-title">Donor Information</div>
                <div class="info-row">
                    <div class="info-label">Name:</div>
                    <div class="info-value">{donation.get('legal_name') or user['full_name']}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Email:</div>
                    <div class="info-value">{user['email']}</div>
                </div>
                {'<div class="info-row"><div class="info-label">PAN:</div><div class="info-value">' + donation.get('pan', 'N/A') + '</div></div>' if donation.get('pan') else ''}
                {'<div class="info-row"><div class="info-label">Address:</div><div class="info-value">' + donation.get('address', 'N/A') + '</div></div>' if donation.get('address') else ''}
            </div>
            
            <div class="section">
                <div class="section-title">Donation Details</div>
                <div class="info-row">
                    <div class="info-label">Campaign:</div>
                    <div class="info-value">{campaign['title']}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Date:</div>
                    <div class="info-value">{datetime.fromisoformat(donation['created_at']).strftime('%B %d, %Y')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Transaction ID:</div>
                    <div class="info-value">{donation.get('payment_ref', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Payment Method:</div>
                    <div class="info-value">{donation.get('method', 'online').upper()}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Financial Year:</div>
                    <div class="info-value">{receipt['fy']}</div>
                </div>
            </div>
            
            {f'''<div class="note-box">
                <strong>Section 80G Benefit:</strong> This donation is eligible for tax deduction under Section 80G of the Income Tax Act, 1961.
                {f"Acknowledgment No: {receipt.get('ack_no', 'Pending')}" if receipt.get('ack_no') else "Acknowledgment number will be updated separately."}
            </div>''' if receipt.get('section_80g') else ''}
            
            <div class="footer">
                <p><strong>WeForYou Foundation</strong></p>
                <p>Registered Charity | CIN: U85100DL2020NPL123456</p>
                <p>Email: donations@weforyou.org | Phone: +91-11-12345678</p>
                <p>This is a computer-generated receipt and does not require a signature.</p>
            </div>
        </body>
        </html>
        """
        return html
    
    async def generate_receipt_pdf(self, donation: dict, user: dict, campaign: dict, receipt: dict) -> str:
        """Generate PDF receipt and return file path"""
        try:
            html_content = self.generate_receipt_html(donation, user, campaign, receipt)
            
            # Generate filename
            fy = receipt['fy']
            receipt_number = receipt['receipt_number']
            filename = f"WFY-{receipt_number}-{fy}.pdf"
            
            # Create directory structure
            fy_dir = self.local_path / 'receipts' / fy
            fy_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = fy_dir / filename
            
            # Generate PDF
            HTML(string=html_content).write_pdf(file_path)
            
            # Return relative path for URL
            relative_path = f"receipts/{fy}/{filename}"
            logger.info(f"Generated receipt PDF: {relative_path}")
            
            return relative_path
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise Exception(f"Failed to generate PDF: {str(e)}")
    
    def get_financial_year(self, date: datetime) -> str:
        """Get financial year string (e.g., '2024-25')"""
        if date.month >= 4:  # April onwards
            return f"{date.year}-{str(date.year + 1)[-2:]}"
        else:
            return f"{date.year - 1}-{str(date.year)[-2:]}"