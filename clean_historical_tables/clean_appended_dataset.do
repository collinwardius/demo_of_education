* clean appended dataset
cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education"
import delimited "data/cleaned_scans/college_surveys_appended.csv", clear

* clean any inconsistent strings

replace state = "DISTRICT OF COLUMBIA" if state == "DIST COLUMBIA"
replace state = "NEW HAMPSHIRE" if state == "NEW HAMP"
replace state = "PENNSYLVANIA"  if state == "PENNSYLVANIA CONTD"
replace state = "SOUTH CAROLINA" if state == "SOUTH CARO"
replace state = "OHIO" if state == "OMO"

drop if inlist(state,"PUERTO RICO", "PORTO RICO", "LOCATION")

* create a year variable

g year = substr(source_dataset,-4,.)
destring year, replace

* merge in the college crosswalk

preserve
import delimited "data/college_data/temp_college_crosswalk.csv", clear varn(1)
rename original_college college
tempfile crosswalk
save `crosswalk'
restore

merge m:1 state college using `crosswalk'
drop if _merge ==1
drop _merge college


rename assigned_college_name college


export delimited "data/college_data/cleaned_appended_college_data", replace