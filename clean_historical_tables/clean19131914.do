
cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education"
import delimited "data/extracted_scans/commis_1913_1914_extracted", clear
rename v1 page_number 
rename v2 header_indicator 
rename v3 key

compress

* split into odd and even pages since tables are split across two pages

keep if inrange(page_number, 1,24)
keep if mod(page_number, 2) == 1

* fill state 

* assign states to colleges. state names often have appended periods

g is_state = !missing(v4) & missing(v5)

g state = substr(v4, 1, strpos(v4, "-") - 1) if is_state & strpos(v4, "-")>0
replace state = v4 if is_state & strpos(v4, "-")==0
replace state = subinstr(state, ".","",.)
replace state = upper(state)
replace state = "NORTH CAROLINA" if state=="NORTH CARO"
replace state = "DISTRICT OF COLUMBIA" if state=="DISTRICT OF CO"
replace state = "MASSACHUSETTS" if state=="MASSACHUSETTS CONTINUED"
replace state = "OHIO" if state == "OH10"
replace state = "NORTH CAROLINA" if state == "NORTH CAROLINA "

* fill states

replace state = state[_n-1] if missing(state) 
drop if is_state

* merge with the even number pages

preserve
import delimited "data/extracted_scans/commis_1913_1914_extracted", clear
rename v1 page_number 
rename v2 header_indicator 
keep if inrange(page_number, 1,24)
keep if mod(page_number, 2) == 0
rename v21 key
destring key, replace force
g count =1 
egen counter = total(count), by(key) 
keep if counter==1
drop if missing(key)
rename v5 professors_men
rename v6 professors_women
rename v7 students_prep_men
rename v8 students_prep_women
rename v9 undergrads_arts_men
rename v10 undergrads_arts_women
rename v11 grads_men
rename v12 grads_women
rename v13 prof_men
rename v14 prof_women
rename v17 students_men
rename v18 students_women

keep key professors_men professors_women students_prep_men students_prep_women undergrads_arts_men undergrads_arts_women grads_men grads_women prof_men prof_women students_men students_women  
tempfile even
save `even'
restore

destring key, replace force

g count =1
egen counter = total(count), by(key)
keep if counter==1

merge 1:1 key using `even', nogen keep(3) // Could go in by hand to count entries


* fill town

replace v4 = "" if inlist(v4, "Do", "Do (May", "Do.", "do", ".do", "do") // Indicates continuation
replace v4 = v4[_n-1] if missing(v4)


* fill university

g lower_cat = lower(v5)
g college = lower_cat

* create a category row 

g category = "total"


* create header row

rename v4 town
rename v5 program
rename v6 for_men_women
rename v7 control
rename v8 year_first_opening


* keep a subset of the variables

keep state town college program category for_men_women year_first_opening professors_men professors_women students_prep_men students_prep_women undergrads_arts_men undergrads_arts_women grads_men grads_women prof_men prof_women students_men students_women  

order state town college program category for_men_women year_first_opening professors_men professors_women students_prep_men students_prep_women undergrads_arts_men undergrads_arts_women grads_men grads_women prof_men prof_women students_men students_women

* clean college names - remove non-conventional characters including Unicode and numbers
replace college = ustrregexra(college, "[^\x20-\x7E]", "") if !missing(college)
replace college = regexr(college, "[^a-zA-Z \-\'\.]", "") if !missing(college)
replace college = regexr(college, " +", " ") if !missing(college)
replace college = trim(college) if !missing(college)
replace college = regexr(college, "^[\.\-]+|[\.\-]+$", "") if !missing(college)


* remove dashes and spaces as well

replace college = subinstr(college, "-", "", .)
replace college = subinstr(college, "  ", " ", .)

* destring all numeric variables

loc numeric_vars year_first_opening professors_men professors_women students_prep_men students_prep_women undergrads_arts_men undergrads_arts_women grads_men grads_women prof_men prof_women students_men students_women

foreach variable of local numeric_vars {
    replace `variable' = subinstr(`variable', ",", "", .) if !missing(`variable')
    replace `variable' = subinstr(`variable', "$", "", .) if !missing(`variable')
    destring `variable', replace force
}

*check to ensure missing county are close to that of the original string variables. Additional missings are typically the result of textract errors.


compress 

export delimited "data/cleaned_scans/commis_1913_1914.csv", replace

