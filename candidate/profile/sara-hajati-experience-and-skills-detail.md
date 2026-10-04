# Sara Hajati: Work Experience and Skills in Detail

Sources: both CV versions in this project (Word and PDF), your saved job search notes, and the Vention business case deck. Nothing here is added from outside those sources. Where the sources disagree, I say so.

## 1. Summary of the profile

Technical Product Lead with 6+ years across marine transportation, ecommerce, blockchain and Web3. The CV positions you around product strategy, analytics infrastructure, UX optimization, customer data platforms, marketing attribution and revenue growth, and around turning early-stage products into scalable, data-driven platforms.

Career arc: Product Data Analyst (2019), Associate PM (2020), PM (2020 to 2022) at Digikala, Technical PM at Wallex (2022 to 2023), Technical Product Lead at Hullo (2023 to now).

---

## 2. Hullo (VIFC), Technical Product Lead
Vancouver, British Columbia | Dec 2023 to present
A ferry service between Vancouver and Nanaimo. You work remotely from Montreal and own all of Hullo's digital assets. Your scope extends past core TPM work into data analytics and marketing.

### Results on the CV
- Booking conversion up 15% by moving from a WordPress booking frontend to a custom API experience
- Ad conversion up 26% through tracking implemented across multiple platforms
- Marketing costs down 20% to 22% through better data quality and targeted campaigns
- Yield and capacity based fare structure, using demand data, drove a 10.3% year over year revenue increase
- Add-on features such as luggage options launched to raise booking value
- Segment CDP and an event taxonomy unified data for segmentation and campaign optimization
- Ketch CMP implemented for consent management and privacy compliance
- Analytics foundation and dashboards for strategic decisions (the PDF version adds "automated Python reports")

### Data infrastructure, built in stages
1. You started with only VM-based access to the booking and inventory vendor's data mart. This was a vendor contract limitation, with no direct database connection.
2. You wrote Python scripts on that VM that produced CSV reports and emailed them out. Reports were later stored in Azure Blob Storage and connected to Power BI for dashboards.
3. You used Cursor yourself to answer ad hoc, one-off questions directly.
4. You got budget for Hullo's own DigitalOcean instance and set up a nightly full dump of the vendor's database into your own data lake there. This was not API-level access.
5. You built an MCP-based natural language agent on top of that clone. Tools are scoped to the specific schema, queries have built-in cost limits (row limits and timeouts) to protect the database, and a regression test set of real questions runs on every change. Non-technical staff can query data in plain language.

### Segment implementation
- Led the implementation
- Ran a discovery meeting with Teddy and Hari from GrowthBench covering event schema, identity resolution, cookie compliance and a phased rollout (production launch targeted around August 2025)
- Coordinated developer tasks and taxonomy review
- Ran a marketing team alignment meeting on how Segment connects to advertising platforms
- Worked directly with Segment on both the contract and the integration

### Vendor and stakeholder management
- Managing technical vendors has been your responsibility since you joined, because Hullo is small
- You own the booking and inventory system vendor relationship
- You manage the external dev team behind the booking website
- You share responsibility with an external marketing agency
- You negotiated a good deal with Hullo's CRM platform
- You are currently leading an RFP to switch the booking and ticketing system, meeting multiple vendors and involving internal teams
- Internal stakeholders you serve: operations, finance, sales and marketing
- You collaborate with CEO Sekhar and produced a customer booking summary report for him with behavioral and LTV metrics

### Other work at Hullo
- RadLab Risk Assessment Report for the board (source code access risks, booking flow dependencies, severity-tiered recommendations)
- Vendor evaluation report covering Freshdesk, Customer.io, Freshmarketer and Segment
- Review of marketing and digital assets after concerns about broken social media links
- Converted a canonical fare product matrix from markdown into a formatted Word document for the booking system reference
- Prepared a compensation and scope conversation with your manager, framing role expansion across TPM, marketing and analytics with Montreal benchmarks

### A decision you pushed back on
Management asked for a price recommendation model trained only on Hullo's internal data. You argued that route growth and pricing power also depend on competitor pricing and broader market conditions, which an internally trained model would miss.

---

## 3. Wallex, Technical Product Manager
Jun 2022 to Dec 2023
Iran's leading crypto exchange. You were Technical PM on the Blockchain team. (Your notes also list systems and business analysis at Wallex Group in your background.)

### Results on the CV
- Web3 transaction failure rate cut from 3.54% to 0.58% by identifying and fixing common issues. Your notes tie this specifically to the automated blockchain node-failover system: anomaly and time-series based degradation detection that switches nodes automatically with no human intervention, which you describe as an agentic workflow. Related support tickets fell 12%.
- Withdrawal times cut from 45 minutes to 15 minutes by automating rebalancing for fund allocation
- Refund processing cut from 90 days to 1 day through automation
- OKRs and KPIs set for the blockchain and Web3 teams, using SQL and Grafana dashboards for real-time insight (you also used Databricks and Metabase for analytics)
- Led Agile ceremonies for collaboration and alignment across teams
- Ran market research through surveys, interviews and competitive analysis to address user pain points and follow Web3 trends

### On-call alerting for listed assets
After the November 2022 GALA token incident you built an alerting system for listed crypto assets. It monitors on-chain supply and mint events and keyword-scans project and security-researcher social accounts, then pages the on-call team to decide whether to halt a market. You built it in 2022, before capable LLMs were practical for the summarization and classification layer.

---

## 4. Digikala, Iran's largest ecommerce platform (40M+ active users)

