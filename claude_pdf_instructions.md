Instructions for claude on how to read in pdf files from
historical reports on education. Here I provide some details on the t


Notes on missing values in tables
1. DO NOT HALLUCINATE VALUES UNDER ANY CIRCUMSTANCE. IF A VALUE IS MISSING WITHIN A TABLE, LEAVE THAT ENTRY BLANK.
2. Sometimes, missing values display as a series of dashes "---" or a series of dots "..." these types of entries should be left blank.
3. EQUALLY IMPORTANTLY, IF A FIELD IS NOT BLANK, MAKE SURE TO ALWAYS FILL IN THAT FIELD.

Notes on the structure of the tables
1. The first column of the report is always the name of a US state.
2. At the very top of the table is the title of the table. Always report the title of the table as the last field in the output document.
3. There should never be an entry that is fully missing all fields. For the typical table, the vast majority of the fields are populated.

Notes on characters used in the table
1. All entries within the table other than state names are numeric.
2. Commas "," sometimes are used. Please ignore these commas and read in the numebrs themselves. 
3. There are NEVER "." used in the table.


Notes on headers
1. The headers of this documents are very complex. Sometimes, there are nested headers. For example, the topmost header is "Resident College Enrollments". This header is subdivided into "Regular session enrollments" and "Summer session enrollments" which is then subdivided into "Men" and "Women" For these sorts of complex headers, please combine them into one succinct header. For example, "enrollment_regular_male". If at any point you are unsure about how to format a header, flag this to me.


