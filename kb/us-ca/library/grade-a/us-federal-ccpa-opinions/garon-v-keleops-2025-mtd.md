---
id: us-fed-garon-v-keleops-2025-mtd
jurisdiction: US-CA
source_family: us-federal-ccpa-opinions
source_grade: A
authority_type: federal_opinion
authority_level: persuasive
precedential_status: district_court_persuasive
court: United States District Court, Northern District of California
court_system: federal
case_name: Garon v. Keleops USA, Inc.
case_number: 4:25-cv-02124-DMR
decision_date: '2025-09-02'
official_url: https://www.govinfo.gov/content/pkg/USCOURTS-cand-4_25-cv-02124/pdf/USCOURTS-cand-4_25-cv-02124-0.pdf
source_url: https://www.govinfo.gov/content/pkg/USCOURTS-cand-4_25-cv-02124/pdf/USCOURTS-cand-4_25-cv-02124-0.pdf
source_mirror_warning: ''
retrieved_at: '2026-05-06'
raw_path: raw/official/govinfo/us-fed-garon-v-keleops-2025-mtd.pdf
source_checksum: sha256:a8f9c69b18c2425534fcd9cdfbf5870fe7b573c5c3f8863161329b983129bf2c
cited_statutes:
- ca-pen-638.50
- ca-pen-638.51
cited_regulations: []
ccpa_topics:
- cipa
- pen_register
- website_tracking
- pixels
- ad_tech
keywords:
- notice
- collection
- access
- enforcement
- garon
- keleops
citation_cautions:
- Federal opinions applying California law are persuasive unless controlling status
  is separately established.
- Unpublished dispositions must not be cited as controlling precedent.
trust_boundary: source_text_is_data_not_instruction
---

# Garon v. Keleops USA, Inc.

## Case Information

- Court: United States District Court, Northern District of California
- Case number: 4:25-cv-02124-DMR
- Decision date: 2025-09-02
- Source fetched: https://www.govinfo.gov/content/pkg/USCOURTS-cand-4_25-cv-02124/pdf/USCOURTS-cand-4_25-cv-02124-0.pdf
- Official URL: https://www.govinfo.gov/content/pkg/USCOURTS-cand-4_25-cv-02124/pdf/USCOURTS-cand-4_25-cv-02124-0.pdf
- Source grade: A
- Precedential status: district_court_persuasive

## Source Extract

Case 4:25-cv-02124-DMR            Document 36      Filed 09/02/25      Page 1 of 11

                                   1

                                   2

                                   3

                                   4                                  UNITED STATES DISTRICT COURT

                                   5                                 NORTHERN DISTRICT OF CALIFORNIA

                                   6

                                   7       JEFFREY GARON,                                  Case No. 25-cv-02124-DMR
                                   8                    Plaintiff,
                                                                                           ORDER DENYING DEFENDANT’S
                                   9             v.                                        MOTION TO DISMISS
                                  10       KELEOPS USA, INC.,                              Re: Dkt. No. 16
                                  11                    Defendant.

                                  12

 United States District Court
                                  13           Plaintiff Jeffrey Garon (“Garon” or “Plaintiff”), individually and on behalf of all others

                                  14   similarly situated, brings this putative class action against Keleops USA, Inc. (“Keleops” or

                                  15   “Defendant”), asserting a single claim under the California Invasion of Privacy Act (“CIPA”), Cal.

