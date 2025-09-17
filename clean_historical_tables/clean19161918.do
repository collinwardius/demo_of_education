
cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education"
import delimited "data/extracted_scans/bi_survey1916_1918_extracted", clear
rename v1 page_number 
rename v2 header_indicator 

* generated header inicator works well for these data
keep if inrange(page, 1, 111)



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

* drop headers now that the states are filled.

drop if header_indicator==1

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


* create header row

rename v3 town
rename v4 program
rename v5 for_men_women
rename v6 control
rename v7 year_first_opening
rename v8 professors_men
rename v9 professors_women
rename v10 total_professors_men
rename v11 total_professors_women
rename v12 students_men
rename v13 students_women
rename v14 total_students_men
rename v15 total_students_women
rename v16 first_degrees_men
rename v17 first_degrees_women
rename v18 total_first_degrees_men
rename v19 total_first_degrees_women
rename v20 graduate_degrees_men
rename v21 graduate_degrees_women
rename v22 total_graduate_degrees_men
rename v23 total_graduate_degrees_women
rename v24 honorary_degrees



* keep a subset of the variables

keep state town college program category for_men_women control year_first_opening professors_men professors_women total_professors_men total_professors_women students_men students_women total_students_men total_students_women first_degrees_men first_degrees_women total_first_degrees_men total_first_degrees_women graduate_degrees_men graduate_degrees_women total_graduate_degrees_men total_graduate_degrees_women honorary_degrees is_college

order state town college program category for_men_women control year_first_opening professors_men professors_women total_professors_men total_professors_women students_men students_women total_students_men total_students_women first_degrees_men first_degrees_women total_first_degrees_men total_first_degrees_women graduate_degrees_men graduate_degrees_women total_graduate_degrees_men total_graduate_degrees_women honorary_degrees is_college

* replace so that total is consolidated for the leading college row

replace professors_men = total_professors_men if is_college
replace professors_women = total_professors_women if is_college
replace students_men = total_students_men if is_college
replace students_women = total_students_women if is_college
replace first_degrees_men = total_first_degrees_men if is_college
replace first_degrees_women = total_first_degrees_women if is_college
replace graduate_degrees_men = total_graduate_degrees_men if is_college
replace graduate_degrees_women = total_graduate_degrees_women if is_college


drop total_professors_men
drop total_professors_women
drop total_students_men
drop total_students_women
drop total_first_degrees_men
drop total_first_degrees_women
drop total_graduate_degrees_men
drop total_graduate_degrees_women

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

*check to ensure missing county are close to that of the original string variables. Additional missings are typically the result of textract errors.

drop is_college
destring year_first_opening, replace 
destring professors_men, replace force 
destring professors_women, replace force
destring students_men, replace force
destring students_women, replace force
destring first_degrees_men, replace force
destring first_degrees_women, replace force
destring graduate_degrees_men, replace force
destring graduate_degrees_women, replace force
destring honorary_degrees, replace force

compress 

export delimited "data/cleaned_scans/bi_survey1916_1918.csv", replace

