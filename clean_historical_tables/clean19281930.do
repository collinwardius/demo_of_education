
cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education"
import delimited "data/extracted_scans/bi_survey1928_1930_extracted", clear
rename v1 page_number 
rename v2 header_indicator 

compress 

* generated header inicator works well for these data
keep if inrange(page_number, 1,34) | inrange(page_number, 45,99)

* combine rows where the town is split from the university name

* fill university

g lower_cat = lower(v3)
g is_college = strpos(lower_cat, "coll") > 0 ///
    | strpos(lower_cat, "inst") > 0 ///
    | strpos(lower_cat, "uni") > 0 ///
    | strpos(lower_cat, "polytechnic") > 0

g flag_dangler= (is_college & missing(v7) & missing(v8))
g new_name = lower_cat[_n-1] + " " + lower_cat if flag_dangler[_n-1]

replace lower_cat= new_name if !missing(new_name)
drop if flag_dangler

replace lower_cat = substr(lower_cat, 1, strpos(v3,",") - 1) if strpos(v3, ",") > 0
replace lower_cat = substr(lower_cat, 1, strpos(v3,".") - 1) if strpos(v3, ".") > 0
replace lower_cat = substr(lower_cat, 1, strpos(v3,"-") - 1) if strpos(v3, "-") > 0



* assign states to colleges. state names often have appended periods

drop if header_indicator
g is_state = !missing(v3) & missing(v7) & missing(v8)

* there are a few straggler cases unique to this year

drop if v3 == "Journalism" & is_state
drop if v3 == "Education" & is_state
drop if v3 == "Special" & is_state


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


*infill colleges

drop is_college
g is_college = strpos(lower_cat, "coll") > 0 ///
    | strpos(lower_cat, "inst") > 0 ///
    | strpos(lower_cat, "uni") > 0 ///
    | strpos(lower_cat, "polytechnic") > 0
g college = lower_cat if is_college
replace college = college[_n-1] if missing(college)

* drop anything in parentheses typically some indications of control

replace college = substr(college,1,strpos(college, "(")-1) if strpos(college, "(")>0

* create a category row 

g category = "total" if is_college
replace category = "major" if is_college ==0


* create header row

rename v3 program
rename v4 year_first_opening
rename v5 professors_men
rename v6 professors_women
rename v7 students_men
rename v8 students_women
rename v9 first_degrees_men
rename v10 first_degrees_women
rename v11 graduate_degrees_men
rename v12 graduate_degrees_women
rename v13 honorary_degrees

* keep a subset of the variables

keep state college program category year_first_opening professors_men professors_women students_men students_women first_degrees_men first_degrees_women graduate_degrees_men graduate_degrees_women honorary_degrees

order state college program category year_first_opening professors_men professors_women students_men students_women first_degrees_men first_degrees_women graduate_degrees_men graduate_degrees_women honorary_degrees

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

loc numeric_vars year_first_opening professors_men professors_women students_men students_women first_degrees_men first_degrees_women graduate_degrees_men graduate_degrees_women honorary_degrees

foreach variable of local numeric_vars {
    replace `variable' = subinstr(`variable', ",", "", .) if !missing(`variable')
    replace `variable' = subinstr(`variable', "$", "", .) if !missing(`variable')
}

*check to ensure missing county are close to that of the original string variables. Additional missings are typically the result of textract errors.

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

export delimited "data/cleaned_scans/bi_survey1928_1930.csv", replace

