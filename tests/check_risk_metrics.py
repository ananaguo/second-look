import math
import unittest
from risk_metrics import calculate_risk


def data(returns):
    return [dict(year=1950+i, stocks=r) for i,r in enumerate(returns)]


class RiskTests(unittest.TestCase):
    def test_known_tail_and_drawdown(self):
        m=calculate_risk(data([-40,-30,-20,-10]+[0]*36),'stocks')
        self.assertEqual(m['var_pct'],20)
        self.assertAlmostEqual(m['es_pct'],35)
        self.assertAlmostEqual(m['drawdown_pct'],69.76)
        self.assertEqual(m['loss_frequency_pct'],10)
        self.assertEqual(m['var_dollars'],2000)

    def test_fractional_tail(self):
        m=calculate_risk(data([-40,-30,-20,-10]+[0]*39),'stocks')
        self.assertAlmostEqual(m['es_pct'],(40+30+0.15*20)/2.15)

    def test_positive_returns(self):
        m=calculate_risk(data([3]*40),'stocks')
        self.assertEqual(m['var_pct'],0)
        self.assertEqual(m['es_pct'],0)
        self.assertEqual(m['drawdown_pct'],0)

    def test_recovery_and_compounding(self):
        m=calculate_risk(data([100,-50]+[0]*38),'stocks')
        self.assertEqual(m['drawdown_pct'],50)

    def test_total_loss(self):
        m=calculate_risk(data([-100]+[0]*39),'stocks')
        self.assertEqual(m['drawdown_pct'],100)

    def test_amount_scaling(self):
        rows=data([-40,-30,-20]+[0]*37)
        a=calculate_risk(rows,'stocks');b=calculate_risk(rows,'stocks',amount=20000)
        self.assertEqual(b['var_dollars'],2*a['var_dollars'])
        self.assertEqual(b['var_pct'],a['var_pct'])

    def test_invalid_inputs(self):
        for rows in ([],data([1]*39),data([float('nan')]*40),data([-101]*40)):
            with self.assertRaises(ValueError):calculate_risk(rows,'stocks')
        rows=data([0]*40);rows[2]['year']=rows[1]['year']
        with self.assertRaises(ValueError):calculate_risk(rows,'stocks')

    def test_order_independence(self):
        rows=data([-40,-30,-20]+[0]*37)
        self.assertEqual(calculate_risk(rows,'stocks'),calculate_risk(rows[::-1],'stocks'))

if __name__=='__main__':unittest.main()