### Product Manager, Oct 2020 to Jun 2022
Customer success and revenue focus.
- Scaled the Digikala Jet MVP from 50 to 10,000 daily orders in 8 months
- Add to Cart rate up from 26% to 38.5% with cashback and bundle pricing
- Cart abandonment down from 57% to 43% with push notifications and multiple payment options
- Worked with design and UX using A/B testing, Google Analytics and Hotjar
- Managed the roadmap, prioritizing by business goals and user needs
- Replenishment and recommendation model, built with the data science team: predicts reorders from purchase history and typical gaps between purchases per category. Evaluated with a holdout control group and repeat order rate. The exact lift figure was not retained.
- Product matching across vendors, with an ML engineer and a data scientist. Hundreds of Iranian supermarkets and grocery stores supplied catalogs with inconsistent names and often no barcodes, so the same product could not be matched by a shared identifier. Scale was potentially millions of listings. Your role was defining the business problem and matching logic (what counts as a correct match, and the cost of a false match versus a missed match), not implementing it. You do not recall the specific algorithm.
- Worked with many vendors, grocery stores and shops, and part of managing them was your responsibility
- Worked with very large production and dev datasets; data modeling was a recurring challenge

### Associate Product Manager, May 2020 to Oct 2020
Fulfillment and automation team.
- Cost Per Item down 15% through data analytics on single-item orders in distribution centers
- Applied a data-driven bin-packing algorithm to optimize box sizes (the CV says this "increased monthly Packing Cost by 12%", see the flag in section 8)

### Product Data Analyst, Jun 2019 to May 2020
- Analyzed large datasets for trends, patterns and correlations using SQL and Python
- Built visualizations in Tableau and Power BI for data-centric decisions

---

## 5. Skills

### Listed on the CV
Agile methodologies (the PDF says Agile/Scrum), data analytics, API integration, customer lifecycle marketing, performance optimization, user experience improvement, Agile project management, market research analysis, product strategy, system integration, platform migration, technical requirements.

### Tools and technologies you have used
- Data and analytics: SQL, Python, Tableau, Power BI, Grafana, Databricks, Metabase, Google Analytics, Hotjar
- Data platforms and cloud: Segment CDP, Ketch CMP, Azure (Blob Storage and integrations), DigitalOcean
- AI and developer tools: Cursor (daily), Claude, Claude Code, Model Context Protocol (MCP)
- Content and presentation: Canva, Buffer, CapCut, pptxgenjs
- Experimentation: A/B testing

### Skill areas shown by the work
- Product strategy and roadmap management, 0 to 1 launches and scaling
- Growth and conversion optimization (cart, checkout, ads, bookings)
- Yield and pricing strategy
- Analytics foundations: dashboards, event taxonomy, CDP, attribution, consent and privacy compliance
- Platform migration and system integration, including frontend replacement through custom APIs
- Process automation (refunds, rebalancing, node failover, alerting)
- Applied AI and data work: replenishment model, product matching, anomaly detection, natural language database agent
- Vendor management, contracts and RFP leadership
- Stakeholder work across operations, finance, sales, marketing, executives and boards
- Agile leadership and OKR/KPI design
- Market and user research: surveys, interviews, competitive analysis

### Working traits you describe in yourself
- Enters unfamiliar, ambiguous domains and becomes the person others rely on
- Data-first, with "how do we know that?" as a habit
- Thrives in growth phase and 0 to 1, loses energy in maintenance mode
- Catches claims that outrun the evidence and corrects them
- Prefers honest drafts that admit gaps, and expects every claim to survive interview follow-up

---

## 6. What the Vention business case shows about your skills

Your Vention deck is a work sample. It shows:
- Hands-on product investigation: you built a machine configuration, wrote the same task in the Code-free editor and in Python, pulled a real application with the CLI, and ran Claude Code against it twice (blind and grounded in the repo), then ran its output on a live digital twin
- Segmenting users (Vention Applications, technical customers, non-technical customers, maintainers) and stating the assumptions your recommendation rests on, including the one that would change your mind
- Product design through user journeys rather than a single screen
- A phased roadmap with a north star metric, a leading metric and a kill switch
- Risk framing built around structural design decisions rather than guardrails
- Technical reading of documentation and SDKs, comparing state machine models and counting the command set
- Questions you put to Brendan Sterne to settle points you could not answer from outside

---

## 7. Education and training

- Master of Engineering, Concordia University, Canada, April 2025 (part time)
- Master of Business Administration, University of Tehran, September 2022
- Bachelor of Electrical and Computer Engineering, University of Tehran
- Preparing for the CELPIP exam; learning French

---

## 8. Things to resolve in your documents

1. **MEng title:** the Word CV says "Computer and Information Systems", the PDF CV says "Software Engineering", and your profile notes say "Computer and Information Technology". Pick the exact name on your degree.
2. **Digikala APM bullet:** both CVs say you "increased monthly Packing Cost by 12%". If the bin-packing algorithm saved money, this probably should say "reduced". Check the real number and direction.
3. **Title typo:** "Associated Product Manager" appears in both CVs; the usual title is "Associate".
4. **Daily orders vs monthly customers:** keep "10,000 daily orders" consistent, since a verbal "10,000 monthly customers" once conflicted with the CV.
5. **Skills list:** the PDF lists "API integration" and "API Integration" twice.
6. **Wallex failure rate:** the CV says 3.54% to 0.58%, your notes say about 3.5% to 0.58%. Both match, just keep one form.
7. **Role framing:** your notes are clear that you are not an AI/ML PM, so keep titles and summary at their real breadth. The Word CV summary says "over six years"; the PDF says "6+ years".
8. **Digikala Jet replenishment lift:** no figure is on file. Say that plainly if asked.
