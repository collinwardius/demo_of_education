*****************************
* Preliminary figures tracking changes in college degree holders over time
* Collin Wardius
* August 14, 2025
*****************************

clear all
clear mata
grstyle init
grstyle set plain

gl figures_path "output/figures"
gl clean_data_path "data/clean"
gl table_path "output/tables"

cd "C:\Users\sandera-cwardius\OneDrive - UC San Diego\demo of education"
use "data/usa_00015", clear
// use if statefip == 6 ///
// 	using "data/usa_00014", clear

* drop observations where education is missing

drop if missing(educ) // this implicitly restricts to 1940


* create indicators for the amount of college completed

g ba_complete = (educ == 10)

g any_college = (inrange(educ,7,11))

g some_college = (inrange(educ,7,9))

g ba_or_above = (inrange(educ, 10,11))

g hs_complete = (educ==6)

g hs_or_above = (inrange(educ,6,11))

lab var ba_complete "ba completer"
lab var any_college "any college education"
lab var some_college "some college"
lab var ba_or_above "ba or more college"
lab var hs_complete "hs completer"
lab var hs_or_above "hs or more"

* create an indicator for female

g female = (sex==2)

* estimate the year of college completion

g est_hs_grad_year = birthyr + 22
g est_col_grad_year = birthyr + 22


* create an native-born indicator

g native_born = (inrange(bpl,1,56))

* create broad regional categories

recode region (11/12=1) (21/22=2) (31/33=3) (41/42=4), gen(broad_region)

lab def region_lab 1 "northeast" 2 "midwest" 3 "south" 4 "west"
lab val broad_region region_lab

/*
Import and merge state funding data from 1937-1938
*/

preserve
import delimited "data/clean/state_higher_ed_receipts_1937_38", clear
statastates, name(state)
drop if _merge ==2
rename v2 univ_funding_per_capita
rename state_fips bpl
keep bpl univ_funding_per_capita
tempfile univ_funding
save `univ_funding'
restore

merge m:1 bpl using `univ_funding', nogen 

/*
Import and merge enrollment share
*/

preserve
import excel "data/clean/total_public_enroll_1937_38.xlsx", clear firstrow
drop if state == "District of Columbia"
statastates, name(state)
keep if _merge==3
drop _merge
rename state_fips bpl
g public_share = state_enrollment/total_enrollment
tempfile enrollment
save `enrollment'
restore

merge m:1 bpl using `enrollment', nogen

* relationship between funding and collegegoing

preserve
keep if native_born & est_hs_grad_year==1936
collapse (mean) ba_or_above univ_funding_per_capita public_share, by(bpl)
replace univ_funding_per_capita = ln(univ_funding_per_capita)

lab var ba_or_above "BA completion"
lab var univ_funding_per_capita "log state funding per capita"
lab var public_share "public share of total enrollment"

// Run your regressions and store the results
reg ba_or_above univ_funding_per_capita, robust
estimates store model1

reg ba_or_above public_share univ_funding_per_capita, robust  
estimates store model2


// Create LaTeX table using esttab
esttab model1 model2 using "$table_path/state_funding_and_attainment_regs.tex", ///
    replace ///
    booktabs ///
    title("Education Attainment and University Funding") ///
    mtitles("BA or Above" "BA or Above") ///
    label ///
    b(3) se(3) ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    stats(N r2, fmt(0 3) labels("Observations" "R-squared")) ///
    nonumbers ///
    compress
est clear




reg ba_or_above public_share, robust
predict double resid, residuals
twoway (scatter ba_or_above univ_funding_per_capita, mlabel(bpl) mlabsize(small) mlabposition(12)) ///
       (lfit ba_or_above univ_funding_per_capita, lcolor(red) lwidth(medium)), ///
       title("College Attainment vs State Funding Per Capita (1936)") ///
       xtitle("University Funding Per Capita") ///
       ytitle("Percentage with BA or Above") ///
	   ylabel(0(0.05).2) ///
       legend(off)
graph export "$figures_path/col_attainment_funding1936.png", as(png) replace

* create a new version splitting states into quadrants

sum ba_or_above, d
loc med_ba = r(p50)
sum univ_funding_per_capita, d
loc med_fund = r(p50)

