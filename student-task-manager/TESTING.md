# Manual test checklist

Automated tests cover the logic and basic window behaviour. Run this list once on **each** OS
(Windows 10, Windows 11, Linux) with a fresh data folder, and again on the packaged build
on a machine that has no Python.

Start clean: delete (or rename) the data folder shown in README.md, or run `python run.py --db test.db`.

## First run
- [ ] App opens; dashboard shows all zeros and "no assignments yet"
- [ ] Text is sharp (not blurry) and nothing is cut off at the smallest window size

## Courses
- [ ] Add a course with a colour (Choose... opens a colour picker)
- [ ] Adding the same code again (also `bcs 1` vs `BCS 1`) shows an error
- [ ] Edit the course name; the change shows in the list
- [ ] Empty code or name shows an error

## Assignments
- [ ] New assignment with a course, a due time and High priority saves and appears in the list
- [ ] Bad time like `25:99` shows an error and keeps the form open
- [ ] Search finds by title, notes, and course name; typing `%` does not match everything
- [ ] Course / Status / Priority filters work alone and together; **Clear filters** resets
- [ ] An assignment due in the past is red and says Overdue; the Overdue filter lists it
- [ ] Mark complete / reopen toggles; completed rows are grey
- [ ] Edit via button, double-click and Enter key; Delete asks first and removes the row
- [ ] Mouse wheel scrolls a long list (add 30+ with sample data several times)

## Dashboard
- [ ] Numbers and the progress bar change after completing/adding assignments
- [ ] Upcoming list shows the earliest open deadlines, overdue first in red
- [ ] Per-course bars match each course's completed / total

## Calendar
- [ ] Deadline days are coloured; clicking a day lists its assignments
- [ ] **Today** jumps to today; double-click an item edits it; changes show after saving
- [ ] Arrow buttons change month and the colours remain

## Reminders
- [ ] Create an assignment due in about 1 hour; within a minute a pop-up appears
- [ ] **Snooze** hides it and it returns after the chosen time
- [ ] **Mark selected complete** completes it and the dashboard updates
- [ ] **Dismiss** does not bring it back every minute
- [ ] Turning reminders off in Settings stops pop-ups; **Show dismissed reminders again** brings them back
- [ ] Moving the deadline later gives a fresh reminder

## Data and shutdown
- [ ] Close and reopen the app: everything is still there
- [ ] Deleting a course keeps its assignments and they show "-" for course
- [ ] Settings shows the correct database path

## Packaged build only
- [ ] Starts by double-click with no Python installed and no black terminal window
- [ ] Calendar screen opens (proves tkcalendar and Babel were bundled)
- [ ] Data is saved in the user data folder, not next to the program
