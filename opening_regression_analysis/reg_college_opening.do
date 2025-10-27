**********************
* Performs regression analysis of college openings
* Collin Wardius 
* October 22, 2025
**********************

est clear
cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/data_from_cluster/"
use cleaned_opening_regression_data, clear

cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output"

* create a treatment indicator

g has_new_college = (year_founding <= year_at_18) // year founding is going to depend on the county of the person and year_at_18 is essentially just an age cohort.


* prakash's recommendation is to recode people that are well older / younger to the max / min age

replace age_at_founding = 25 if age_at_founding > 25
replace age_at_founding = 9 if age_at_founding < 9


est clear
eststo: reghdfe college  ib17.age_at_founding, absorb(g_state_county_pre_18 birthyr nativity race hispan mbpl fbpl sex moved_pre_18 state_moved_pre_18) vce(cl g_state_county_pre_18)
estadd ysumm
estadd scalar N_counties=e(N_clust)

coefplot, ///
    keep(*age_at_founding) ///
    vertical ///
    yline(0, lcolor(black) lpattern(dash)) ///
    coeflabels(25.age_at_founding = "25" ///
                24.age_at_founding = "24" ///
                23.age_at_founding = "23" ///
                22.age_at_founding = "22" ///
                21.age_at_founding = "21" ///
                20.age_at_founding = "20" ///
                19.age_at_founding = "19" ///
                18.age_at_founding = "18" ///
                17.age_at_founding = "17" ///
                16.age_at_founding = "16" ///
                15.age_at_founding = "15" ///
                14.age_at_founding = "14" ///
                13.age_at_founding = "13" ///
                12.age_at_founding = "12" ///
                11.age_at_founding = "11" ///
                10.age_at_founding = "10" ///
                9.age_at_founding = "9") ///
    xlabel(, angle(0)) ///
    ytitle("Effect on College Attendance") ///
    subtitle("Region by Cohort Trends") ///
    xtitle("Age at College Founding") ///
    graphregion(color(white)) bgcolor(white) ///
    legend(off) ///
    baselevels ///
    xscale(reverse) ///
    mcolor(navy) ciopts(lcolor(navy))

graph export "figures/twfe_college_attainment_baseline.png", replace



