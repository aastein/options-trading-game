from __future__ import annotations

import unittest

from options.bs_pricer import BlackScholesPricer


class TestBlackScholesPricer(unittest.TestCase):
    
    def setUp(self):
        self.pricer = BlackScholesPricer(risk_free_rate=0.045)
    
    def test_call_price_atm(self):
        price = self.pricer.price_call(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            volatility=0.20
        )
        
        self.assertGreater(price, 0)
        self.assertLess(price, 100.0)
    
    def test_put_price_atm(self):
        price = self.pricer.price_put(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            volatility=0.20
        )
        
        self.assertGreater(price, 0)
        self.assertLess(price, 100.0)
    
    def test_call_delta(self):
        delta = self.pricer.calculate_delta(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            volatility=0.20,
            option_type="call"
        )
        
        self.assertGreater(delta, 0)
        self.assertLess(delta, 1)
    
    def test_put_delta(self):
        delta = self.pricer.calculate_delta(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            volatility=0.20,
            option_type="put"
        )
        
        self.assertLess(delta, 0)
        self.assertGreater(delta, -1)
    
    def test_gamma(self):
        gamma = self.pricer.calculate_gamma(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            volatility=0.20
        )
        
        self.assertGreater(gamma, 0)
    
    def test_zero_expiry_call_itm(self):
        price = self.pricer.price_call(
            spot=105.0,
            strike=100.0,
            time_to_expiry=0.0,
            volatility=0.20
        )
        
        self.assertAlmostEqual(price, 5.0, delta=0.01)
    
    def test_zero_expiry_call_otm(self):
        price = self.pricer.price_call(
            spot=95.0,
            strike=100.0,
            time_to_expiry=0.0,
            volatility=0.20
        )
        
        self.assertAlmostEqual(price, 0.0, delta=0.01)


if __name__ == '__main__':
    unittest.main()
