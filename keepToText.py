#<<<<<<< HEAD
#import sys, glob, os, shutil, zipfile, time
#from html.parser import HTMLParser
#=======
from __future__ import print_function
import sys, glob, os, shutil, zipfile, time, codecs, re, argparse
#>>>>>>> fork1/master
from dateutil.parser import parse, parserinfo
from html.parser import HTMLParser
from zipfile import ZipFile
from lxml import etree
from mako.template import Template


outputEncoding = None
MyHTMLParser = None
args = None

class InvalidEncoding(Exception):
    def __init__(self, inner):
        Exception.__init__(self)
        self.inner = str(inner)
        
def msg(s):
    print(s, file=sys.stderr)
    sys.stderr.flush()

def htmlFileToText(inputPath, outputDir, tag, attrib, attribVal):
    global outputEncoding
    global MyHTMLParser

    basename = os.path.basename(inputPath).replace(".html", ".txt")
    outfname = os.path.join(outputDir, basename)
    try:
        with codecs.open(inputPath, "r", "utf-8") as inf, codecs.open(outfname, "w", outputEncoding) as outf:
            html = inf.read()
            parser = MyHTMLParser(outf, tag, attrib, attribVal)
            parser.feed(html)
    except UnicodeEncodeError as ex:
        msg("Skipping file " + inputPath + ": " + str(ex))
    except LookupError as ex:
        raise InvalidEncoding(ex)
        
def htmlDirToText(inputDir, outputDir, tag, attrib, attribVal):
    try_rmtree(outputDir)
    try_mkdir(outputDir)
    msg("Building text files in {0} ...".format(outputDir))
    
    for path in glob.glob(os.path.join(inputDir, "*.html")):
        htmlFileToText(path, outputDir, tag, attrib, attribVal)
        
    msg("Done.")
    
def tryUntilDone(action, check):
    ex = None
    i = 1
    while True:
        try:
            if check(): return
        except Exception as e:
            ex = e
                
        if i == 20: break
        
        try:
            action()
        except Exception as e:
            ex = e
            
        time.sleep(1)
        i += 1
        
    sys.exit(ex if ex != None else "Failed")          
        
def try_rmtree(dir):
    if os.path.isdir(dir): msg("Removing {0}".format(dir))

    def act(): shutil.rmtree(dir)        
    def check(): return not os.path.isdir(dir)        
    tryUntilDone(act, check)
        
def try_mkdir(dir):
    def act(): os.mkdir(dir)
    def check(): return os.path.isdir(dir)
    tryUntilDone(act, check)
    
htmlExt = re.compile(r"\.html$", re.I)
    
class Note:
    def __init__(self, heading, title, text, labels):

        self.ctime = parse(heading, parserinfo(dayfirst=True))
        if title == "":
            self.title = "Untitled " + self.ctime.isoformat()
        else:
            self.title = title
        self.text = text
        self.labels = labels

    def getWsSeparatedLabelString(self):
        "Return a WS-separated label string suited for import into CintaNotes"
        labels = []
        for label in self.labels:
            label = label.replace(" ", "_")
            label = label.replace(",", "")
            labels.append(label)
        return " ".join(labels)
        
def extractNoteFromHtmlFile(inputPath):
    """
    Extracts the note heading (containing the ctime), title, text, and labels
    from an exported Keep HTML file
    """

    with codecs.open(inputPath, 'r', 'utf-8') as myfile:
        data = myfile.read()
    
    tree = etree.HTML(data)

    heading = tree.xpath("//div[@class='heading']/text()")[0].strip()
    title = "\n".join(tree.xpath("//div[@class='title']/text()"))
    text = "\n".join(tree.xpath("//div[@class='content']/text()"))
    labels = tree.xpath("//div[@class='labels']/span[@class='label']/text()")

    return Note(heading, title, text, labels)
        
def processHtmlFiles(inputDir):
    "Iterates over Keep HTML files to extract relevant notes data"

    msg("Processing HTML files in {}".format(inputDir))
    
    notes = []
    for path in glob.glob(os.path.join(inputDir, "*.html")):
        try:
            note = extractNoteFromHtmlFile(path)
            notes.append(note)
        except IndexError: pass

    msg("Done.")

    return notes

def getHtmlDir(takeoutDir):
    "Returns first subdirectory beneath takeoutDir which contains .html files"
    dirs = [os.path.join(takeoutDir, s) for s in os.listdir(takeoutDir)]
    for dir in dirs:
        if not os.path.isdir(dir): continue
        htmlFiles = [f for f in os.listdir(dir) if htmlExt.search(f)]
        if len(htmlFiles) > 0: return dir
        
def htmlDirToXml(zipFileDir, htmlDir):
    xmlFile = os.path.join(zipFileDir, "cintanotes.xml")
    notes = processHtmlFiles(inputDir=htmlDir)

    cintaXml = Template("""
        <?xml version="1.0"?>
        <notebook version="4104" uid="">

        %for note in notes:
                <note uid="" created="${note.ctime.strftime("%Y%m%dT%H%M%S")}"
                    source="" link="" remarks=""
                    tags="${note.getWsSeparatedLabelString()}"
                    section="0" plainText="1">
                    <![CDATA[${note.text}]]>
                </note>
        %endfor

        </notebook>
    """)

    msg("Generating CintaNotes XML file: " + xmlFile)

    with codecs.open(xmlFile, 'w', 'utf-8') as outfile:
        outfile.write(cintaXml.render(notes=notes))