est clear
eststo: reghdfe college  ib17.age_at_founding, absorb(g_state_county_pre_18 birthyr nativity race hispan mbpl fbpl sex moved_pre_18 state_moved_pre_18 region_pre_18#c.age_at_founding) vce(cl g_state_county_pre_18)
estadd ysumm
estadd scalar N_counties=e(N_clust)

coefplot, ///
    keep(*age_at_founding) ///
    vertical ///
    yline(0, lcolor(black) lpattern(dash)) ///
    coeflabels(25.age_at_founding = "25" ///
                24.age_at_founding = "24" ///
                23.age_at_founding = "23" ///
                22.age_at_founding = "22" ///
                21.age_at_founding = "21" ///
                20.age_at_founding = "20" ///
                19.age_at_founding = "19" ///
                18.age_at_founding = "18" ///
                17.age_at_founding = "17" ///
                16.age_at_founding = "16" ///
                15.age_at_founding = "15" ///
                14.age_at_founding = "14" ///
                13.age_at_founding = "13" ///
                12.age_at_founding = "12" ///
                11.age_at_founding = "11" ///
                10.age_at_founding = "10" ///
                9.age_at_founding = "9") ///
    xlabel(, angle(0)) ///
    ytitle("Effect on College Attendance") ///
    subtitle("Region by Cohort Trends") ///
    xtitle("Age at College Founding") ///
    graphregion(color(white)) bgcolor(white) ///
    legend(off) ///
    baselevels ///
    xscale(reverse) ///
    mcolor(navy) ciopts(lcolor(navy))

graph export "figures/twfe_college_attainment_regional_trends.png", replace

est clear
eststo: reghdfe college  ib17.age_at_founding, absorb(g_state_county_pre_18 birthyr nativity race hispan mbpl fbpl sex moved_pre_18 state_moved_pre_18 g_state_county_pre_18#c.age_at_founding) vce(cl g_state_county_pre_18)
estadd ysumm
estadd scalar N_counties=e(N_clust)

coefplot, ///
    keep(*age_at_founding) ///
    vertical ///
    yline(0, lcolor(black) lpattern(dash)) ///
    coeflabels(25.age_at_founding = "25" ///
                24.age_at_founding = "24" ///
                23.age_at_founding = "23" ///
                22.age_at_founding = "22" ///
                21.age_at_founding = "21" ///
                20.age_at_founding = "20" ///
                19.age_at_founding = "19" ///
                18.age_at_founding = "18" ///
                17.age_at_founding = "17" ///
                16.age_at_founding = "16" ///
                15.age_at_founding = "15" ///
                14.age_at_founding = "14" ///
                13.age_at_founding = "13" ///
                12.age_at_founding = "12" ///
                11.age_at_founding = "11" ///
                10.age_at_founding = "10" ///
                9.age_at_founding = "9") ///
    xlabel(, angle(0)) ///
    ytitle("Effect on College Attendance") ///
    subtitle("Region by Cohort Trends") ///
    xtitle("Age at College Founding") ///
    graphregion(color(white)) bgcolor(white) ///
    legend(off) ///
    baselevels ///
    xscale(reverse) ///
    mcolor(navy) ciopts(lcolor(navy))

graph export "figures/twfe_college_attainment_county_trends.png", replace

* try the DiD imputation estimator 
/*
Note here that the first period is the reference period.
*/


did_imputation college hik year_at_18 year_founding ///
    , horizons(0/8) pretrend(8)  ///
    fe(year_at_18 g_state_county_pre_18 nativity race hispan sex moved_pre_18 state_moved_pre_18) ///
    cluster(g_state_county_pre_18) ///
    autosample
event_plot, default_look graph_opt(xtitle("Age at college founding") ytitle("Average causal effect on college attainment") ///
	title("") legend(position(6) rows(1)) xlabel(-8 "23" -7 "24" -6 "23" -5 "22" -4 "21" -3 "20" -2 "19" -1 "18" 0 "17" 1 "16" 2 "15" 3 "14" 4 "13" 5 "12" 6 "11" 7 "10" 8 "9")) 
graph export "figures/did_imputation_college_attainment_baseline.png", replace


did_imputation college hik year_at_18 year_founding ///
    , horizons(0/8) pretrend(8)  ///
    fe(year_at_18 g_state_county_pre_18 nativity race hispan sex moved_pre_18 state_moved_pre_18 region_pre_18#c.age_at_founding) ///
    cluster(g_state_county_pre_18) ///
    autosample
event_plot, default_look graph_opt(xtitle("Age at college founding") ytitle("Average causal effect on college attainment") ///
	title("") legend(position(6) rows(1)) xlabel(-8 "23" -7 "24" -6 "23" -5 "22" -4 "21" -3 "20" -2 "19" -1 "18" 0 "17" 1 "16" 2 "15" 3 "14" 4 "13" 5 "12" 6 "11" 7 "10" 8 "9")) 
graph export "figures/did_imputation_college_attainment_regional_trends.png", replace


did_imputation college hik year_at_18 year_founding ///
    , horizons(0/8) pretrend(8)  ///
    fe(year_at_18 g_state_county_pre_18 nativity race hispan sex moved_pre_18 state_moved_pre_18 region_pre_18#c.age_at_founding) ///
    cluster(g_state_county_pre_18) ///
    autosample
event_plot, default_look graph_opt(xtitle("Age at college founding") ytitle("Average causal effect on college attainment") ///
	title("") legend(position(6) rows(1)) xlabel(-8 "23" -7 "24" -6 "23" -5 "22" -4 "21" -3 "20" -2 "19" -1 "18" 0 "17" 1 "16" 2 "15" 3 "14" 4 "13" 5 "12" 6 "11" 7 "10" 8 "9")) 
graph export "figures/did_imputation_college_attainment_county_trends.png", replace





/*
* try to run just a standard two way fixed effects regression

est clear

eststo: reghdfe college  has_new_college, absorb(g_state_county_pre_18 birthyr nativity race hispan mbpl fbpl sex moved_pre_18 state_moved_pre_18) vce(cl g_state_county_pre_18)
estadd ysumm
estadd scalar N_counties=e(N_clust)

eststo: reghdfe ba has_new_college, absorb(g_state_county_pre_18 birthyr nativity race hispan mbpl fbpl sex moved_pre_18) vce(cl g_state_county_pre_18)
estadd ysumm
estadd scalar N_counties=e(N_clust)

esttab est1 est2 using "tables/college_opening_regs.tex", ///
      replace ///
      label ///
      b(3) se(3) ///
      star(* 0.10 ** 0.05 *** 0.01) ///
      title("Effect of College Opening on College Attainment") ///
      mtitles("Any College" "BA Degree") ///
      scalars("N_counties N counties" "N Observations" "ymean Mean of Dep. Var." ) ///
      sfmt(%9.0f %9.0f %9.3f) ///
      coefl(has_new_college "Exposed to new college") ///
      note("All regressions control for county and age cohort FE. SEs clustered at the county level.") ///
      nocons








* try the in-built stata command


hdidregress aipw (college i.nativity i.race i.hispan i.mbpl i.fbpl i.sex) ///
    (has_new_college), time(year_at_18) group(g_state_county_pre_18)


/*
eststo: reghdfe college  ib17.age_at_founding, absorb(g_state_county_pre_18 nativity race hispan mbpl fbpl sex) vce(cl hik)
estadd ysumm
*/


* try the csdid package 


csdid college i.g_state_county_pre_18 i.nativity i.race i.hispan i.mbpl i.fbpl i.sex ///
    , time(birthyr) gvar(year_founding) notyet


* use later treated counties as controls for earlier treated counties

levelsof college_name

foreach name in `r(levels)' {
    preserve
    sum year_founding if college_name == "`name'"
    loc col_founding = `r(mean)'
    keep if college_name == "`name'" | year_founding >= `col_founding' + 5
    g now_treated = college_name == "`name'"
    g post =  (birthyr>= year_founding - 18)
    keep if inrange(birthyr, `col_founding'-23, `col_founding'-13)
    di "`college_name'"
    reghdfe college post#now_treated ///
        , vce(cl hik) absorb(g_state_county_pre_18  nativity race hispan mbpl fbpl sex)
    restore
}
*/