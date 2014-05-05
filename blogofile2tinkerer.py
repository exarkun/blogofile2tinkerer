from __future__ import unicode_literals

if __name__ == '__main__':
    from sys import argv
    import blogofile2tinkerer
    raise SystemExit(blogofile2tinkerer.main(argv))

from datetime import datetime
from subprocess import PIPE, Popen

from twisted.python.filepath import FilePath

HEADER_TEMPLATE = """\
%(title)s
%(underbar)s

.. author:: %(author)s
.. categories:: %(categories)s
.. tags:: %(tags)s
.. comments:: %(comments)s
"""

SITEMAP = """\
Sitemap
=======

.. toctree::
   :maxdepth: 1

%(entries)s
"""

def main(argv):
    # input
    posts = FilePath(argv[1])

    # output
    blog = FilePath(argv[2])

    entries = []
    for post in posts.children():
        data = post.getContent().decode("utf-8")
        ignored, header, body = data.split(b"---", 2)
        meta = dict((text.strip() for text in line.split(":", 1)) for line in header.splitlines() if line.strip())
        date = datetime.strptime(meta["date"], "%Y/%m/%d %H:%M:%S")

        parent = blog.preauthChild(
            ("%d/%02d/%02d" % (date.year, date.month, date.day)).encode("utf-8"))
        title = filter(
            lambda ch: ch.isalpha() or ch == " ",
            meta["title"].strip().lower()).replace(" ", "_")
        entry = parent.child((title + ".rst").encode("utf-8"))

        header = HEADER_TEMPLATE % dict(
            author=meta["author"].strip(), categories="none",
            tags=meta["categories"].strip(), comments="",
            title=meta["title"].strip(),
            underbar="=" * len(meta["title"].strip()))

        if not parent.isdir():
            parent.makedirs()

        entry.setContent((header + html2rst(body)).encode("utf-8"))

        entries.append(entry)

    entries.sort()
    entries.reverse()

    sitemap = SITEMAP % dict(
        entries="".join([
                "\n   " + "/".join(entry.segmentsFrom(blog))
                for entry in entries]))
    blog.child(b"master.rst").setContent(sitemap.encode("utf-8"))


def html2rst(html):
    process = Popen([b"pandoc", b"--from=html", b"--to=rst"], stdin=PIPE, stdout=PIPE)
    process.stdin.write(html.encode("utf-8"))
    process.stdin.close()
    rst = process.stdout.read().decode("utf-8")
    process.wait()
    return rst
