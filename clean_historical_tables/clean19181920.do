/*
I use this file as the template file for the data cleaning
*/


cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education"
import delimited "data/extracted_scans/bi_survey1918_1920_extracted", clear
rename (v1 v2) (page header_indicator)
keep if inrange(page, 1, 75)

bys page: drop if _n<=3 // drops the header of each page I think this could present problems if there is no header at the top of a page. For this instance it works as all pages have headers.

* assign states to colleges. state names typically have associated periods.

g is_state = !missing(v3) & missing(v4)

g state = substr(v3, 1, strpos(v3, "-") - 1) if is_state & strpos(v3, "-")>0
replace state = v3 if is_state & strpos(v3, "-")==0
replace state = subinstr(state, ".","",.)
replace state = upper(state)
replace state = "NORTH CAROLINA" if state=="NORTH CARO"
replace state = "DISTRICT OF COLUMBIA" if state=="DISTRICT OF CO"
replace state = "MASSACHUSETTS" if state=="MASSACHUSETTS CONTINUED"

* fill states

replace state = state[_n-1] if missing(state) 
drop if is_state

* fill town

replace v3 = "" if inlist(v3, "Do", "Do (May", "Do.")
replace v3 = v3[_n-1] if missing(v3)


* fill university

g lower_cat = lower(v4)
g is_college = strpos(lower_cat, "col") > 0 ///
    | strpos(lower_cat, "inst") > 0 ///
    | strpos(lower_cat, "uni") > 0

g college = lower_cat if is_college
replace college = college[_n-1] if missing(college)

* drop anything in parentheses

replace college = substr(college,1,strpos(college, "(")-1) if strpos(college, "(")>0

* create a category row 

g category = "total" if is_college
replace category = "major" if is_college ==0

drop if missing(v8) & missing(v9) // would indicate no students. These should be limited as this is evidence of a textract error.


* create header row

rename v4 program
rename v5 year_first_opening
rename v6 professors_men
rename v7 professors_women
rename v8 students_men
rename v9 students_women
rename v10 first_degrees_men
rename v11 first_degrees_women
rename v12 graduate_degrees_men
rename v13 graduate_degrees_women
rename v14 honorary_degrees
rename v3 town



* keep a subset of the variables

keep state town college program category year_first_opening professors_men professors_women students_men students_women first_degrees_men first_degrees_women graduate_degrees_men graduate_degrees_women honorary_degrees

order state town college program category year_first_opening professors_men professors_women students_men students_women first_degrees_men first_degrees_women graduate_degrees_men graduate_degrees_women honorary_degrees

* clean college names - remove non-conventional characters including Unicode and numbers
replace college = ustrregexra(college, "[^\x20-\x7E]", "") if !missing(college)
replace college = regexr(college, "[^a-zA-Z \-\'\.]", "") if !missing(college)
replace college = regexr(college, " +", " ") if !missing(college)
replace college = trim(college) if !missing(college)
replace college = regexr(college, "^[\.\-]+|[\.\-]+$", "") if !missing(college)

* destring all numeric variables

loc numeric_vars year_first_opening professors_men professors_women students_men students_women first_degrees_men first_degrees_women graduate_degrees_men graduate_degrees_women honorary_degrees

foreach variable of local numeric_vars {
    replace `variable' = subinstr(`variable', ",", "", .) if !missing(`variable')
    replace `variable' = subinstr(`variable', "$", "", .) if !missing(`variable')
}

destring year_first_opening, replace 
destring professors_men, replace force // check to ensure missing county are close to that of the original string variables. Additional missings are typically the result of textract errors.
destring professors_women, replace force
destring students_men, replace force
destring students_women, replace force
destring first_degrees_men, replace force
destring first_degrees_women, replace force
destring graduate_degrees_men, replace force
destring graduate_degrees_women, replace force
destring honorary_degrees, replace force

compress
export delimited "data/cleaned_scans/bi_survey1918_1920.csv", replace