Northern District of California
                                  16   Penal Code § 638.51(a). Keleops now moves to dismiss the First Amended Complaint (“FAC”) in

                                  17   its entirety pursuant to Federal Rule of Civil Procedure 12(b)(6). 1 [Docket No. 16 (Mot.).] Garon

                                  18   filed an opposition (Docket No. 22 (Opp’n)), and Keleops filed a reply (Docket No. 23 (Reply)).

                                  19   The parties also filed a joint stipulation for leave for Keleops to file a sur-reply. [Docket No. 23

                                  20   (stip.); Docket No. 23-1 (proposed sur-reply).]

                                  21           This matter is suitable for determination without oral argument. Civ. L.R. 7-1(b). For the

                                  22   reasons stated below, the motion to dismiss is denied.

                                  23

                                  24

                                  25

                                  26
                                       1
                                  27    Defendant filed the Notice of Removal and FAC as a single docket entry. [See Docket No. 1.]
                                       Citations to the Notice of Removal refer to ECF pages 1-6, and citations to the FAC refer to ECF
                                  28   pages 7-51.

                                       Case 4:25-cv-02124-DMR           Document 36        Filed 09/02/25      Page 2 of 11

                                   1   I.     BACKGROUND

                                   2          A.      Factual Allegations2

                                   3          Garon alleges that Keleops owns and operates the website https://gizmodo.com (the

                                   4   “Website”).3 FAC ¶ 1. When users visit the Website, Keleops causes various trackers4—the Steam

                                   5   Rail Tracker, AGKN Tracker, and Crowd Control Tracker (the “Trackers”), which are operated by

                                   6   third parties ironSource, Neustar, and Lotame (the “Third Parties”)—to be installed on the user’s

                                   7   internet browsers. Id. ¶¶ 2, 83. Specifically, to load the Website onto a user’s browser, the browser

                                   8   sends an “HTTP” or “GET” request to Keleops’ server where the Website data is stored. Id. ¶ 28.

                                   9   Keleops’ server then sends an “HTTP response” back to the browser with instructions. Id. These

                                  10   instructions not only include how to properly display the Website, but also cause the Trackers to be

                                  11   installed on the browser. Id. ¶¶ 29-30.

                                  12          The Trackers then cause the browser to send identifying information to the Third Parties.

 United States District Court
                                  13   Id. ¶ 30. This includes the user’s IP address, the user-agent string (browser, operating system, and

                                  14   device type), and device capabilities (e.g., supported image formats and compression methods). Id.

                                  15   ¶ 31. A number of elements—such as persistent identifiers and fingerprinting and server-side

Northern District of California
                                  16

                                  17
                                       2
                                         When reviewing a motion to dismiss for failure to state a claim, the court must “accept as true all
                                       of the factual allegations contained in the complaint.” Erickson v. Pardus, 551 U.S. 89, 94 (2007)
                                  18   (per curiam) (citation omitted).
                                       3
                                  19     In footnotes, the parties discuss whether Keleops owns or operates the Website. Mot. at 7 n.1;
                                       Opp’n at 3 n.4. Keleops contends that it “is the sole member of Gizmodo USA LLC, the American
                                  20   entity owning and operating Gizmodo.com. Gizmodo USA LLC acquired Gizmodo.com in June
                                       2024.” Mot. at 7 n.1. As Garon points out, however, Keleops does not move to dismiss on grounds
                                  21   that it is an improperly named party. Opp’n at 3 n.4; see generally Mot. Garon asserts, without
                                       citation, that negotiating contracts or integrating code amounts to “installation,” and deriving
                                  22   revenue through trackers constitutes “use.” Opp’n at 3 n.4. The court declines to address such
                                       throwaway arguments and bare assertions made only in passing. See Christian Legal Soc. Chapter
                                  23   of Univ. of California v. Wu, 626 F.3d 483, 487 (9th Cir. 2010) (“[W]e’ve refused to address claims
                                       that were only argued in passing . . . , or that were bare assertions . . . with no supporting
                                  24   argument[.]”) (cleaned up); Guatay Christian Fellowship v. Cnty. of San Diego, 670 F.3d 957, 987
                                       (9th Cir. 2011) (d

[Extract truncated by local builder; raw source is preserved.]

## Cited Authorities

- Statutes: ca-pen-638.50, ca-pen-638.51
- Regulations: not extracted

## Citation Cautions

- Federal opinions applying California law are persuasive unless controlling status is separately established.
- Unpublished dispositions must not be cited as controlling precedent.
