
cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education"
import delimited "data/extracted_scans/bi_survey1930_1932_extracted", clear
rename v1 page_number 
rename v2 header_indicator 

compress

* generated header inicator works well for these data
keep if inrange(page_number, 1,34)

* drop header rows

drop if header_indicator==1

* assign states to colleges. state names often have appended periods

g is_state = !missing(v3) & missing(v4) & missing(v5) & missing(v6) & missing(v7)

g state = substr(v3, 1, strpos(v3, "-") - 1) if is_state & strpos(v3, "-")>0
replace state = v3 if is_state & strpos(v3, "-")==0
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

* remove town from the university name. They always come after a ,

replace v3 = substr(v3, 1, strpos(v3,",") - 1) if strpos(v3 , ",") > 0


* fill university

g lower_cat = lower(v3)
g college = lower_cat

* drop anything in parentheses typically some indications of control

replace college = substr(college,1,strpos(college, "(")-1) if strpos(college, "(")>0

* create a category row 

g category = "total"


* create header row

rename v3 program
rename v4 professors_men
rename v5 professors_women
rename v6 students_men
rename v7 students_women
rename v12 undergrads_arts_men
rename v13 undergrads_arts_women
rename v14 grads_arts_men
rename v15 grads_arts_women
rename v16 undergrads_prof_men
rename v17 undergrads_prof_women
rename v18 grads_prof_men
rename v19 grads_prof_women
rename v20 first_degrees_men
rename v21 first_degrees_women
rename v22 masters_total
rename v23 doctorate_total
rename v24 honorary_degrees

* keep a subset of the variables

keep state college program category professors_men professors_women students_men students_women undergrads_arts_men undergrads_arts_women grads_arts_men grads_arts_women undergrads_prof_men undergrads_prof_women grads_prof_men grads_prof_women first_degrees_men first_degrees_women masters_total doctorate_total honorary_degrees

order state college program category professors_men professors_women students_men students_women undergrads_arts_men undergrads_arts_women grads_arts_men grads_arts_women undergrads_prof_men undergrads_prof_women grads_prof_men grads_prof_women first_degrees_men first_degrees_women masters_total doctorate_total honorary_degrees

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

loc numeric_vars professors_men professors_women students_men students_women undergrads_arts_men undergrads_arts_women grads_arts_men grads_arts_women undergrads_prof_men undergrads_prof_women grads_prof_men grads_prof_women first_degrees_men first_degrees_women masters_total doctorate_total honorary_degrees

foreach variable of local numeric_vars {
    replace `variable' = subinstr(`variable', ",", "", .) if !missing(`variable')
    replace `variable' = subinstr(`variable', "$", "", .) if !missing(`variable')
}

*check to ensure missing county are close to that of the original string variables. Additional missings are typically the result of textract errors.

foreach variable of local numeric_vars {
    di "`variable'"
    destring `variable', replace force 
}


compress 

export delimited "data/cleaned_scans/bi_survey1930_1932.csv", replace

