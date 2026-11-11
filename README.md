# Thailand NCDs Intelligence v1.5 | Thailand NCDs Intelligence v1.5

**Offline-first, iPad-compatible interactive analytics portfolio** built from user-supplied World Bank World Development Indicators (WDI) CSV exports. Indicator: `SH.DYN.NCOM.ZS`. Source export header reports last updated **2026-10-08**. Years **2000–2021**, **11 ASEAN countries**, **242 country-year observations**.

## Open / วิธีเปิด

1. Extract this ZIP in the iPad Files app.
2. Open `dashboard/index.html` in a browser or an HTML file viewer that executes JavaScript. Some iPad file previewers block local scripts; if so, serve this folder over a local HTTP server or deploy only after authorization.
3. Change the year, focus country, language, and dashboard tab. All values and the Plotly library are embedded. No runtime network is required.

**Status:** Source-to-dashboard data parity and static JavaScript syntax verified; no browser end-to-end execution on Safari/iPad was performed. No Power BI Desktop, PBIX, or GitHub deployment is claimed.

## Case study — English

**Problem.** Compare the estimated probability of premature mortality (ages 30–70) from cardiovascular disease, cancer, diabetes, or chronic respiratory disease in Thailand and ASEAN peers using consistent observation years.

**Approach.** Validate World Bank export schema and indicator, preserve raw files with SHA-256 fingerprints, select 11 countries and a complete common-year panel, reconcile 242 observations against the original export, and build an interactive offline dashboard with country/year filters.

**Results.** Thailand: **18.3% (2000)** versus **14.5% (2021)**, a change of **−3.8 percentage points** (−20.77% relative). The **unweighted** ASEAN-11 country mean in 2021 was **20.6091%**; Thailand was **6.1091 percentage points lower** and ranked **second lowest** in the set. These are descriptive findings, not causal estimates or statistical significance claims.

**BI design.** The retained Enterprise BI Specification includes a star schema, DAX dictionary, year-wise KPI reference, and filter-context test matrix. DAX runtime execution remains unverified because Power BI Desktop was not available.

**Methodology.** The indicator is a model-based probability, not a death count or crude mortality rate. The ASEAN mean gives equal weight to each country, not each person. The common panel excludes later years with incomplete values. Cross-country comparisons do not adjust for uncertainty intervals or model revisions. Ecological data cannot identify individual risk or causal effects.

**Data governance.** The package contains only public aggregate country-year indicators. Source CSV and metadata are preserved, hashes recorded, and downstream CSV parity tested. A local SHA-256 digest establishes byte integrity of the supplied file, not independent authentication against the World Bank server. Check the current redistribution and attribution conditions before public release.

**Skills evidenced.** Python/Pandas validation, data lineage, source reconciliation, statistical descriptive comparison, BI dimensional modeling, Plotly interactive visualization, bilingual technical documentation, and automated testing.

## กรณีศึกษา — ภาษาไทย

**ปัญหา:** วิเคราะห์ความน่าจะเป็นของการเสียชีวิตก่อนวัยอันควร (อายุ 30–70 ปี) จากโรคหัวใจและหลอดเลือด มะเร็ง เบาหวาน และโรคทางเดินหายใจเรื้อรังของประเทศไทยเทียบกับประเทศอาเซียน โดยใช้ช่วงปีเดียวกัน

**วิธีดำเนินการ:** ตรวจ Schema และ Metadata ของไฟล์ World Bank ที่ได้รับ เก็บ SHA-256 เลือก 11 ประเทศและปีที่มีข้อมูลครบทุกประเทศ ตรวจค่ากลับกับไฟล์ต้นทาง 242 ระเบียน และสร้าง Dashboard HTML/Plotly แบบไม่ต้องเชื่อมต่ออินเทอร์เน็ต

**ผลลัพธ์:** ไทยมีค่า 18.3% ในปี 2000 และ 14.5% ในปี 2021 ลดลง 3.8 จุดร้อยละ (ลดลงสัมพัทธ์ 20.77%) ค่าเฉลี่ยเลขคณิตของ 11 ประเทศในปี 2021 เท่ากับ 20.6091% ไทยต่ำกว่าค่าเฉลี่ย 6.1091 จุดร้อยละ และมีค่าต่ำเป็นอันดับ 2 ของกลุ่ม

**ข้อจำกัด:** ตัวชี้วัดเป็นค่าความน่าจะเป็นที่ประมาณจากแบบจำลอง ไม่ใช่จำนวนผู้เสียชีวิต ค่าเฉลี่ยอาเซียนไม่ถ่วงน้ำหนักประชากร ไม่ได้ทดสอบนัยสำคัญหรือสรุปความสัมพันธ์เชิงสาเหตุ ข้อมูลระดับประเทศไม่สามารถนำไปอนุมานความเสี่ยงรายบุคคลได้

**ธรรมาภิบาลข้อมูล:** รักษาไฟล์ต้นฉบับและ Metadata จัดทำ Manifest SHA-256 ตรวจความสอดคล้องระหว่างข้อมูลต้นฉบับกับชุด Dashboard และแยกสถานะการทดสอบโค้ดออกจากการทดสอบบน Safari/Power BI จริง

## Structure

- `dashboard/index.html`: self-contained interactive dashboard (embedded Plotly)
- `data/`: original World Bank CSVs, metadata, BI-ready fact/dimensions
- `bi_spec/`: frozen Power BI specification (not runtime certified)
- `docs/`: bilingual release and QA documentation
- `evidence/`: source hashes, KPI references, test results
- `tests/`: offline automated regression tests
- `build_v15.py`: deterministic build and source reconciliation

## Reproduce

Python 3.11+, `pandas`, `plotly`; execute `python build_v15.py`, then `python -m unittest discover -s tests -v` from this folder. The build script expects the supplied v1.4 input folder and original World Bank export at their source paths; use the packaged data files to adapt the paths for another machine. The distributed HTML itself needs no Python runtime.

## Release gate

**GO:** offline artifact creation, source-data reconciliation, structural validation, 22 automated tests.
**HOLD:** verified Safari/iPad interactive behavior, WCAG conformance, live source authentication, Power BI Desktop/DAX runtime, public deployment.
