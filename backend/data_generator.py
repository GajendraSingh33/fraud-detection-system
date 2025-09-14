import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import uuid

class TransactionDataGenerator:
    """Generate realistic transaction data for testing and real-time simulation"""
    
    def __init__(self):
        self.merchant_types = ['grocery', 'gas', 'restaurant', 'online', 'atm', 'pharmacy', 'entertainment', 'travel', 'unknown']
        self.time_periods = ['morning', 'afternoon', 'evening', 'night']
        self.card_types = ['debit', 'credit', 'prepaid']
        
        # Realistic location data with weights
        self.locations = [
            'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX', 'Phoenix, AZ',
            'Philadelphia, PA', 'San Antonio, TX', 'San Diego, CA', 'Dallas, TX', 'San Jose, CA',
            'Austin, TX', 'Jacksonville, FL', 'Fort Worth, TX', 'Columbus, OH', 'Charlotte, NC',
            'San Francisco, CA', 'Indianapolis, IN', 'Seattle, WA', 'Denver, CO', 'Boston, MA',
            'Unknown Location', 'Foreign Country'
        ]
        
        # Merchant-specific amount ranges
        self.merchant_amount_ranges = {
            'grocery': (5, 200),
            'gas': (20, 120),
            'restaurant': (8, 150),
            'online': (10, 2000),
            'atm': (20, 500),
            'pharmacy': (5, 100),
            'entertainment': (15, 300),
            'travel': (50, 5000),
            'unknown': (1, 10000)
        }
        
        # Time-based transaction probabilities
        self.hourly_weights = {
            0: 0.5, 1: 0.2, 2: 0.1, 3: 0.1, 4: 0.1, 5: 0.3,
            6: 0.8, 7: 1.2, 8: 1.5, 9: 1.8, 10: 2.0, 11: 2.2,
            12: 2.5, 13: 2.3, 14: 2.0, 15: 1.8, 16: 1.9, 17: 2.1,
            18: 2.3, 19: 2.0, 20: 1.5, 21: 1.2, 22: 0.8, 23: 0.6
        }
        
        # User profiles for realistic patterns
        self.user_profiles = {
            'normal_user': {
                'avg_daily_transactions': 3,
                'preferred_merchants': ['grocery', 'gas', 'restaurant'],
                'avg_amount': 75,
                'fraud_probability': 0.001
            },
            'heavy_user': {
                'avg_daily_transactions': 8,
                'preferred_merchants': ['online', 'restaurant', 'entertainment'],
                'avg_amount': 120,
                'fraud_probability': 0.005
            },
            'business_user': {
                'avg_daily_transactions': 12,
                'preferred_merchants': ['travel', 'online', 'restaurant'],
                'avg_amount': 300,
                'fraud_probability': 0.008
            },
            'suspicious_user': {
                'avg_daily_transactions': 2,
                'preferred_merchants': ['unknown', 'online', 'atm'],
                'avg_amount': 500,
                'fraud_probability': 0.15
            }
        }
    
    def generate_transaction(self, user_profile: str = None) -> Dict:
        """Generate a single realistic transaction"""
        
        # Select user profile
        if user_profile is None:
            user_profile = random.choices(
                list(self.user_profiles.keys()),
                weights=[70, 20, 8, 2]  # Most users are normal
            )[0]
        
        profile = self.user_profiles[user_profile]
        
        # Determine if this should be a fraudulent transaction
        is_fraud_attempt = random.random() < profile['fraud_probability']
        
        if is_fraud_attempt:
            return self._generate_fraud_transaction()
        else:
            return self._generate_normal_transaction(profile)
    
    def _generate_normal_transaction(self, profile: Dict) -> Dict:
        """Generate a normal transaction based on user profile"""
        
        # Select merchant type based on profile preferences
        merchant_type = random.choice(profile['preferred_merchants'])
        
        # Generate amount based on merchant and profile
        min_amount, max_amount = self.merchant_amount_ranges[merchant_type]
        base_amount = random.uniform(min_amount, max_amount)
        
        # Adjust based on profile
        amount = base_amount * random.uniform(0.5, 1.5) * (profile['avg_amount'] / 75)
        amount = round(max(amount, 0.01), 2)
        
        # Select time based on realistic patterns
        hour = self._generate_realistic_hour()
        time_of_day = self._hour_to_period(hour)
        
        # Select location (mostly domestic for normal users)
        location = random.choices(
            self.locations,
            weights=[5] * 20 + [1, 0.1]  # Very low weight for unknown/foreign
        )[0]
        
        # Select card type (normal distribution)
        card_type = random.choices(
            self.card_types,
            weights=[50, 45, 5]  # Mostly debit/credit, few prepaid
        )[0]
        
        return {
            'amount': amount,
            'merchant_type': merchant_type,
            'location': location,
            'time_of_day': time_of_day,
            'card_type': card_type,
            'user_profile': 'normal'
        }
    
    def _generate_fraud_transaction(self) -> Dict:
        """Generate a fraudulent transaction with suspicious patterns"""
        
        fraud_patterns = [
            'high_amount_unknown_merchant',
            'multiple_small_amounts',
            'foreign_location',
            'unusual_time',
            'prepaid_card_pattern'
        ]
        
        pattern = random.choice(fraud_patterns)
        
        if pattern == 'high_amount_unknown_merchant':
            return {
                'amount': round(random.uniform(1000, 15000), 2),
                'merchant_type': 'unknown',
                'location': random.choice(['Unknown Location', 'Foreign Country']),
                'time_of_day': 'night',
                'card_type': random.choice(['credit', 'prepaid']),
                'user_profile': 'fraudulent'
            }
        
        elif pattern == 'multiple_small_amounts':
            return {
                'amount': round(random.uniform(0.01, 50), 2),
                'merchant_type': random.choice(['online', 'unknown']),
                'location': random.choice(self.locations[-2:]),  # Unknown/Foreign
                'time_of_day': random.choice(['night', 'evening']),
                'card_type': 'prepaid',
                'user_profile': 'fraudulent'
            }
        
        elif pattern == 'foreign_location':
            return {
                'amount': round(random.uniform(100, 3000), 2),
                'merchant_type': random.choice(['online', 'travel', 'unknown']),
                'location': 'Foreign Country',
                'time_of_day': random.choice(['night', 'morning']),
                'card_type': random.choice(['credit', 'prepaid']),
                'user_profile': 'fraudulent'
            }
        
        elif pattern == 'unusual_time':
            return {
                'amount': round(random.uniform(200, 5000), 2),
                'merchant_type': random.choice(['atm', 'online', 'unknown']),
                'location': random.choice(['Unknown Location'] + self.locations[:10]),
                'time_of_day': 'night',
                'card_type': random.choice(self.card_types),
                'user_profile': 'fraudulent'
            }
        
        elif pattern == 'prepaid_card_pattern':
            return {
                'amount': round(random.uniform(50, 1000), 2),
                'merchant_type': random.choice(['online', 'atm', 'unknown']),
                'location': random.choice(self.locations),
                'time_of_day': random.choice(self.time_periods),
                'card_type': 'prepaid',
                'user_profile': 'fraudulent'
            }
        
        # Default fraud pattern
        return {
            'amount': round(random.uniform(500, 10000), 2),
            'merchant_type': 'unknown',
            'location': 'Unknown Location',
            'time_of_day': 'night',
            'card_type': 'prepaid',
            'user_profile': 'fraudulent'
        }
    
    def _generate_realistic_hour(self) -> int:
        """Generate hour based on realistic transaction patterns"""
        hours = list(range(24))
        weights = [self.hourly_weights[h] for h in hours]
        return random.choices(hours, weights=weights)[0]
    
    def _hour_to_period(self, hour: int) -> str:
        """Convert hour to time period"""
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 22:
            return 'evening'
        else:
            return 'night'
    
    def generate_batch_transactions(self, count: int) -> List[Dict]:
        """Generate a batch of transactions"""
        transactions = []
        for _ in range(count):
            transactions.append(self.generate_transaction())
        return transactions
    
    def generate_user_session(self, user_profile: str = 'normal_user', session_length: int = None) -> List[Dict]:
        """Generate a series of transactions for a single user session"""
        profile = self.user_profiles[user_profile]
        
        if session_length is None:
            session_length = max(1, int(np.random.poisson(profile['avg_daily_transactions'])))
        
        transactions = []
        base_time = datetime.now()
        
        for i in range(session_length):
            # Add some time variance between transactions
            transaction_time = base_time + timedelta(
                minutes=random.randint(5, 120)
            )
            
            transaction = self.generate_transaction(user_profile)
            transaction['timestamp'] = transaction_time
            transaction['session_id'] = str(uuid.uuid4())[:8]
            transactions.append(transaction)
            
            base_time = transaction_time
        
        return transactions
    
    def get_merchant_statistics(self) -> Dict:
        """Get statistics about merchant types for model training"""
        return {
            'merchant_types': self.merchant_types,
            'amount_ranges': self.merchant_amount_ranges,
            'risk_levels': {
                'grocery': 'low',
                'gas': 'low',
                'restaurant': 'low',
                'pharmacy': 'low',
                'entertainment': 'medium',
                'online': 'medium',
                'travel': 'medium',
                'atm': 'high',
                'unknown': 'high'
            }
        }
    
    def simulate_peak_hours(self) -> Dict:
        """Simulate transaction volume during peak hours"""
        current_hour = datetime.now().hour
        base_volume = 100
        
        # Multiply by hourly weight
        peak_volume = int(base_volume * self.hourly_weights.get(current_hour, 1.0))
        
        # Generate transactions for current conditions
        transactions = []
        for _ in range(peak_volume):
            transaction = self.generate_transaction()
            transaction['peak_hour'] = True
            transaction['volume_multiplier'] = self.hourly_weights.get(current_hour, 1.0)
            transactions.append(transaction)
        
        return {
            'hour': current_hour,
            'expected_volume': peak_volume,
            'transactions': transactions,
            'peak_factor': self.hourly_weights.get(current_hour, 1.0)
        }