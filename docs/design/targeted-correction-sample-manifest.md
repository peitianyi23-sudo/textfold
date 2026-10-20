# Targeted correction exploratory sample

Subsequent implementation/evaluation: [verification](targeted-correction-verification.md). The selection record below predates that work.

Selected read-only from the existing Zotero library on 2026-10-20 by two agents. All ten exact local PDF
attachments exist, physical page counts were measured with pdfinfo, and each has an existing MinerU full.md.
No conversion, correction, library/cache writes, downloads, or full visual PDF comparison ran.
This is a candidate corpus and preliminary text inspection, not a quality benchmark or error-frequency study.

## Main selection

| Journal | Paper | Year | Physical pages | Parent ID / key | PDF attachment ID / key |
|---|---|---:|---:|---|---|
| PRL | Energy Spectra for Decaying 2D Turbulence in a Bounded Domain | 2000 | 4 | 2950 / 8ZDCVP5H | 2951 / 4I6IB88E |
| PRL | Physical Mechanism of the Two-Dimensional Inverse Energy Cascade | 2006 | 4 | 2981 / GDSSABQJ | 2982 / BCLH4QQK |
| PRL | Advection and the Efficiency of Spectral Energy Transfer in Two-Dimensional Turbulence | 2016 | 5 | 3353 / 63EHZJ6E | 3354 / EAPKNRSZ |
| PRF | Spectral condensation in laboratory two-dimensional turbulence | 2021 | 9 | 2792 / IQIFUBSD | 2793 / UYSYD4X6 |
| PRF | Local-flux vectors of conserved quantities in wavenumber space: Anisotropic structures in Charney--Hasegawa--Mima turbulence | 2022 | 9 | 2877 / K24JQ9AA | 2878 / SAXDFCTS |
| JFM Rapids | Vortex patterns in rapidly rotating Rayleigh–Bénard convection under spatial periodic forcing | 2022 | 11 | 3205 / U4GGYGRV | 3206 / LH25ZI5H |
| JFM | Energy and enstrophy fluxes in the double cascade of two-dimensional turbulence | 2007 | 8 | 3505 / HNQX8BPJ | 3506 / MLMPBK65 |
| JFM Rapids | Exploring the severely confined regime in Rayleigh–Benard convection | 2016 | 13 | 50 / SQKCGF3D | 148 / P4GQ4IDR |
| PoF | Experimental quantification of inverse energy cascade in deep rotating turbulence | 2013 | 10 | 3835 / CY27JMKZ | 3836 / RMBNNHD6 |
| PoF | Spectrally condensed turbulence in thin layers | 2009 | 11 | 3144 / AYJAGSJK | 3145 / WYGAA7FE |

Total: 84 physical pages. Nine papers are 4–11 pages; one JFM Rapids publisher PDF is 13 pages, a deliberate
exception to the initial approximate twelve-page preference. Its Cambridge attachment URL identifies
S0022112016005784a.pdf, DOI 10.1017/jfm.2016.578. Zotero metadata has the title typo "con fined";
the selected attachment identity, rather than the normalized display title, is authoritative.
The sample is concentrated in turbulence/convection and does not represent all disciplines or journal layouts.

## Exact local inputs

Cache root is `D:/Paper/Zotero lib/llm-for-zotero-mineru/`; append the numeric attachment ID above and `/full.md`.
PDF filenames, relative to `D:/Paper/Zotero lib/storage/`:

```text
4I6IB88E/Clercx_van Heijst_2000_Energy Spectra for Decaying 2D Turbulence in a Bounded Domain.pdf
BCLH4QQK/Chen et al_2006_Physical Mechanism of the Two-Dimensional Inverse Energy Cascade.pdf
EAPKNRSZ/Fang_Ouellette_2016_Advection and the Efficiency of Spectral Energy Transfer in Two-Dimensional.pdf
UYSYD4X6/Fang_Ouellette_2021_Spectral condensation in laboratory two-dimensional turbulence.pdf
SAXDFCTS/Takaoka et al_2022_Local-flux vectors of conserved quantities in wavenumber space.pdf
LH25ZI5H/Ding et al_2022_Vortex patterns in rapidly rotating Rayleigh–Bénard convection under spatial.pdf
MLMPBK65/Boffetta_2007_Energy and enstrophy fluxes in the double cascade of two-dimensional turbulence.pdf
P4GQ4IDR/Chong_Xia_2016_Exploring the severely con fined regime in Rayleigh-Benard convection.pdf
RMBNNHD6/Yarom et al_2013_Experimental quantification of inverse energy cascade in deep rotating.pdf
WYGAA7FE/Xia et al_2009_Spectrally condensed turbulence in thin layers.pdf
```

