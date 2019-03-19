# KeepToText

Convert a Google Takeout zip file containing Google Keep notes to a
directory of text files, suitable for import into systems such as Evernote

Use Google Takeout to get a zip file, which will contain your Keep notes

**NOTE**: Be sure that *only* Keep files are included in the Google Takeout zip file, not contacts or any other Google data

Usage:

  simple usage: `python keepToText.py zipFile`
  
  full usage: `python keepToText.py [-h] [--encoding ENCODING] [--system-encoding]
                     [--format {Evernote,CintaNotes,StandardNotes}]
                     zipFile`

By default, the text files will be placed in a directory called `Text`, under the same
directory as the zip file. You may import that folder into Evernote.

If you specify `--format CintaNotes`, a single `cintanotes.xml` file containing all your notes will be
created in the same directory as the zip file. You may import that file into CintaNotes.

If you specify `--format StandardNotes`, a single `standardnotes-from-keep.txt` file containing all your
notes will be created in the same directory as the zip file. You may import that file into Standard Notes.

Works with Python 2 or 3

**Options**:
  
  Use the `--encoding` option to specify an output encoding, for example, `--encoding latin_1`
  
  Use the `--system-encoding` option to use your operating system's current encoding
  
  The default output encoding is `utf-8`
  
  Use the `--format` option to choose between Evernote, CintaNotes or Standard Notes, for example, `--format CintaNotes`
  
  The default format is Evernote
    
**Module dependencies**:

   For Evernote format: HTMLParser
   
   For CintaNotes format: lxml, mako, and python-dateutil

   For StandardNotes format: hashlib, json, lxml, mako, python-dateutil, and uuid
   
   To install a dependency, use: `python -m pip install [dependency]`

**About the Standard Notes format**:

   Proper operation with Python 2 has not been verified.

   Use `Extensions > Batch Manager > Open > Backup Explorer` to inspect the output file before performing an import.

   Title and timestamp from Google Keep are preserved. Timestamp timezones may not be preserved correctly. Notes without a title will be given a title of the form "Untitled yyyy-mm-ddThh:mm:ss".

   The Standard Notes note identifier (UUID) will be set to a value derived from the SHA256 hash of timestamp+title+text of the note, in the hope that this will help Standard Notes detect a duplicate on re-import. However, the Batch Manager extension also has as separate duplicate finder tool you can use.

   The Standard Notes parser was copied and modified from the CintaNotes parser - thanks for the head-start! Using Mako templating for output works, but it's sort of a hack; a future enhancement would be to create a list of StandardNote dicts and output by dumping that to JSON instead.