twoway (scatter ba_or_above univ_funding_per_capita, mlabel(bpl) mlabsize(small) mlabposition(12)) ///
       , title("College Attainment vs State Funding Per Capita (1936)") ///
       xtitle("University Funding Per Capita") ///
       ytitle("Percentage with BA or Above") ///
       legend(off) ///
	   yline(`med_ba', lcolor(red)) ///
	   ylabel(0(0.05).2) ///
	   xline(`med_fund', lcolor(red))
graph export "$figures_path/col_attainment_funding_quadrants1936.png", as(png) replace

twoway (scatter resid univ_funding_per_capita, mlabel(bpl) mlabsize(small) mlabposition(12)) ///
       (lfit resid univ_funding_per_capita, lcolor(red) lwidth(medium)), ///
       title("College Attainment vs State Funding Per Capita (1936)") ///
	   subtitle("controlling for public share") ///
       xtitle("University Funding Per Capita") ///
       ytitle("residualized percentage with BA or above") ///
	   ylabel(0(0.05).2) ///
       legend(off)
graph export "$figures_path/col_attainment_funding_control_public_share1936.png", as(png) replace



restore

/*
Do a CV calculation for college and HS
Redo the above scatter plot controlling for the private share of enrollment
Look at what college grads are doing across space.
*/

/*
Bar graph comparing attainment across regions for different age cohorts
*/

preserve
keep if inlist(birthyr, 1880, 1910)
collapse (mean) ba_or_above hs_or_above, by(birthyr broad_region)
* Two bars per region: one for 1890, one for 1910
graph bar (asis) ba_or_above, ///
    over(birthyr) over(broad_region) ///
    asyvars ///
    title("BA Attainment: 1880 vs 1910 Birth Cohorts") ///
    ytitle("Proportion with BA or Above") ///
    legend(label(1 "Born 1880") label(2 "Born 1910"))
graph export "$figures_path/ba_by_region.png", as(png) replace

graph bar (asis) hs_or_above, ///
    over(birthyr) over(broad_region) ///
    asyvars ///
    title("HS Attainment: 1880 vs 1910 Birth Cohorts") ///
    ytitle("Proportion with HS or Above") ///
    legend(label(1 "Born 1880") label(2 "Born 1910"))
graph export "$figures_path/hs_by_region.png", as(png) replace
restore




/*
Over birth cohorts, plot the r squared over time
*/

// This ended up not being very informative
// tempname results
// tempfile rsquareds
// postfile `results' year r_squared n_obs college using "`rsquareds'.dta", replace
//
// * Loop through years (adjust range as needed)
// forvalues year = 1880(5)1910 {
// 	preserve
// 	keep if birthyr == `year' & native_born
//     * Run regression for this year only
//     reghdfe ba_or_above, absorb(bpl)
//   
//     * Post the year, R-squared, and sample size
//     post `results' (`year') (`e(r2)') (`e(N)') (1)
//	
// 	* Run regression for this year only
// 	reg hs_or_above, absorb(bpl) 
//   
//     * Post the year, R-squared, and sample size
//     post `results' (`year') (`e(r2)') (`e(N)') (0)
// 	restore
// }
//
// * Close the postfile and save results
// postclose `results'
//
// * Load the results dataset
//
// preserve
// use "`rsquareds'.dta", clear
//
// separate r_squared, by(college)
//
// twoway connected `r(varlist)' year, msymbol(diamond) msize(small) lpattern(solid)
// restore


/*
The idea for a figure to see if the idea has legs is to compare
the probability of getting a college degree over states by cohort.

So for example, what share of people from California that would be college age in
1920 have a college degree relative to to those that would be college age in 1940.
*/ 

preserve
keep if native_born
g ba_or_above_cond_hs = ba_or_above if hs_or_above
g any_college_cond_hs = any_college if hs_or_above
collapse (mean) ba_or_above any_college ba_or_above_cond_hs any_college_cond_hs, by(bpl est_hs_grad_year)
export delimited $clean_data_path/cohort_col_by_state, replace
restore



/*
Two additional figures to make.

1. Bar graph showing the regional changes in college completion by birth year
2. Some coefficient of variation that shows that birth states becomes extremely important
in predicting the probability of college completion.

If there is some way you could show there was less regional variation in high school
attainment relative to college attainment, that would be nice.
*/ 



// preserve
// keep if female
// keep if inrange(est_year_of_college_grad, 1900,1940)
// collapse (mean) ba_complete, by(est_year_of_college_grad)
// sort est_year_of_college_grad
// line ba_complete est_year_of_college_grad, title("share of females with college degree") ///
// 	ytitle("share") ///
// 	xtitle("estimated graduation cohort")
// graph export "$figures_path/share_female_ba.png", as(png) replace
// restore


// preserve
// keep if year==1940
// keep if inrange(est_year_of_college_grad, 1900,1934)
// reg ba_complete i.female##i.est_year_of_college_grad
//
// * Calculate predicted probabilities by gender across years
// margins female, at(est_year_of_college_grad=(1900(4)1934))
//
// * Create the marginsplot
// marginsplot, ///
//     xlabel(1900(2)1934, angle(45)) ///
//     xtitle("Estimated Year of College Graduation") ///
//     ytitle("Predicted Probability of College Completion") ///
//     title("College Completion Rates by Gender Over Time") ///
//     legend(order(1 "Male" 2 "Female") position(6) cols(2))
// graph export "$figures_path/completion_by_gender.png", as(png) replace
// restore
//

