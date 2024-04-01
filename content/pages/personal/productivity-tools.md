---
title: Productivity tools
---

"The difference between science and screwing around is writing it down."

This page is where I keep notes along my journey to find the ideal set of tools
to work productively throughout my career as an infrastructure architect in the
HPC industry.

## Notes and knowledge

My goals:

1. Maintain a knowledgebase of both public and private information.
2. Maintain meeting notes for future reference.
3. Somehow connect the two.

My requirements:

1. Cannot store notes in anyone's cloud other than my employer's (so OneDrive or Sharepoint)
2. Must synchronize across both desktop (Mac) and mobile (iOS). Mobile can be read-only for now. Windows support is a bonus.
3. Indexable by Copilot is highly desirable.

### Obsidian

The good:

- Extensible with plugins.
- Wikilinks is very straightforward for connecting knowledgebase with notes.

Problems:

- Embedding images in notes is janky.
- Incompatible with Copilot so far (Copilot does not index OneDrive, and it does index Markdown in Sharepoint).
- Integrating non-markdown content in Vault (docx, external URLs) is extremely limited.

### Microsoft Loop

The good:

- Pretty overall UI.
- Can have URLs (docx/pptx Sharepoint links, external webpages) appear in the navigation next to notes.

Problems:

- Ideas UI has no way to create a new idea as far as I can tell.
- Search doesn't seem to map to a workspace in a reasonable way. Finding information can be difficult.
- Context menus are inconsistent. For example, you cannot create a link directly in a folder.
- Limited link hierarchy. For some reason you cannot nest pages more than a few levels deep.
- No copilot support for loop components. Copilot seems to be write-only in Loop. To summarize contents, you have to go through [copilot.microsoft.com](https://copilot.microsoft.com).

### Microsoft OneNote

Problems:

- No find and replace in 2022. See [Find and replace text in notes](https://support.microsoft.com/en-us/office/find-and-replace-text-in-notes-34b1f7f8-d327-40c5-8b0c-8419425ed68b).
- Completely incompatible with Microsoft Word. Copy/paste doesn't preserve html elements, only styles; headings turn into fonts, bulleted lists paste in as ascii with spaces.
- No feature parity across implementations. For example, cannot change note date on any platform except Windows.
