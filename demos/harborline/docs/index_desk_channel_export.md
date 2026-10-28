# #index-desk — channel export

Workspace: Harborline Private Capital
Channel: #index-desk (index research, fund data operations, client solutions)
Export range: 2026-08-24 to 2026-10-09
Exported by: Analytics Engineering for the analytics onboarding pack

## 2026-08-24

**Priya N. (Client Solutions)** 09:12
Westbrook's analyst asked again why their 2018 vintage is behind. Which view do I point them at?

**Marcus L. (Index Research)** 09:20
V_ALLOCATOR_VINTAGE_VS_BENCHMARK filtered to Westbrook State Retirement System. 2018 is the only vintage with a negative gap: portfolio IRR 8.5 against 12.0 for the matching indices, about 3.5 points behind. Then V_ALLOCATOR_HOLDINGS for the funds: Bramblewood Ventures III is 15.7 points under the NA venture 2018 cohort and Sable Point Ventures II is 12.2 under. The other six 2018 positions are at or above benchmark. Every other Westbrook vintage is at or above too.

**Priya N.** 09:23
"The two Vs" again. Thanks.

## 2026-08-28

**Dana O. (Fund Data Operations)** 14:05
Calder Ridge IV Q2 report came in on the 21st. Extraction ran clean: NAV 2,614.0, calls 64.0, distributions 96.0, line balance 210.0, confidence 0.97, auto-accepted. It matches what the LP feed already had so nothing to reconcile.

**Marcus L.** 14:10
Good. That is the fund I use in training because the report and the feed agree to the decimal. IRR 18.4, TVPI 1.31, DPI 0.40.

**Dana O.** 14:12
Reminder for everyone: anything with confidence under 0.90 goes to the analyst review queue. 47 in review and 17 corrected across the two latest quarters out of 711 extractions.

## 2026-09-03

**Tomas R. (Index Research)** 11:40
Custom index question from a Premium client: North American buyout, vintages 2015 to 2020, against the broad PE benchmark. Answer I gave: 49 funds, median IRR 15.9 percent at 30 June versus 13.3 for HPCI-BROAD-PE all vintages, pooled TVPI 1.58 versus 1.54. By size bucket the mid-market funds lead at 16.3 median and the mega funds trail at 13.1.

**Marcus L.** 11:44
Use the median for the cohort headline and say so. The published index number is capital weighted, which is why the mega funds pull HPCI-BUYOUT-NA down to 13.4 even though most of the cohort is above 15.

**Tomas R.** 11:45
Yes. Also reminded them V_COHORT_INDEX_QUARTERLY has the elementary cohorts so they can widen or narrow without a new query.

## 2026-09-11

**Lena F. (Index Research)** 16:02
Sub-line note for the methodology update. For vintages 2019 to 2022, funds with a subscription line average 7.4 percent IRR at eight quarters of age against 2.3 for funds without, so a gap of about 5 points. At four quarters it is 2.9 against -4.3. For 2014 to 2017 the gap at 30 June is under 1.5 points, so it washes out with age as expected.

**Marcus L.** 16:08
That goes in v2.1 section 6 with the 15 percent of NAV watch threshold. 89 funds had a drawn balance at 30 June, about 17 billion in total; only five are above 15 percent of NAV.

## 2026-09-22

**Priya N.** 10:31
Pacing question from an endowment: why are their 2021 and 2022 funds not distributing. What is the house answer?

**Tomas R.** 10:38
Distribution drought. At sixteen quarters of age the 2021 and 2022 vintages have a median DPI around 0.16; the 2014 to 2016 vintages were at 0.55 to 0.60 at the same age. Universe-wide, first-half 2026 distributions were about 36 billion against about 64 billion in first-half 2021, so roughly 44 percent lower. V_CASH_FLOW_PACING_QUARTERLY by vintage and fund age shows it.

## 2026-10-09

**Marcus L.** 08:55
Reminder that the as-of date for the portal is 15 October and the latest published quarter stays 30 June until the Q3 refresh on 29 December. Anyone asked for "this quarter" numbers means Q2 2026.

**Dana O.** 09:02
And liquidated funds (25 of them, mostly 2012 and 2013 vintages) stop reporting, so filter to the 30 June rows when you mean active funds.
