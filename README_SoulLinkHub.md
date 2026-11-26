# Pokémon SoulLink Hub

A two-player Pokémon SoulLink companion for **Generations 1--3**. The
project connects two mGBA game sessions to a shared hub that tracks
parties, route encounters, linked pairs, and fainted Pokémon.

## Features

* **Generation 1, 2, and 3 support** for compatible Pokémon Game Boy,
Game Boy Color, and Game Boy Advance games.
* **Automatic route linking:** the hub tracks the first eligible
encounter for each area and links the players' Pokémon for that
encounter.
* **Automatic fainting:** when a linked Pokémon faints, its partner is
automatically fainted as well.
* **Live party tracking:** view both players' parties in the companion
window.
* **Encounter and pair logs:** review route encounters and active or
fallen pairs.
* **Optional rule toggles:** enable or disable nickname and
duplicate-type rules in the hub.
* **Local co-op and online P2P modes:** play with two emulator windows
on one computer, or connect with another player using the online
host/guest flow.
* **Run profiles:** keep separate runs and their associated emulator
save files.

> \*\*Important:\*\* This is a companion/modding project. Use game ROMs that
> you are legally entitled to use. The project does not include Pokémon
> ROM files.

## What you need

* A Windows or macOS computer.
* **mGBA** installed.
* **Python 3** installed if you are using the source-code launcher
rather than a packaged release.
* The SoulLink Hub project files, kept together in the same folder.
* Two compatible Generation 1--3 game ROMs for a local run, or one ROM
per player for an online run.

The launcher needs to know where `mGBA` is installed. On first launch,
it may detect mGBA automatically; otherwise, use **Change mGBA** to
select the executable.

## Installation

1. Download or clone this repository.
2. Extract the project so the launcher, hub, and Lua script remain
together in the same folder.
3. Install mGBA.
4. If using the Python source version, install Python 3.
5. On Windows, run `Start\_SoulLink.bat`. You can also start the
launcher with Python by running `launch\_soullink.py`.
6. If prompted, browse to your mGBA executable.

Do not move or rename individual project files unless you also update
any paths or shortcuts that refer to them.

## Create and start a local two-player run

1. Open the **Soul Link Run Manager**.
2. Under **Local 2-Window Runs**, click **+ New Local Run**.
3. Enter a name for the run.
4. Select the Player 1 ROM when prompted.
5. Select the Player 2 ROM when prompted.
6. Select the run in the list and click **Launch Local 2-Window
Co-Op**.
7. The launcher opens both mGBA sessions and the Soul Link Companion
hub. It also loads the SoulLink Lua script into the emulator
sessions.
8. Start or load your games. Check the hub's **Connected Windows**
indicator and **Live Parties** tab to confirm both emulator sessions
are communicating with the hub.

Each player has a separate save file. The launcher stores run profiles
and save files in its `profiles` folder, including a `profiles/saves`
folder for emulator saves. Keep the two players' save files separate.

## Online host / guest mode

The launcher also includes an **Online P2P Runs (Host / Guest)**
workflow.

### Host

1. Create an Online Run and select the ROM you will play.
2. Launch the run using the host option.
3. In the Soul Link Companion, wait for the room code to appear.
4. Click **Copy My Code** and send that code to the other player.
5. Input the guest's code

### Guest

1. Create or select an Online Run and choose the guest/join option.
2. Enter the host's room code in the Companion.
3. Click **Connect Code**.
4. Click **Copy My Code** and send that code to the Host.
5. After the connection is established, the guest's mGBA session should
launch.
6. 
7. Click **Copy My Code** and send that code to the other player.

Both players should use compatible game versions and the same SoulLink
project version. Online play depends on the peer-to-peer connection
being established; network/firewall conditions can affect whether a
connection succeeds.

## Using the Soul Link Companion

The hub has several tabs:

### Live Parties

Shows the Pokémon detected in each player's party.

