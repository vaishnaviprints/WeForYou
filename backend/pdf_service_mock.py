import os
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        self.use_local = os.environ.get('USE_LOCAL_STORAGE', 'true').lower() == 'true'
        self.local_path = Path(os.environ.get('LOCAL_STORAGE_PATH', '/app/backend/storage'))
        self.local_path.mkdir(parents=True, exist_ok=True)
        
    def generate_receipt_html(self, donation: dict, user: dict, campaign: dict, receipt: dict) -> str:
        """Generate simple HTML (mock)"""
        return f"<html><body><h1>Receipt: {receipt['receipt_number']}</h1></body></html>"
    
    async def generate_receipt_pdf(self, donation: dict, user: dict, campaign: dict, receipt: dict) -> str:
        """Mock PDF generation - returns path"""
        fy = receipt['fy']
        receipt_number = receipt['receipt_number']
        filename = f"WFY-{receipt_number}-{fy}.pdf"
        
        fy_dir = self.local_path / 'receipts' / fy
        fy_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = fy_dir / filename
        
        # Create a mock PDF file
        with open(file_path, 'w') as f:
            f.write("MOCK PDF RECEIPT - WeasyPrint not available in this environment")
        
        relative_path = f"receipts/{fy}/{filename}"
        logger.info(f"Generated mock receipt: {relative_path}")
        
        return relative_path
    
    def get_financial_year(self, date: datetime) -> str:
        """Get financial year string"""
        if date.month >= 4:
            return f"{date.year}-{str(date.year + 1)[-2:]}"
        else:
            return f"{date.year - 1}-{str(date.year)[-2:]}"
