**********************
* Performs additional bespoke cleaning steps to create a regression ready dataset for the cohort analysis
* Collin Wardius 
* October 22, 2025
**********************

timer clear
timer on 1
cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/data_from_cluster/"
import delimited "revised_linked_1900_1940_census_treated_only.csv", clear

/*
Need to drop observations that only lived in a county that got one college in 1940
*/

egen min_year_hik = min(year) if treated ==1, by(hik)

egen t_min_year_hik = max(min_year_hik), by(hik)

drop if t_min_year_hik == 1940 // These are people who are only observed in a treated county in the last year. IE, we do not know if they were in a treated county before the last year.

drop min_year_hik t_min_year_hik

rename name college_name 
drop icpsrcty icpsrst // drop variables that are related to the college merge

lab var has_college "county had college before 1900"
lab var treated "exactly one college founded between 1900 and 1940 in the county"

replace treated = 0 if missing(treated) // This will include all counties other than those that gain exactly one college


* calculate the share of people that have multiple observations below 18

g below_18 = age <18

egen num_below_18 = total(below_18), by(hik)

* We can do some robustness around this but my plan was to keep the latest below 18 location assignment for each person

egen max_below18 = max(year) if below_18, by(hik)

* indicate whether the person moved

egen g_state_county = group(statefip countyicp)

sort hik year

bys hik: g t_moved_pre_18 = (g_state_county != g_state_county[_n-1]) & (below_18==1) & !missing(g_state_county) & !missing(g_state_county[_n-1])

egen moved_pre_18 = max(t_moved_pre_18), by(hik)

drop t_moved_pre_18

keep if (below_18 & year == max_below18) | year==1940

* keep only geographic information from the earlier year to merge later

preserve
drop if year == 1940
rename year year_before_18
rename statefip statefip_pre_18
rename countyicp countyicp_pre_18
rename g_state_county g_state_county_pre_18
rename age age_pre_18
rename birthyr birthyr_pre_18
rename icpsrnam icpsrnam_pre_18
rename statenam statenam_pre_18
rename region region_pre_18
keep hik statefip_pre_18 countyicp_pre_18 g_state_county_pre_18 year_before_18 college_name year_founding college_type treated icpsrnam_pre_18 statenam_pre_18 region_pre_18
tempfile before_data
save `before_data'
restore

* merge back on to the 1940 data

keep if year == 1940

* drop all variables relating to colleges from the 1940 data since this is immaterial for the analysis

drop treated has_college treated year_founding college_name college_type

merge 1:1 hik using `before_data', nogen

/*
birthyr seems to be more accurately reported in 1940 so use this as the birthyear
There is limited disagreement between birthyears across hiks but it is limited
In general, I will be assuming that the 1940 census is more accurate when adjudacating
between different versions of the same data.
*/

* drop if treated = 0. These are people who must have initially lived in a place that would have a college, but they then moved away.

drop if treated == 0 


* define the projected year at which the individual turns 18

g year_at_18 = birthyr + 18

* define the difference between the founding year of a college and the age cohort
* here, positive values imply being treated, negative values imply not being treated

g treatment_cohort = year_at_18 - year_founding

g age_at_founding = year_founding - birthyr

g age_squared = age^2


* create a college identifier I am going to make this the college name by year founded by county identifier

egen college_id = group(college_name year_founding g_state_county_pre_18)

/* 
egen count_by_group = total(count), by(college_name age_at_founding)

egen min_by_college = min(count_by_group), by(college_name) 
*/

* create some indicator of whether you moved pre 18 for college

g state_moved_pre_18 = (statefip_pre_18 != bpl) // This would include both within US moves as well as moved from some other country to the US.

save cleaned_opening_regression_data, replace

* create an additional dataset of desciptives on the counties that are treated

keep college_id college_name college_type college_id year_founding statenam_pre_18 icpsrnam_pre_18 countyicp_pre_18 statefip_pre_18 g_state_county_pre_18

duplicates drop college_id, force

save "treated_colleges_counties", replace

timer off 1
timer list 1
timer clear










