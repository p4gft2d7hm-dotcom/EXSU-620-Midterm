# Evidence for the turn thresholds (input for D2)

Prepared 20 October 2026. Sources were checked online. Full texts should be read before final citation, especially where this note relies on an abstract or a guideline summary page.

## Summary

| Parameter | Current value | Evidence | Verdict |
|---|---|---|---|
| Turn angle | 30° change in roll | The international guideline prefers the 30° tilted side-lying position over 90° [1]. An RCT of 30° tilt repositioning reduced pressure ulcers versus usual care [2]. | **Defensible.** Starting from supine, a 30° tilt is exactly a 30° roll change. The margin against sensor error still has to be argued from our calibration (ER-01). |
| Dwell (hold) | 120 s | No source found for 120 s. The largest RCT of a wearable turning sensor defined adequate repositioning as at least **15 min of tissue decompression** every 2 h [3, 4]. | **Not defensible as it stands.** See the options below. |
| Interval | 2 h | This is the ward standard named on the project card, and it was used in the sensor RCT [3]. In nursing homes with high-density foam mattresses, 2-, 3- and 4-hourly turning gave no difference in incidence [5]. | **Keep 2 h** as specified on the card. Make it configurable, and state that the evidence for any single interval is limited. |
| Upright vs in bed | pitch ≥ 60° | The guideline advises keeping head-of-bed elevation at 30° or lower [1]. | Supports a high threshold, but meals and respiratory care can need higher elevation. **State as a limitation** (CR-4). |

## Sources

1. European Pressure Ulcer Advisory Panel, National Pressure Injury Advisory Panel, Pan Pacific Pressure Injury Alliance. Repositioning and mobilization. In: Haesler E, ed. *Prevention and Treatment of Pressure Ulcers/Injuries: Clinical Practice Guideline. The International Guideline.* 2019:115–144. Recommendation as summarised by the NPIAP guided-positioning page (2020): use 30° side-lying in preference to 90° (strength of evidence C); keep head-of-bed elevation at 30° or lower (expert opinion). https://www.vumc.org/pip/sites/default/files/NPIAP%20-%20Side%20Lying%20Positioning.pdf . Evidence tables: https://internationalguideline.com/s/NPIAP_EPUAP_PPPIA_2019-repositioning-mobilization-data-table.pdf
2. Moore Z, Cowman S, Conroy RM. A randomised controlled clinical trial of repositioning, using the 30° tilt, for the prevention of pressure ulcers. *J Clin Nurs.* 2011;20(17-18):2633–2644. Cluster RCT, 213 older adults: 3-hourly night repositioning with 30° tilt gave 3% incidence, versus 11% with 6-hourly 90° lateral turns (p = 0.035). https://www.epistemonikos.org/en/documents/8ae6a62f664594ed97cb30c6770e87e66df8dd5c
3. Pickham D, Ballew B, Ebong K, Shinn J, Lough ME, Mayer B. Evaluating optimal patient-turning procedures for reducing hospital-acquired pressure ulcers (LS-HAPU): study protocol for a randomized controlled trial. *Trials.* 2016;17:190. Chest-worn wearable sensor (Leaf Healthcare). Optimal turning was defined as a turn every 2 h with at least 15 min of tissue decompression. If the patient returns to the back within about 7–8 min, the next turn falls due in 1 h. https://pmc.ncbi.nlm.nih.gov/articles/PMC4823913
4. Pickham D, Berte N, Pihulic M, Valdez A, Mayer B, Desai M. Effect of a wearable patient sensor on care delivery for preventing pressure injuries in acutely ill adults: a pragmatic randomized clinical trial (LS-HAPI study). *Int J Nurs Stud.* 2018;80:12–19. doi:10.1016/j.ijnurstu.2017.12.012. 1,312 ICU patients. Turning compliance was 67% of time with the sensor versus 54% without. Pressure injuries occurred in 0.7% versus 2.3% (OR 0.33, 95% CI 0.12–0.90). Adequate decompression was achieved only 39% of the time, with no difference between groups. https://search.pedro.org.au/search-results/record-detail/62070
5. Bergstrom N, Horn SD, Rapp MP, Stern A, Barrett R, Watkiss M. Turning for Ulcer ReductioN: a multisite randomized clinical trial in nursing homes. *J Am Geriatr Soc.* 2013. doi:10.1111/jgs.12440. With high-density foam mattresses, there was no difference in incidence between 2-, 3- and 4-hourly turning. https://sciencedaily.com/releases/2013/11/131112123918.htm

## What this means for the design

**Angle (CR-3).** 30° is anchored to the guideline position, so it is the natural threshold. The open question is measurement margin. If calibration shows an error of about ±3°, a real 30° tilt can read as 27°. Two honest options for D2:

- Keep 30°, report the miss rate for real 30° tilts in D7, and accept a lower sensitivity.
- Set the detection threshold slightly below 30° (e.g. 30° minus the measured 95th-percentile error) and justify the value from ER-01 data. Do this only after calibration, never to fit results.

**Dwell (CR-3).** 120 s distinguishes a deliberate turn from a fidget, but nothing shows that 2 minutes offloads tissue. The only sensor-based clinical definition found uses **15 minutes**. Options for the group:

1. **Adopt 15 min** (`DWELL_S = 900`), citing [3, 4]. This is the strongest position. Consequence: a turn made at 1 h 50 min is only confirmed at 2 h 05 min, so the critical alarm would already have fired. Handle this by timing the turn from when the hold *started* once it is confirmed, and show a "turn pending confirmation" state so the nurse is not alarmed for a turn already made.
2. **Two-level definition:** "turn detected" after 120 s (stops the advisory from nagging), "effective turn" after 15 min (counts for compliance and the CR-4 audit). This keeps the prompt useful and the audit honest.
3. **Keep 120 s** and state plainly in D2 that it is an engineering choice to reject fidgets, with no tissue-level evidence. This is the weakest option. The card says the thresholds must be defended with evidence, not chosen because they look reasonable.

Option 2 fits the card well: it keeps the advisory/critical behaviour of Figure 3 and makes the compliance figure match the published definition.

**Interval (CR-2).** Keep 2 h as specified. Note in D2 that the evidence for any particular interval is limited [5] and that the interval is a configuration parameter.

## Not found (worth stating in D2)

- No published numeric angle threshold for a sensor-detected turn in the trials above. The Leaf protocol describes angle and decompression thresholds as configurable but gives no numbers [3].
- No tissue-perfusion study was reviewed here. A physiology reference on reperfusion after offloading would strengthen the dwell argument if someone in the group has one.