* **Player 1** and **Player 2** are displayed side by side.
* Use **Manual Link / Unlink** if you need to create or remove a pair
yourself.
* Select the desired party slot for each player, then click **Link**
or **Unlink**.

### Encounters

Shows the first wild, starter, or gift encounter tracked for each area.

* Eligible encounters are detected and recorded automatically.
* When both players have an eligible Pokémon for the same area, the
hub links them.
* Use **Reset Selected Route Encounter** only when you intentionally
want to clear that area's encounter record and try again.

### Pairs Log

Shows active and fallen SoulLink pairs.

* A linked Pokémon fainting causes its partner to faint automatically.
* Use **Delete Selected Pair** only if you intentionally want to
remove that pair from the hub's tracking.

### Type Charts

The two player type-chart tabs provide a type-effectiveness reference.
The hub also includes the **Rule 5: No Type Dups** toggle.

## Rules and options

The hub currently exposes these rule toggles:

* **Rule 3: Nicknames** --- enables or disables the nickname rule.
* **Rule 5: No Type Dups** --- enables or disables the duplicate-type
rule.

The Encounters tab describes the first Wild / Starter / Gift encounter
per area as the tracked encounter rule. Make sure both players agree on
the rules before starting a run.

## Saving and deleting runs

* Run profiles are stored separately so you can keep multiple
playthroughs.
* Each local player has an individual `.sav` file; online runs have
their own save file.
* Use the launcher's **Delete** button in the appropriate run section
to remove a run and its associated save files.
* **Deleting a run and its saves is permanent.** Back up any save you
may want to keep before deleting the run.
* Do not manually delete a save while its mGBA session is still
running. Close the emulator first so it cannot write the save back
to disk.

## Troubleshooting

### The hub shows fewer than 2 connected windows

* Make sure both mGBA sessions are open.
* Confirm the SoulLink Lua script loaded in both sessions.
* Check that the hub and Lua script are from the same project release.
* Restart the run from the launcher if one emulator was closed or
stopped responding.

### A Pokémon or encounter is not appearing in the hub

* Confirm the game is supported and is running in mGBA.
* Check that the Lua script is loaded in that emulator session.
* Give the hub a moment to receive the next update.
* If it still does not appear, restart both emulator sessions and the
hub.

### Route linking does not happen

* Confirm both players have connected to the same hub/run.
* Check the Encounters tab to see whether each player's encounter was
detected and whether the route is already recorded.
* If you need to retry a route, select it and use **Reset Selected
Route Encounter**. Be aware that this clears that route's current
encounter record.

### Partner fainting does not trigger

* Confirm the Pokémon are linked. Check the Pairs Log.
* Confirm both emulator sessions are connected to the hub.
* If the issue persists, save your logs and report the game title,
version/revision, which player fainted, and what the other game did.

### The launcher cannot find mGBA or Python

* Use **Change mGBA** to select the correct mGBA executable.
* For the source-code launcher, install Python 3 and make sure it is
available on your system.
* On Windows, try running `Start\_SoulLink.bat` again after installing
Python.

### Online connection does not complete

* Verify that the host and guest are using the same project version.
* Have the host and guest both generate and send a fresh room code.
* Check firewall/security software settings and retry. Some networks
may restrict peer-to-peer connections.

## Reporting bugs

When opening an issue, include:

* Operating system.
* SoulLink Hub version or commit.
* Game title and ROM revision for **both** players.
* Local or online mode.
* Steps to reproduce the issue.
* What you expected to happen and what actually happened.
* Relevant hub or emulator console messages.
* Whether the issue happens every time or only occasionally.

Do not upload or distribute copyrighted ROM files. Save files and
screenshots may contain personal gameplay data; review them before
attaching them to an issue.

## Project status

Automatic route linking and automatic partner fainting are implemented
for the project's supported Generation 1--3 games. Compatibility can
vary by game, ROM revision, and emulator behavior. If you encounter a
title or revision that does not work correctly, please report it with
the details listed above.