Do not assume uniform cache filenames. Cache 2793 has UUID-prefixed content-list JSON and layout.json;
older restored caches such as 2951, 2982 and 3354 have content_list.json and _llm_source.json.
Presence of a layout file does not establish correctness of its coordinates.

## Preliminary text-only candidates

These are specific suspicious extractions, not PDF-confirmed corrections. Locations refer to each cache's full.md.
No denominator or systematic search protocol exists for these observations; do not turn them into error rates.

- 2951, line 13: `$k ^ { - 5 7 3 }$`; abstract elsewhere uses -5/3. Suspect exponent corruption.
- 2951, line 15: rendered tau formula followed by raw `v0tN`. Suspect duplicated formula residue.
- 3354, lines 13–15: blank paragraph after `little change;` before `consistently, these cases`. Suspect fragmentation.
- 3506, line 11: `\varepsilon ^ { 2 7 3 }`, and `\dot { E } ( k )` in the same spectrum discussion. Suspect math recognition.
- 3506, line 11: prose ends `is the vorticity).` without the apparent opening parenthesis. Suspect text/math boundary.
- 3145, line 15 (also lines 5 and 13): U+0001 appears where delimiters may have been misrecognized.
- 3145, line 15: `$\circledcirc$ 2009 American Institute of Physics`. Suspect copyright recognition.
- 3836, lines 3–7: AIP promotional material precedes the title. Possible extraction boilerplate, distinct from math errors.

The presence of these real control characters makes them supported-data cases, rather than hypothetical exotic
encoding hardening. Whether any requires a source change still depends on the exact PDF evidence.

## Backups and version exclusions

- PRL Xia et al. 2008, Turbulence-Condensate Interaction in Two Dimensions: parent 3001/ZS6X7R8Y;
  PDF 3002/VRPFNMBN, four pages, cached.
- PRF Lemasquerier et al. 2020, Gas giant–like zonal jets in the laboratory: parent 1364/APUYQ3SU;
  PDF 1363/UMWXRHHG, five pages, cached; Gallery of Fluid Motion, less equation-rich.
- JFM Xia 2019, Tuning heat transport via boundary layer topographies: parent 39/36VJLQLP;
  PDF 109/AVYPDP4V, four pages, cached; Focus on Fluids commentary.
- PoF Paret/Tabeling 1998, Intermittency in the two-dimensional inverse cascade of energy: Experimental observations:
  parent 3047/KFHKE48G; PDF 3046/SCJNUVL8, eleven pages, cached.
- Zhou/Xia 2011, Disentangle plume-induced anisotropy in the velocity field in buoyancy-driven turbulence:
  JFM parent 79/WLQACHJI; PDF 112/23RGP9VA, ten pages, cached. The attachment is an arXiv version;
  retain as a preprint-layout backup, not evidence for JFM publisher-layout coverage.

## Approved evaluation split

All papers have been selected by availability/length/journal, not known error counts. Preliminary text inspection
has already exposed examples in several papers; those cannot honestly be called blind held-out material.
The user approved the following split and independent PDF reference review of the evaluation set on 2026-10-20:

- Discovery: attachments 2951, 3354, 3506, 3145, 3836, whose text has already been skimmed.
- Evaluation: attachments 2982, 2793, 2878, 3206, 148. Keep these out of pattern tuning.

An evaluation of missed errors needs independent PDF reference work on the test corpus; only rechecking
detector-selected candidates cannot measure recall. That test-only reference work does not imply a per-page
production correction workflow. Reference review and performance measurements have not yet run.

See [the open design discussion](targeted-extraction-correction-discussion.md) for accepted decisions and frontier.
