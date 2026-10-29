# Herdr Agent Tree

This repo has two parts:

- A Python plugin. It adds the parent and child text tree.
- A custom Herdr GPUI app. It adds cards and our tree styles.

## Project language

Write our docs, comments, and app text in simple English (A1).
Use short sentences and common words. Explain needed technical words.
Keep code IDs, API fields, commands, paths, and URLs exact.
Keep other projects' source text, licenses, and notices exact.

## Install the full app

When a user asks to install or update Herdr Agent Tree, follow
[INSTALL.md](INSTALL.md). This is also the path for the one-prompt setup.
Install both parts unless the user asks for text mode only.
Find the latest stable Herdr and Herdr GPUI versions at that time.
Check that the server and app work together. Add all patches in `native/`.
Build and test the app. Install it for the user, open it, and check it.
Save the code version, file ID, and steps to use the old app again.

The setup is done when the right app is running and these checks pass:

- The plugin and saved tree view are on. Panes have the three tree values.
- The installed app has the expected code ID and file ID.
- Cards, dark headers, tree lines, row marks, and icons work.
- Task titles, work state, and screen reader labels stay in place.

If a check cannot run, name it and say what still needs work.
A guide, build, or accepted command alone is not a full install.

## Work on the Python plugin

Read [README.md](README.md). Run the tests from this folder:

```sh
rtk proxy python3 -m unittest discover -s tests
```

## Keep the user's work

Keep the chosen version of the original project. If a patch does not fit, read
the new code and add the same feature there. Test the change and report it.
Keep all features. Ask before using an older version or replacing
`/Applications/Herdr.app`.
