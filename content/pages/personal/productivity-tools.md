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

## Task tracking

I've struggled to find a great to do list tracker.  My requirements are pretty simple in that I don't rely on calendar integration or Pomodoro or other fancy features. Maybe I should.

### Microsoft To Do

The good:

- Integrates with the Microsoft ecosystem.  Flagged emails from Outlook and tagged tasks from Microsoft Planner and Microsoft Project automatically show up there.
- The concept of starting your day by taking tasks off your lists and sticking them in a "Today" is nice in practice.

Problems:

1. There's no easy way to just see every task you have in a flat list that you can manipulate. This makes it REALLY hard to see what you need to do by when alongside tasks that you haven't assigned dates to. I continually found it difficult to figure out what was coming without scrolling through every single list in the "All" view. You cannot combine tasks from Outlook alongside tasks from Planner or tasks you've added through the To Do app itself.
2. Importance is a binary yes or no.
3. No way to email or forward tasks to add them to your list.
4. No keyboard shortcut to quickly add a todo list while you're in the middle of something else.

Item #1 ultimately became a show-stopper for me despite the convenience of the Microsoft Outlook and Planner integrations.  Being surprised by tasks being due that are on your to-do list is the hallmark of a bad to-do list app.

### TickTick

I tried TickTick for a few years at Microsoft after hearing about it from an mkbhd video.

The good:

- Cross-platform. Handy when you work at Microsoft but use a Mac.
- Gantt charts! Sometimes this is just a handy way to visualize a workload and figure out how far behind certain tasks are.

The bad:

- Adding notes to lists is really clunky.  You can convert a task to a note, but it's then listed as an incomplete item on that list in perpetuity. There's no way to otherwise annotate a project.
- The autodetection of dates is overly broad. I used to have monthly reports to do, and any task that referred to a monthly report ("send out the monthly report for review") became a recurring task.

Overall, I struggled with its approach to task lists not being project-oriented. Archiving lists and using tasks as notes is not quite the same as completing projects and attaching arbitrary markdown to a list to help organize key schedule information around a project. This is surprising since it has a great Gantt view.

### Things 3

I used Things for a few years at NERSC, and it was fine and straightforward. It is also a very project-oriented way of structuring tasks, where lists have a notion of completeness, and rather than archiving lists, you complete projects. This maps well to the way I tend to bucketize tasks.

The good:

- Adding arbitrary notes to the top of lists is handy.
- Lets you specify a start date and end date separately.  Really handy.
- I like the completeness pie charts alongside each.

The bad:

- No visualization (like Gantt charts) even though the tasks contain this metadata.
- Unreasonably expensive for what you get. Each iOS device is a different, arbitrary charge. I ate the $80 to get Things for my laptop, phone, and iPad. When I got a Vision Pro, there was no way I'd pay again for the app just in case I wanted to see my to-do list.
