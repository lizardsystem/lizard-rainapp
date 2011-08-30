from unittest import TestCase
from math import log, exp

B_loc_1 = 17.9189977
B_loc_2 = 0.2245493
B_loc_3 = -3.5714538
B_loc_4 = 0.4264825
B_loc_5 = 0.1281047

B_shp_1 = -0.20559396
B_shp_2 = 0.01767472

B_disp_1 = 0.33739862
B_disp_2 = -0.01768042
B_disp_3 = -0.01398795



def herhalingstijd(bui_duur, oppervlak, neerslag_som):
   '''
      Berekend de herhalingstijd van de bui op basis van de duur, oppervlak en neerslag som
      bui_duur in [uren]
      oppervlak in [vierkante km]
      neerslag_som in [mm]
   '''

   #locatie parameter (formule 6 Aart)
   loc =  B_loc_1 * bui_duur**B_loc_2 + (B_loc_3 + B_loc_4 * log(bui_duur)) * oppervlak**B_loc_5
   #vorm parameter (formule 8 Aart)
   vorm = B_shp_1 + B_shp_2  * log(oppervlak)
   #dispersie/schaal parameter (formule 7 Aart)
   disp = B_disp_1 + B_disp_2 * log(bui_duur) + B_disp_3 * log(oppervlak)

   #afgeleide schaal parameter:
   schaal = disp * loc

   #herhalingstijd
   return round( 1 / ( 1 - (exp( - ( 1- (neerslag_som -loc) * (vorm/schaal) )**(1/vorm)) )), 0)

   
   
class computeTestSuite(TestCase):

   def runTest(self):
      """Test herhalingstijd calculation

      """
      self.assertAlmostEqual(25, herhalingstijd(24, 50, 62.82))
