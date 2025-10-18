
import requests
import hashlib
from decimal import Decimal
from typing import Dict, Optional
from django.conf import settings


class SSLCommerzPayment:
    """SSLCommerz payment gateway handler"""
    
    def __init__(self):
        self.store_id = getattr(settings, 'SSLCOMMERZ_STORE_ID', '')
        self.store_password = getattr(settings, 'SSLCOMMERZ_STORE_PASSWORD', '')
        self.is_sandbox = getattr(settings, 'SSLCOMMERZ_IS_SANDBOX', True)
        
        # API endpoints
        if self.is_sandbox:
            self.base_url = "https://sandbox.sslcommerz.com"
        else:
            self.base_url = "https://securepay.sslcommerz.com"
    
    def create_session(self, payment_data: Dict) -> Dict:
        """
        Initialize payment session
        
        Required fields in payment_data:
        - total_amount: Decimal
        - currency: str (default: BDT)
        - tran_id: str (unique transaction ID)
        - success_url: str
        - fail_url: str
        - cancel_url: str
        - cus_name: str
        - cus_email: str
        - cus_phone: str
        - product_name: str
        - product_category: str
        """
        
        url = f"{self.base_url}/gwprocess/v4/api.php"
        
        # Prepare payload
        payload = {
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'total_amount': str(payment_data['total_amount']),
            'currency': payment_data.get('currency', 'BDT'),
            'tran_id': payment_data['tran_id'],
            'success_url': payment_data['success_url'],
            'fail_url': payment_data['fail_url'],
            'cancel_url': payment_data['cancel_url'],
            'ipn_url': payment_data.get('ipn_url', ''),
            
            # Customer info
            'cus_name': payment_data['cus_name'],
            'cus_email': payment_data['cus_email'],
            'cus_add1': payment_data.get('cus_add1', 'Dhaka'),
            'cus_city': payment_data.get('cus_city', 'Dhaka'),
            'cus_postcode': payment_data.get('cus_postcode', '1000'),
            'cus_country': payment_data.get('cus_country', 'Bangladesh'),
            'cus_phone': payment_data['cus_phone'],
            
            # Product info
            'product_name': payment_data['product_name'],
            'product_category': payment_data['product_category'],
            'product_profile': payment_data.get('product_profile', 'general'),
            
            # Shipping (optional)
            'shipping_method': payment_data.get('shipping_method', 'NO'),
            'num_of_item': payment_data.get('num_of_item', 1),
            
            # EMI options (optional)
            'emi_option': payment_data.get('emi_option', 0),
        }
        
        try:
            response = requests.post(url, data=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'status': 'FAILED',
                'failedreason': str(e)
            }
    
    def validate_transaction(self, val_id: str, tran_id: str) -> Dict:
        """
        Validate transaction after payment
        
        Args:
            val_id: Validation ID from SSLCommerz
            tran_id: Transaction ID
        """
        url = f"{self.base_url}/validator/api/validationserverAPI.php"
        
        params = {
            'val_id': val_id,
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'format': 'json'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'status': 'FAILED',
                'failedreason': str(e)
            }
    
    def initiate_refund(self, bank_tran_id: str, refund_amount: Decimal, refund_remarks: str = '') -> Dict:
        """
        Initiate refund
        
        Args:
            bank_tran_id: Bank transaction ID from SSLCommerz
            refund_amount: Amount to refund
            refund_remarks: Reason for refund
        """
        url = f"{self.base_url}/validator/api/merchantTransIDvalidationAPI.php"
        
        payload = {
            'refund_amount': str(refund_amount),
            'refund_remarks': refund_remarks or 'Customer requested refund',
            'bank_tran_id': bank_tran_id,
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'format': 'json'
        }
        
        try:
            response = requests.get(url, params=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'status': 'FAILED',
                'errorReason': str(e)
            }
    
    def query_transaction(self, tran_id: str) -> Dict:
        """
        Query transaction status
        
        Args:
            tran_id: Transaction ID
        """
        url = f"{self.base_url}/validator/api/merchantTransIDvalidationAPI.php"
        
        params = {
            'tran_id': tran_id,
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'format': 'json'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'status': 'FAILED',
                'errorReason': str(e)
            }