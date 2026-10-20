# TextFold reading

## Language

**Reference list (bibliography)**:
The list identifying the works cited by a document, with entries such as authors, titles and publication dates.
It is distinct from the document's discussion of earlier research.
_Avoid_: Prior Work, Related Work

**Related Work discussion**:
The author's narrative explaining earlier research and its relationship to the present work.
It is part of the article's argument, distinct from the reference list.
_Avoid_: Bibliography, reference list

**Figure**:
A visual illustration or plot, possibly comprising several panels under one shared caption.

**Table**:
Information organized in rows and columns, distinct from a plotted or illustrated figure.

**Figure panel**:
One part of a figure, often identified by a label such as (a) or (b).
Several panels can belong to one figure and share its caption.
_Avoid_: Figure, when referring only to one of its panels

**Figure caption**:
The author's description of a figure and its panels.
Its continuation across columns remains part of the same caption.

**Extracted block**:
A region reported by a document extractor.
An extracted image block can contain a complete figure or only part of one.
_Avoid_: Figure, unless the block contains the complete figure

**Model discovery**:
Finding model choices from local agents, running local model services and saved provider lists.
Discovery identifies choices; it does not establish that a model can successfully answer a request.
_Avoid_: Connection test

**Connection test**:
A small actual model request used to check whether the selected model can answer.
_Avoid_: Model discovery

**Extraction correction**:
Restoring extracted text, mathematics and paragraph structure to match the selected original document.
It is distinct from summarizing, translating or rewriting the author's content.
_Avoid_: Summary revision

**Correction scope**:
The content selected for extraction correction: a whole document, a chapter, or a page range.
Selection does not imply that checking has completed.
_Avoid_: Checked content

**Targeted correction**:
Extraction correction that investigates automatically identified suspicious passages against the original document.
Its completion describes the investigated passages, rather than exhaustive checking of every PDF page.

**Source evidence**:
Content from the selected original document that establishes a reading or correction, including readable PDF characters
with their placement or a readable image of the relevant passage. Faulty character mappings alone do not establish a reading.

**Essential equation**:
A mathematical relation whose omission would lose a necessary definition, central result, or governing mechanism of the document's argument.
An intermediate derivation step or familiar definition is not essential solely because it is expressed as an equation.

**Local expansion**:
An in-place view of a passage in the author's original words, including its display mathematics, while the rest of the document retains the chosen reading level.

**Source page**:
A web page contributing original content to a reading document, identified by its source URL.

**Reading document**:
A library item read as one work, containing an ordered set of chapters drawn from one or more sources.

**Library folder**:
A grouping of reading documents for organization, distinct from the chapters within a reading document.
