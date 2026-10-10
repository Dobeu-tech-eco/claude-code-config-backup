# MV-104 (5/25) fillable field map — form reading order

Generated from assets/mv104-template.pdf (158 fields). `field` is the exact PDF field name to pass to scripts/fill_mv104.py. Choice fields accept ONLY the listed options (codes keep their trailing period, e.g. "1."). Checkboxes accept the listed state(s); the code meanings are in references/mv104-page2-instructions.txt and mv104-page1-text.txt.

| # | Pg | Field (exact name) | Type | Allowed values |
|---|---|---|---|---|
| 1 | 1 | `Time AMPM` | checkbox | AM, PM |
| 2 | 1 | `Police Agency/Precinct/Crash Number` | text | free text |
| 3 | 1 | `Day of Week` | choice | Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday |
| 4 | 1 | `Crash Time` | text | free text |
| 5 | 1 | `Number of Vehicles/Units` | text | free text |
| 6 | 1 | `Number of Injured` | text | free text |
| 7 | 1 | `Number of Fatalities` | text | free text |
| 8 | 1 | `Crash Date Month` | choice | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12 |
| 9 | 1 | `Crash Date Day` | choice | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31 |
| 10 | 1 | `Crash Date Year` | text | free text |
| 11 | 1 | `Police Responded` | checkbox | Yes |
| 12 | 1 | `Police Filed Crash Report` | checkbox | Yes |
| 13 | 1 | `OTHER DRIVER` | checkbox | free text |
| 14 | 1 | `PEDESTRIAN` | checkbox | Yes |
| 15 | 1 | `BICYCLIST` | checkbox | Yes |
| 16 | 1 | `E-BIKE/E-SCOOTER` | checkbox | Yes |
| 17 | 1 | `(PART A: Your Vehicle/Unit) Driver State of License` | choice | NY, AL, AK, AZ, AR, CA, CO, CT, DE, DC, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NC, ND, OH, OK, OR, PA, RI,  |
| 18 | 1 | `(PART B: Other Vehicle/Unit) Driver State of License` | choice | NY, AL, AK, AZ, AR, CA, CO, CT, DE, DC, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NC, ND, OH, OK, OR, PA, RI,  |
| 19 | 1 | `(PART A: Your Vehicle/Unit) Driver License ID Identification Number` | text | free text |
| 20 | 1 | `(PART B: Other Vehicle/Unit) Driver License ID Identification Number` | text | free text |
| 21 | 1 | `(PART A: Your Vehicle/Unit) Driver Name - exactly as printed on license (Last, First, M.I. (middle initial))` | text | free text |
| 22 | 1 | `(PART B: Other Vehicle/Unit) Driver Name - exactly as printed on license (Last, First, M.I. (middle initial))` | text | free text |
| 23 | 1 | `(PART A: Your Vehicle/Unit) Driver Address (include house number, street and apartment number)` | text | free text |
| 24 | 1 | `(PART B: Other Vehicle/Unit) Driver Address (include house number, street and apartment number)` | text | free text |
| 25 | 1 | `3. TRAFFIC CONTROL` | choice | 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 15., 16., 17., 18., 19., 20., 21., 22., 23., -, X |
| 26 | 1 | `(PART A: Your Vehicle/Unit) Driver City or Town` | text | free text |
| 27 | 1 | `(PART A: Your Vehicle/Unit) Driver State` | choice | NY, AL, AK, AZ, AR, CA, CO, CT, DE, DC, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NC, ND, OH, OK, OR, PA, RI,  |
| 28 | 1 | `(PART A: Your Vehicle/Unit) Driver Zip Code` | text | free text |
| 29 | 1 | `(PART B: Other Vehicle/Unit) Driver City or Town` | text | free text |
| 30 | 1 | `(PART B: Other Vehicle/Unit) Driver State` | choice | NY, AL, AK, AZ, AR, CA, CO, CT, DE, DC, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NC, ND, OH, OK, OR, PA, RI,  |
| 31 | 1 | `(PART B: Other Vehicle/Unit) Driver Zip Code` | text | free text |
| 32 | 1 | `(PART A: Your Vehicle/Unit) Driver Sex` | text | free text |
| 33 | 1 | `(PART A: Your Vehicle/Unit) Number of People in Vehicle/Unit` | text | free text |
| 34 | 1 | `(PART B: Other Vehicle/Unit) Driver Sex` | text | free text |
| 35 | 1 | `(PART B: Other Vehicle/Unit) Number of People in Vehicle/Unit` | text | free text |
| 36 | 1 | `(PART A: Your Vehicle/Unit) Driver Date of Birth Month` | choice | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12 |
| 37 | 1 | `(PART A: Your Vehicle/Unit) Driver Date of Birth Day` | choice | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31 |
| 38 | 1 | `(PART A: Your Vehicle/Unit) Driver Date of Birth Year` | text | free text |
| 39 | 1 | `(PART B: Other Vehicle/Unit) Driver Date of Birth Month` | choice | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12 |
| 40 | 1 | `(PART B: Other Vehicle/Unit) Driver Date of Birth Day` | choice | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31 |
| 41 | 1 | `(PART B: Other Vehicle/Unit) Driver Date of Birth Year` | text | free text |
| 42 | 1 | `(PART A: Your Vehicle/Unit) Registrant Name - exactly as printed on registration` | text | free text |
| 43 | 1 | `(PART B: Other Vehicle/Unit) Registrant Name - exactly as printed on registration` | text | free text |
| 44 | 1 | `(PART A: Your Vehicle/Unit) Registrant Date of Birth Month` | choice | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12 |
| 45 | 1 | `(PART A: Your Vehicle/Unit) Registrant Date of Birth Day` | choice | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31 |
| 46 | 1 | `(PART A: Your Vehicle/Unit) Registrant Date of Birth Year` | text | free text |
| 47 | 1 | `(PART B: Other Vehicle/Unit) Registrant Date of Birth Month` | choice | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12 |
| 48 | 1 | `(PART B: Other Vehicle/Unit) Registrant Date of Birth Day` | choice | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31 |
| 49 | 1 | `(PART B: Other Vehicle/Unit) Registrant Date of Birth Year` | text | free text |
| 50 | 1 | `(PART A: Your Vehicle/Unit) Registrant Address (include house number, street and apartment number)` | text | free text |
| 51 | 1 | `(PART A: Your Vehicle/Unit) Registrant Sex` | text | free text |
| 52 | 1 | `(PART B: Other Vehicle/Unit) Registrant Address (include house number, street and apartment number)` | text | free text |
| 53 | 1 | `(PART B: Other Vehicle/Unit) Registrant Sex` | text | free text |
| 54 | 1 | `(PART A: Your Vehicle/Unit) Registrant City or Town` | text | free text |
| 55 | 1 | `(PART A: Your Vehicle/Unit) Registrant State` | choice | NY, AL, AK, AZ, AR, CA, CO, CT, DE, DC, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NC, ND, OH, OK, OR, PA, RI,  |
| 56 | 1 | `(PART A: Your Vehicle/Unit) Registrant Zip Code` | text | free text |
| 57 | 1 | `(PART B: Other Vehicle/Unit) Registrant City or Town` | text | free text |
| 58 | 1 | `(PART B: Other Vehicle/Unit) Registrant State` | choice | NY, AL, AK, AZ, AR, CA, CO, CT, DE, DC, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NC, ND, OH, OK, OR, PA, RI,  |
| 59 | 1 | `(PART B: Other Vehicle/Unit) Registrant Zip Code` | text | free text |
| 60 | 1 | `6. ROADWAY SURFACE CONDITION` | choice | 1., 2., 3., 4., 5., 6., 7., 0., -, X |
| 61 | 1 | `(PART A: Your Vehicle/Unit) Registrant Plate Number` | text | free text |
| 62 | 1 | `(PART A: Your Vehicle/Unit) Registrant State of Registration` | choice | NY, AL, AK, AZ, AR, CA, CO, CT, DE, DC, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NC, ND, OH, OK, OR, PA, RI,  |
| 63 | 1 | `(PART A: Your Vehicle/Unit) Registrant Vehicle/Unit Year/Make/Model` | text | free text |
| 64 | 1 | `(PART A: Your Vehicle/Unit) Registrant Vehicle/Unit Type` | text | free text |
| 65 | 1 | `(PART B: Other Vehicle/Unit) Registrant Plate Number` | text | free text |
| 66 | 1 | `(PART B: Other Vehicle/Unit) Registrant State of Registration` | choice | NY, AL, AK, AZ, AR, CA, CO, CT, DE, DC, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NC, ND, OH, OK, OR, PA, RI,  |
| 67 | 1 | `(PART B: Other Vehicle/Unit) Registrant Vehicle/Unit Year/Make/Model` | text | free text |
| 68 | 1 | `(PART B: Other Vehicle/Unit) Registrant Vehicle/Unit Type` | text | free text |
| 69 | 1 | `(PART A: Your Vehicle/Unit) Registrant Vehicle Identification Number` | text | free text |
| 70 | 1 | `(PART A: Your Vehicle/Unit) Registrant Insurance Code` | text | free text |
| 71 | 1 | `(PART B: Other Vehicle/Unit) Registrant Vehicle Identification Number` | text | free text |
| 72 | 1 | `(PART B: Other Vehicle/Unit) Registrant Insurance Code` | text | free text |
| 73 | 1 | `23. DIRECTION OF TRAVEL (Unit 1)` | choice | 1., 2., 3., 4., 5., 6., 7., 8., -, X |
| 74 | 1 | `(PART A: Your Vehicle/Unit) Registrant Insurance Company/Self Insured Name` | text | free text |
| 75 | 1 | `(PART A: Your Vehicle/Unit) Registrant Insurance Policy/Certificate Number` | text | free text |
| 76 | 1 | `(PART B: Other Vehicle/Unit) Registrant Insurance Company/Self Insured Name` | text | free text |
| 77 | 1 | `(PART B: Other Vehicle/Unit) Registrant Insurance Policy/Certificate Number` | text | free text |
| 78 | 1 | `24. DIRECTION OF TRAVEL (Unit 2)` | choice | 1., 2., 3., 4., 5., 6., 7., 8., -, X |
| 79 | 1 | `Crash Diagram Code` | text | free text |
| 80 | 1 | `Cost of repairs to any one unit or property will be more than $1,000` | checkbox | free text |
| 81 | 1 | `25. PRE-CRASH VEHICLE/UNIT ACTION (Unit 1)` | choice | 1., 2., 3., 4., 5., 6., 7., 8., 10., 11., 12., 13., 14., 15., 19., 20., 21., 22., 23., 24., -, X |
| 82 | 1 | `Briefly describe how the crash happened` | text | free text |
| 83 | 1 | `26. PRE-CRASH VEHICLE/UNIT ACTION (Unit 2)` | choice | 1., 2., 3., 4., 5., 6., 7., 8., 10., 11., 12., 13., 14., 15., 19., 20., 21., 22., 23., 24., -, X |
| 84 | 1 | `Name of City, Town, or Village` | text | free text |
| 85 | 1 | `County` | text | free text |
| 86 | 1 | `Crash Location` | checkbox | Village of:, Town, City |
| 87 | 1 | `Road Where Crash Occurred (route number, road, street name or address)` | text | free text |
| 88 | 1 | `House Number` | text | free text |
| 89 | 1 | `Permanent Landmark` | text | free text |
| 90 | 1 | `28. TYPE OF CRASH` | choice | 1., 2., 3., 4., 5., 7., 10., 11., 12., 13., 14., 15., 16., 17., 18., 19., 20., 22., 23., 24., 25., 27., 30., 31., 32., 33., 34., 36., 37., 38., 40., 41., 42., 4 |
| 91 | 1 | `At Intersection With: (Route Number, Road, Street Name or Exit Number)` | text | free text |
| 92 | 1 | `Crash intersection or nearest location` | checkbox | At Intersection With:, Within distance of: |
| 93 | 1 | `Crash Occurred at an Intersection` | checkbox | Yes |
| 94 | 1 | `N (North)` | checkbox | Yes |
| 95 | 1 | `S (South)` | checkbox | free text |
| 96 | 1 | `Feet` | text | free text |
| 97 | 1 | `Miles` | text | free text |
| 98 | 1 | `of (Route Number, Road, Street Name, Exit Number or Milepost)` | text | free text |
| 99 | 1 | `29. TYPE OF CRASH (Unit 1)` | choice | 1., 2., 3., 4., 5., 7., 10., 11., 12., 13., 14., 15., 16., 17., 18., 19., 20., 22., 23., 24., 25., 27., 30., 31., 32., 33., 34., 36., 37., 38., 40., 41., 42., 4 |
| 100 | 1 | `Parking Lot` | checkbox | free text |
| 101 | 1 | `E (East)` | checkbox | Yes |
| 102 | 1 | `W (West)` | checkbox | free text |
| 103 | 1 | `8. Which Unit Occupied (Row 1)` | choice | 1., 2. |
| 104 | 1 | `10. Safety Equipment Used (Row 1)` | choice | 1., 2., 3., 4., 6., 17., 18., 19., 20., 21., 22., 23., 24., 25., 26., 0., C., X., (-). |
| 105 | 1 | `12. Age (Row 1)` | text | free text |
| 106 | 1 | `13. Sex (Row 1)` | text | free text |
| 107 | 1 | `15. Injury (Row 1)` | choice | A., B., C. |
| 108 | 1 | `Describe Most Serious Injuries (Row 1)` | text | free text |
| 109 | 1 | `Date of Death (If Applicable)(Row 1)` | text | free text |
| 110 | 1 | `Name of Drivers, Passengers, Pedestrians and Bicyclists (Row 1)` | text | free text |
| 111 | 1 | `9 . Position in/on Unit (Row 1)` | choice | 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12. |
| 112 | 1 | `8. Which Unit Occupied (Row 2)` | choice | 1., 2. |
| 113 | 1 | `10. Safety Equipment Used (Row 2)` | choice | 1., 2., 3., 4., 6., 17., 18., 19., 20., 21., 22., 23., 24., 25., 26., 0., C., X., (-). |
| 114 | 1 | `12. Age (Row 2)` | text | free text |
| 115 | 1 | `13. Sex (Row 2)` | text | free text |
| 116 | 1 | `15. Injury (Row 2)` | choice | A., B., C. |
| 117 | 1 | `Date of Death (If Applicable)(Row 2)` | text | free text |
| 118 | 1 | `30. TYPE OF CRASH (Unit 2)` | choice | 1., 2., 3., 4., 5., 7., 10., 11., 12., 13., 14., 15., 16., 17., 18., 19., 20., 22., 23., 24., 25., 27., 30., 31., 32., 33., 34., 36., 37., 38., 40., 41., 42., 4 |
| 119 | 1 | `Name of Drivers, Passengers, Pedestrians and Bicyclists (Row 2)` | text | free text |
| 120 | 1 | `9 . Position in/on Unit (Row 2)` | choice | 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12. |
| 121 | 1 | `Describe Most Serious Injuries (Row 2)` | text | free text |
| 122 | 1 | `8. Which Unit Occupied (Row 3)` | choice | 1., 2. |
| 123 | 1 | `10. Safety Equipment Used (Row 3)` | choice | 1., 2., 3., 4., 6., 17., 18., 19., 20., 21., 22., 23., 24., 25., 26., 0., C., X., (-). |
| 124 | 1 | `12. Age (Row 3)` | text | free text |
| 125 | 1 | `13. Sex (Row 3)` | text | free text |
| 126 | 1 | `15. Injury (Row 3)` | choice | A., B., C. |
| 127 | 1 | `Date of Death (If Applicable)(Row 3)` | text | free text |
| 128 | 1 | `Name of Drivers, Passengers, Pedestrians and Bicyclists (Row 3)` | text | free text |
| 129 | 1 | `9 . Position in/on Unit (Row 3)` | choice | 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12. |
| 130 | 1 | `Describe Most Serious Injuries (Row 3)` | text | free text |
| 131 | 1 | `8. Which Unit Occupied (Row 4)` | choice | 1., 2. |
| 132 | 1 | `9 . Position in/on Unit (Row 4)` | choice | 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12. |
| 133 | 1 | `10. Safety Equipment Used (Row 4)` | choice | 1., 2., 3., 4., 6., 17., 18., 19., 20., 21., 22., 23., 24., 25., 26., 0., C., X., (-). |
| 134 | 1 | `12. Age (Row 4)` | text | free text |
| 135 | 1 | `13. Sex (Row 4)` | text | free text |
| 136 | 1 | `15. Injury (Row 4)` | choice | A., B., C. |
| 137 | 1 | `Describe Most Serious Injuries (Row 4)` | text | free text |
| 138 | 1 | `Date of Death (If Applicable)(Row 4)` | text | free text |
| 139 | 1 | `Name of Drivers, Passengers, Pedestrians and Bicyclists (Row 4)` | text | free text |
| 140 | 1 | `Name of Drivers, Passengers, Pedestrians and Bicyclists (Row 5)` | text | free text |
| 141 | 1 | `8. Which Unit Occupied (Row 5)` | choice | 1., 2. |
| 142 | 1 | `9 . Position in/on Unit (Row 5)` | choice | 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12. |
| 143 | 1 | `10. Safety Equipment Used (Row 5)` | choice | 1., 2., 3., 4., 6., 17., 18., 19., 20., 21., 22., 23., 24., 25., 26., 0., C., X., (-). |
| 144 | 1 | `15. Injury (Row 5)` | choice | A., B., C. |
| 145 | 1 | `Date of Death (If Applicable)(Row 5)` | text | free text |
| 146 | 1 | `12. Age (Row 5)` | text | free text |
| 147 | 1 | `13. Sex (Row 5)` | text | free text |
| 148 | 1 | `Describe Most Serious Injuries (Row 5)` | text | free text |
| 149 | 1 | `Date` | text | free text |
| 150 | 1 | `Print Name of Driver or Representative A representative may sign for the driver if the driver is unable to sign because of injury or death If you are signing as the drivers representative check the box next to I am signing on behalf of enter the vehicle unit number and check the box that describes why the driver cannot sign` | text | free text |
| 151 | 1 | `I am signing on behalf of Vehicle/Unit (specify)` | text | free text |
| 152 | 1 | `I am signing on behalf of Vehicle/Unit` | checkbox | Yes |
| 153 | 1 | `Why the driver cannot sign` | checkbox | Injury, Death |
| 154 | 1 | `Check this box if you are a firefighter and this crash occurred while responding to a call in emergency operation as defined by Vehicle and Traffic Law 114-b` | checkbox | Yes |
| 155 | 2 | `Was your vehicle vandalized?` | checkbox | No, Yes |
| 156 | 2 | `Did this crash occur in New York State?` | checkbox | Yes, No |
| 157 | 2 | `Was anyone killed or injured in this crash or was the estimated damage to any one vehicle or property greater than $1,000?` | checkbox | No, Yes |
| 158 | 2 | `Did this crash involve an e-bike or e-scooter in which a person was killed or suffered an injury?` | checkbox | Yes, No |
