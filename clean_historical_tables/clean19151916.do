
cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education"
import delimited "data/extracted_scans/commis_1915_1916_extracted", clear
rename v1 page_number 
rename v2 header_indicator 

compress

* generated header inicator works well for these data
keep if inrange(page_number, 1,20)


* assign states to colleges. state names often have appended periods

g is_state = !missing(v3) & missing(v4) & missing(v5) & missing(v6) & missing(v7)

g state = substr(v3, 1, strpos(v3, "-") - 1) if is_state & strpos(v3, "-")>0
replace state = "COLORADO" if state=="1916"
replace state = v3 if is_state & strpos(v3, "-")==0
replace state = subinstr(state, ".","",.)
replace state = upper(state)
replace state = "NORTH CAROLINA" if state=="NORTH CARO"
replace state = "SOUTH CAROLINA" if state=="SOUTH CARO"
replace state = "DISTRICT OF COLUMBIA" if state=="DISTRICT OF CO"
replace state = "MASSACHUSETTS" if state=="MASSACHUSETTS CONTINUED"
replace state = "OHIO" if state == "OH10"
replace state = "NORTH CAROLINA" if state == "NORTH CAROLINA "

* fill states

replace state = state[_n-1] if missing(state) 
drop if is_state

* drop header rows

drop if header_indicator==1


* fill town

replace v3 = "" if inlist(v3, "Do", "Do (May", "Do.") // Indicates continuation
replace v3 = v3[_n-1] if missing(v3)


* fill university

g lower_cat = lower(v4)
g college = lower_cat


* drop anything in parentheses typically some indications of control

replace college = substr(college,1,strpos(college, "(")-1) if strpos(college, "(")>0

* create a category row 

g category = "total"


* create header row

rename v3 town
rename v4 program
rename v5 for_men_women
rename v6 control
rename v7 year_first_opening
rename v14 professors_men
rename v15 professors_women 
rename v16 students_prep_men
rename v17 students_prep_women
rename v18 undergrads_arts_men
rename v19 undergrads_arts_women
rename v20 grads_men
rename v21 grads_women
rename v22 professional_men
rename v23 professional_women
rename v26 students_men
rename v27 students_women


* keep a subset of the variables

keep state college town program category for_men_women control year_first_opening  professors_men professors_women students_prep_men students_prep_women undergrads_arts_men undergrads_arts_women grads_men grads_women professional_men professional_women students_men students_women

order state college town program category for_men_women control year_first_opening  professors_men professors_women students_prep_men students_prep_women undergrads_arts_men undergrads_arts_women grads_men grads_women professional_men professional_women students_men students_women

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

loc numeric_vars year_first_opening  professors_men professors_women students_prep_men students_prep_women undergrads_arts_men undergrads_arts_women grads_men grads_women professional_men professional_women students_men students_women


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

tempfile clean19151916
save `clean19151916', replace


* append on the data on major 

import delimited "data/extracted_scans/commis_1915_1916_extracted", clear

rename v1 page_number 
rename v2 header_indicator 
keep if inrange(page_number, 21,36)
drop v26 v27

replace v3 = lower(v3)
g is_college = strpos(v3, "coll") > 0 ///
    | strpos(v3, "inst") > 0 ///
    | strpos(v3, "uni") > 0 ///
    | strpos(v3, "polytechnical") > 0


drop if is_college==1 &  missing(v4) & missing(v5) & missing(v6) & missing(v7) & missing(v8) & missing(v9) & missing(v10) & missing(v11) & missing(v12) & missing(v13) & missing(v14) & missing(v15) & missing(v16) & missing(v17) & missing(v18) & missing(v19) & missing(v20) & missing(v21) & missing(v22) & missing(v23) & missing(v24) & missing(v25)

g is_state = !missing(v3) & missing(v4) & missing(v5) & missing(v6) & missing(v7) & missing(v8) & missing(v9) & missing(v10) & missing(v11) & missing(v12) & missing(v13) & missing(v14) & missing(v15) & missing(v16) & missing(v17) & missing(v18) & missing(v19) & missing(v20) & missing(v21) & missing(v22) & missing(v23) & missing(v24) & missing(v25)

g state = v3 if is_state
replace state = state[_n-1] if missing(state)
replace state = upper(state)

drop if header_indicator==1

* Step 1: Clean up the state names
replace state = upper(trim(state))

* Step 2: Fix specific formatting issues
replace state = "OHIO" if regexm(state, "O HIO")
replace state = "OHIO" if state == "OHTO"

* Step 4: Remove any entries that end with colons and clean
replace state = regexr(state, ":$", "")
replace state = "OHIO" if state == "OHTO"

replace state = substr(state, 1, strpos(state, "-") - 1) if strpos(state, "-")>0

rename v3 college
rename v4 studentsarts_sciences
rename v5 studentsagriculture
rename v6 studentsforestry
rename v7 studentsgeneral_engineering
rename v8 studentschemical_engineering
rename v9 studentscivil_engineering
rename v10 studentselectrical_engineering
rename v11 studentsmechanical_engineering
rename v12 studentsmining_engineering
rename v13 studentsarchitecture
rename v14 studentscommerce
rename v15 studentseducation
rename v16 studentsfine_arts
rename v17 studentshousehold_economics
rename v18 studentsjournalism
rename v19 studentsmusic
rename v20 studentstheology
rename v21 studentslaw
rename v22 studentsmedicine
rename v23 studentsveterinary_medicine
rename v24 studentsdentistry
rename v25 studentspharmacy


reshape long students, i(college state) j(program) string
g category = "major"

replace program = subinstr(program, "_", " ", .)

* clean college names - remove non-conventional characters including Unicode and numbers
replace college = ustrregexra(college, "[^\x20-\x7E]", "") if !missing(college)
replace college = regexr(college, "[^a-zA-Z \-\'\.]", "") if !missing(college)
replace college = regexr(college, " +", " ") if !missing(college)
replace college = trim(college) if !missing(college)
replace college = regexr(college, "^[\.\-]+|[\.\-]+$", "") if !missing(college)


* remove dashes and spaces as well

replace college = subinstr(college, "-", "", .)
replace college = subinstr(college, "  ", " ", .)

keep state college program category students

append using `clean19151916'

gsort state college -category program

export delimited "data/cleaned_scans/commis_1915_1916.csv", replace
