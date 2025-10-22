**********************
* Performs regression analysis of college openings
* Collin Wardius 
* October 22, 2025
**********************

cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/data_from_cluster/"
use cleaned_opening_regression_data, clear


drop if min_by_college < 200


*******************
* First approach is just a basic regression with county fixed effects
*******************

eststo: reghdfe college  ib20.age_at_founding, absorb(g_state_county_pre_18 nativity race hispan mbpl fbpl sex) vce(cl hik)



eststo: reghdfe college ib20.age_at_founding, absorb(g_state_county_pre_18 g_state_county_pre_18#c.treatment_cohort nativity race hispan mbpl fbpl sex) vce(cl hik)

******************
* Next approach is the DD approach 
******************


