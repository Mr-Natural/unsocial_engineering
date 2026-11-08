# Casebook and resource directory

The first collection is `/casebook/2026`. It uses the normal anonymous published-only
reader. A reserved `YYYY-` slug prefix is its membership identifier. The slug is
immutable and included in the publishing revision hash; no private article names,
bodies or dates are held in site source. Pages support pagination and make fresh
database reads, so withdrawal also removes the story from the collection.

Every new Casebook export starts with a **Dates and scope** section. It identifies
the incident date when documented, otherwise the dated warning or operation window,
with uncertainty explicit. This section is rendered and hashed by the existing
publishing contract. The publication date and Article schema/Open Graph dates remain
the actual release dates. No incident date is inferred from research or publication.

This first iteration does not introduce database date columns, chronological event
sorting, a new migration or a changed publishing RPC. A later date-filtering feature
must add validated event metadata to the immutable envelope and approval hash, with
appropriate migration and hosted boundary tests. Do not build an independently
editable mapping of unreviewed dates or backdate published_at.

Personal Experiences remain private drafts until Shaun confirms facts and wording.
Their eventual series/evidence treatment needs its own reviewed implementation;
first-person testimony must not be silently presented as independently verified.

`/resources` is a country/jurisdiction directory, separate from `/sources`, the
publication's research references. It uses official destinations, with Scotland
separate from England/Wales/Northern Ireland and local police as the starting point
for cross-border reports. Link review is manual; no recurring monitoring is enabled.

Source release and article publication remain separate owner-approved steps. A
preview contains synthetic content from the isolated preview database only.
