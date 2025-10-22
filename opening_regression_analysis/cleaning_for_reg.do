**********************
* Performs additional bespoke cleaning steps to create a regression ready dataset for the cohort analysis
* Collin Wardius 
* October 22, 2025
**********************

cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/data_from_cluster/"
import delimited "linked_1900_1940_census_treated_only.csv", clear



rename name college_name 
drop icpsrcty icpsrst // drop variables that are related to the college merge

lab var has_college "county had college before 1900"
lab var treated "exactly one college founded between 1900 and 1940 in the county"

replace treated = 0 if missing(treated) // This will include both counties that already had a college along with counties that gain a college


* calculate the share of people that have multiple observations below 18

g below_18 = age <18

egen num_below_18 = total(below_18), by(hik)

* We can do some robustness around this but my plan was to keep the latest below 18 location assignment for each person

egen max_below18 = max(year) if below_18, by(hik)

keep if (below_18 & year == max_below18) | year==1940

* check to ensure there are two observations for each hik

g count =1
egen count_hik = total(count), by(hik)

* keep only geographic information from the earlier year to merge later

preserve
drop if year == 1940
rename year year_before_18
rename statefip statefip_pre_18
rename countyicp countyicp_pre_18
rename age age_pre_18
rename birthyr birthyr_pre_18
keep hik statefip countyicp year_before_18
tempfile before_data
save `before_data'
restore

* merge back on to the 1940 data

keep if year == 1940

merge 1:1 hik using `before_data', nogen

/*
birthyr seems to be more accurately reported in 1940 so use this as the birthyear
There is limited disagreement between birthyears across hiks but it is limited
In general, I will be assuming that the 1940 census is more accurate when adjudacating
between different versions of the same data.
*/

* define the projected year at which the individual turns 18

g year_at_18 = birthyr + 18

* define the difference between the founding year of a college and the age cohort
* here, positive values imply being treated, negative values imply not being treated

g treatment_cohort = year_at_18 - year_founding

g age_at_founding = year_founding - birthyr

* for now, I am going to drop events where there are extremely few observations

egen count_by_treatment_group = total(count), by(college_name) // Note here that college name is implicitly defining the event.
keep if count_by_treatment_group > 100
drop count_by_treatment_group


* create group by state and county

egen g_state_county_pre_18 = group(statefip_pre_18 countyicp_pre_18)
g age_squared = age^2

* ensure that there is sufficient coverage in each period

keep if inrange(age_at_founding, 11, 31)

egen count_by_group = total(count), by(college_name age_at_founding)

egen min_by_college = min(count_by_group), by(college_name)

* somehow albertus magnus college is included despite yale existing. I am going to drop them

drop if college_name == "Albertus Magnus Coll."


save cleaned_opening_regression_data, replace