def htmlDirToSn(zipFileDir, htmlDir):
    snFile = os.path.join(zipFileDir, "standardnotes-from-keep.txt")
    notes = processHtmlFiles(inputDir=htmlDir)

    snJSON = Template("""{
  <%!
    import hashlib, json, uuid
  %>
  "items": [
    %for note in notes:
    {
      "created_at": "${note.ctime.isoformat()}",
      "updated_at": "${note.ctime.isoformat()}",
      "uuid": "${str(uuid.UUID(hashlib.sha256((note.ctime.isoformat()+note.title+note.text).encode('utf-8')).hexdigest()[:32], version=5))}",
      "content_type": "Note",
      "content": {
        "title": ${json.dumps(note.title)},
        "text": ${json.dumps(note.text)},
        "references": []
      }
    }${'' if loop.last else ','}
    %endfor
  ]
}
""")

    msg("Generating Standard Notes TXT file: " + snFile)

    with codecs.open(snFile, 'w', 'utf-8') as outfile:
        outfile.write(snJSON.render(notes=notes))

def keepZipToOutput(zipFileName):
    zipFileDir = os.path.dirname(zipFileName)
    takeoutDir = os.path.join(zipFileDir, "Takeout")
    
    try_rmtree(takeoutDir)
    
    if os.path.isfile(zipFileName):
        msg("Extracting {0} ...".format(zipFileName))

    try:
        with ZipFile(zipFileName) as zipFile:
            zipFile.extractall(zipFileDir)
    except (IOError, zipfile.BadZipfile) as e:
        sys.exit(e)
#<<<<<<< HEAD
#    translatedKeepDirs = ["Keep", "Notizen"]    
#    for dirName in translatedKeepDirs:
#	if os.path.isdir(takeoutDir+"/"+dirName): htmlDir = os.path.join(takeoutDir, dirName)
#
#    htmlDirToText(inputDir=htmlDir, outputDir=outputDir,
#        tag="div", attrib="class", attribVal="content")
#=======

    htmlDir = getHtmlDir(takeoutDir)
    if htmlDir is None: sys.exit("No Keep directory found")
    
    msg("Keep dir: " + htmlDir)

    if args.format == "Evernote":
        htmlDirToText(inputDir=htmlDir,
            outputDir=os.path.join(zipFileDir, "Text"),
            tag="div", attrib="class", attribVal="content")
            
    elif args.format == "CintaNotes":
        htmlDirToXml(zipFileDir=zipFileDir, htmlDir=htmlDir)
        
    elif args.format == "StandardNotes":
        htmlDirToSn(zipFileDir=zipFileDir, htmlDir=htmlDir)

def setOutputEncoding():
    global outputEncoding
    outputEncoding = args.encoding
    if outputEncoding is not None: return
    if args.system_encoding: outputEncoding = sys.stdin.encoding
    if outputEncoding is not None: return    
    outputEncoding = "utf-8"

def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("zipFile")
    parser.add_argument("--encoding",
        help="character encoding of output")
    parser.add_argument("--system-encoding", action="store_true",
        help="use the system encoding for the output")
    parser.add_argument("--format", choices=["Evernote", "CintaNotes", "StandardNotes"],
        default='Evernote', help="Output Format")
    global args
    args = parser.parse_args()    

def doImports():
    if args.format == "Evernote":
        global HTMLParser
        try:
            from HTMLParser import HTMLParser
        except ImportError:
            from html.parser import HTMLParser
        
        global MyHTMLParser
        class MyHTMLParser(HTMLParser):
            def attrib_matches(self, tag, attrs):
                return [pair for pair in attrs if
                        pair[0] == self.attrib and pair[1] == self.attribVal]    

            def handle_starttag(self, tag, attrs):
                if tag == self.tag:
                    if self.attrib_matches(tag, attrs) and not self.nesting:
                        self.nesting = 1
                    elif self.nesting:
                        self.nesting += 1
                elif tag == "br" and self.nesting:
                    self.outf.write(os.linesep)

            def handle_endtag(self, tag):
                if tag == self.tag and self.nesting:
                    self.nesting -= 1
                    
            def handle_data(self, data):
                if self.nesting:
                    self.outf.write(data.strip())
            
            def __init__(self, outf, tag, attrib, attribVal):
                HTMLParser.__init__(self)
                self.outf = outf
                self.tag = tag
                self.attrib = attrib
                self.attribVal = attribVal
                self.nesting = 0
                
    elif args.format == "CintaNotes":

    elif args.format == "StandardNotes":
        global Template
        from mako.template import Template
#>>>>>>> fork1/master

def main():
    getArgs()
    doImports()
    setOutputEncoding()
        
    msg("Output encoding: " + outputEncoding)
    
    try:
#<<<<<<< HEAD
#        keepZipToText(zipFile)
#    except OSError as e:
#        sys.exit(e)
#
#if __name__ == "__main__":
#    main()
#=======
        keepZipToOutput(args.zipFile)
    except Exception as ex:
        sys.exit(ex)
    except OSError as ex:
        sys.exit(ex)
    except InvalidEncoding as ex:
        sys.exit(ex.inner)

if __name__ == "__main__":
    main()

#>>>>>>> fork1/master
