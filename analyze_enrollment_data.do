* preliminary analysis of trends in enrollment

cd "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education"
import delimited "data/college_data/cleaned_appended_college_data", clear

preserve
keep if category == "total"

replace students_men = 0 if missing(students_men)
replace students_women = 0 if missing(students_women)
g enrollment = students_men + students_women


collapse (sum) enrollment, by(year)

* Create line graph of enrollment with dots for individual years

twoway (line enrollment year) ///
	, title("Enrollment Trends Over Time") ///
	xlabel(, angle(45)) ///
	ylabel(, format(%9.0gc)) ///
	legend(off) ///
	xtitle("Year") ///
	ytitle("Enrollment")

restore

